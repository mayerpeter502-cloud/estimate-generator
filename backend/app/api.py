from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json
import tempfile
import os
from app.database import get_db
from app.models import Business, Category, ServiceItem, Estimate
from app.schemas import BusinessCreate, CategoryCreate, ServiceItemCreate, EstimateCreate
from app.pdf_generator import generate_pdf
from app.importer import import_from_excel

router = APIRouter()


@router.post("/businesses")
async def create_business(data: BusinessCreate, db: AsyncSession = Depends(get_db)):
    b = Business(**data.dict())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return {"id": b.id, "name": b.name}


@router.get("/businesses")
async def get_businesses(db: AsyncSession = Depends(get_db)):
    stmt = select(Business)
    result = await db.execute(stmt)
    return [{"id": b.id, "name": b.name, "phone": b.phone} for b in result.scalars().all()]


@router.post("/businesses/{bid}/categories")
async def create_category(bid: str, data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    c = Category(business_id=bid, **data.dict())
    db.add(c)
    await db.commit()
    return {"id": c.id, "name": c.name}


@router.get("/businesses/{bid}/categories")
async def get_categories(bid: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Category).where(Category.business_id == bid)
    result = await db.execute(stmt)
    return [{"id": c.id, "name": c.name} for c in result.scalars().all()]


@router.post("/categories/{cid}/items")
async def create_item(cid: str, data: ServiceItemCreate, db: AsyncSession = Depends(get_db)):
    metadata_json = json.dumps(data.metadata_) if data.metadata_ else "{}"
    item = ServiceItem(
        category_id=cid, name=data.name, base_price=data.base_price,
        unit=data.unit, description=data.description, metadata_=metadata_json
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "name": item.name, "base_price": float(item.base_price), "unit": item.unit}


@router.get("/categories/{cid}/items")
async def get_items(cid: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ServiceItem).where(ServiceItem.category_id == cid)
    result = await db.execute(stmt)
    return [
        {"id": i.id, "name": i.name, "base_price": float(i.base_price),
         "unit": i.unit, "description": i.description or ""}
        for i in result.scalars().all()
    ]


@router.put("/items/{item_id}")
async def update_item(item_id: str, data: ServiceItemCreate, db: AsyncSession = Depends(get_db)):
    item = await db.get(ServiceItem, item_id)
    if not item:
        raise HTTPException(404, "Услуга не найдена")
    item.name = data.name
    item.base_price = data.base_price
    item.unit = data.unit
    item.description = data.description
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "name": item.name, "base_price": float(item.base_price), "unit": item.unit}


@router.delete("/items/{item_id}")
async def delete_item(item_id: str, db: AsyncSession = Depends(get_db)):
    item = await db.get(ServiceItem, item_id)
    if not item:
        raise HTTPException(404, "Услуга не найдена")
    await db.delete(item)
    await db.commit()
    return {"message": "Услуга удалена", "id": item_id}


@router.post("/estimates")
async def create_estimate(data: EstimateCreate, db: AsyncSession = Depends(get_db)):
    total = 0
    items_out = []
    business_id = None
    for i in data.items:
        stmt = select(ServiceItem).options(selectinload(ServiceItem.category)).where(ServiceItem.id == i.item_id)
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(404, f"Услуга с ID {i.item_id} не найдена")
        if business_id is None:
            business_id = item.category.business_id
        subtotal = float(item.base_price) * i.quantity
        total += subtotal
        items_out.append({"name": item.name, "qty": i.quantity, "price": float(item.base_price), "subtotal": subtotal})
    est = Estimate(
        business_id=business_id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        work_object=data.work_object or "",  # ← НОВОЕ ПОЛЕ
        items_data=json.dumps(items_out, ensure_ascii=False),
        total=total,
        status="created"
    )
    db.add(est)
    await db.commit()
    await db.refresh(est)
    business = await db.get(Business, business_id)
    pdf_path = generate_pdf(business, est)
    return {"id": est.id, "total": total, "pdf": pdf_path}


@router.get("/estimates")
async def get_estimates(business_id: str = "", db: AsyncSession = Depends(get_db)):
    if business_id:
        stmt = select(Estimate).where(Estimate.business_id == business_id).order_by(Estimate.id.desc())
    else:
        stmt = select(Estimate).order_by(Estimate.id.desc())
    result = await db.execute(stmt)
    return [
        {"id": e.id, "client_name": e.client_name, "client_phone": e.client_phone,
         "work_object": e.work_object or "",  # ← НОВОЕ ПОЛЕ
         "total": float(e.total), "status": e.status, "pdf": f"output/estimate_{e.id}.pdf"}
        for e in result.scalars().all()
    ]


@router.get("/estimates/{est_id}")
async def get_estimate(est_id: str, db: AsyncSession = Depends(get_db)):
    est = await db.get(Estimate, est_id)
    if not est:
        raise HTTPException(404, "Смета не найдена")
    items_data = json.loads(est.items_data) if isinstance(est.items_data, str) else est.items_data
    return {
        "id": est.id, "client_name": est.client_name, "client_phone": est.client_phone,
        "work_object": est.work_object or "",  # ← НОВОЕ ПОЛЕ
        "total": float(est.total), "status": est.status,
        "pdf": f"output/estimate_{est.id}.pdf", "items": items_data
    }


@router.get("/estimates/{est_id}/pdf")
async def download_pdf(est_id: str):
    pdf_path = f"output/estimate_{est_id}.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(404, "PDF файл не найден")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"smeta_{est_id[:8]}.pdf")


@router.post("/import")
async def import_excel(file: UploadFile = File(...), business_id: str = "", db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Файл должен быть в формате Excel (.xlsx или .xls)")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = await import_from_excel(tmp_path, business_id, db)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Ошибка импорта: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
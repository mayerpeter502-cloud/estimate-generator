import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Business, Category, ServiceItem

async def import_from_excel(file_path: str, business_id: str, db: AsyncSession):
    business = await db.get(Business, business_id)
    if not business:
        raise ValueError(f"Бизнес с ID {business_id} не найден")
    
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    stmt = select(Category).where(
        Category.business_id == business_id,
        Category.name == "Импорт"
    )
    result = await db.execute(stmt)
    category = result.scalar_one_or_none()
    
    if not category:
        category = Category(business_id=business_id, name="Импорт")
        db.add(category)
        await db.flush()
    
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row[0]:
            continue
        
        try:
            name = str(row[0]).strip()
            price = float(row[1]) if row[1] else 0
            unit = str(row[2]).strip() if row[2] else "услуга"
            
            item = ServiceItem(
                category_id=category.id,
                name=name,
                base_price=price,
                unit=unit,
                description="",
                metadata_="{}"
            )
            db.add(item)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Строка {row_num}: {str(e)}")
    
    await db.commit()
    
    return {
        "imported": imported_count,
        "errors": errors,
        "category_id": category.id
    }
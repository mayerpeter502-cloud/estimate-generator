import { useState, useEffect } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || '/api'

function App() {
  const [businessId, setBusinessId] = useState(null)
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState([])
  const [clientName, setClientName] = useState('')
  const [clientPhone, setClientPhone] = useState('')
  const [workObject, setWorkObject] = useState('')
  const [loading, setLoading] = useState(false)
  const [estimates, setEstimates] = useState([])
  const [activeTab, setActiveTab] = useState('create')
  const [editModal, setEditModal] = useState(null)
  const [deleteModal, setDeleteModal] = useState(null)
  const [estimateModal, setEstimateModal] = useState(null)
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const loadEstimates = async () => {
    try {
      console.log("ЗАПРОС ИСТОРИИ..."); const res = await axios.get(`${API}/estimates`); console.log("ПОЛУЧЕНО СМЕТ:", res.data.length)
      setEstimates(res.data)
    } catch (error) {
      console.error('Ошибка загрузки истории:', error)
    }
  }

  useEffect(() => {
    const initDemo = async () => {
      try {
        const bizRes = await axios.post(`${API}/businesses`, { name: 'Демо Автосервис', phone: '+7 (999) 123-45-67' })
        setBusinessId(bizRes.data.id)
        const catRes = await axios.post(`${API}/businesses/${bizRes.data.id}/categories`, { name: 'Ремонт и ТО' })
        const demoItems = [
          { name: 'Замена масла в двигателе', base_price: 1500, unit: 'услуга' },
          { name: 'Диагностика двигателя', base_price: 800, unit: 'услуга' },
          { name: 'Замена тормозных колодок (перед)', base_price: 2500, unit: 'услуга' },
          { name: 'Замена тормозных колодок (зад)', base_price: 2500, unit: 'услуга' },
          { name: 'Замена свечей зажигания', base_price: 1200, unit: 'услуга' },
          { name: 'Замена воздушного фильтра', base_price: 500, unit: 'услуга' },
          { name: 'Промывка инжектора', base_price: 3000, unit: 'услуга' },
          { name: 'Регулировка развал-схождения', base_price: 2000, unit: 'услуга' }
        ]
        for (const item of demoItems) {
          await axios.post(`${API}/categories/${catRes.data.id}/items`, item)
        }
        const itemsRes = await axios.get(`${API}/categories/${catRes.data.id}/items`)
        setItems(itemsRes.data)
        // Загружаем историю после инициализации
        await loadEstimates()
      } catch (error) {
        console.error('Ошибка инициализации:', error)
      }
    }
    initDemo()
  }, [])

  useEffect(() => {
    loadEstimates()
  }, [businessId])

  const toggleItem = (id) => {
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  }

  const generateEstimate = async () => {
    if (!clientName.trim()) { showToast('Введите имя клиента', 'error'); return }
    if (selected.length === 0) { showToast('Выберите хотя бы одну услугу', 'error'); return }
    setLoading(true)
    try {
      const res = await axios.post(`${API}/estimates`, {
        client_name: clientName,
        client_phone: clientPhone,
        work_object: workObject,
        items: selected.map(id => ({ item_id: id, quantity: 1 }))
      })
      showToast(`Смета создана! Итого: ${res.data.total} ₽`)
      setClientName(''); setClientPhone(''); setWorkObject(''); setSelected([])
      loadEstimates()
    } catch (error) {
      showToast('Ошибка при создании сметы', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (item) => setEditModal({ ...item })
  const saveEdit = async () => {
    try {
      await axios.put(`${API}/items/${editModal.id}`, {
        name: editModal.name, base_price: parseFloat(editModal.base_price), unit: editModal.unit
      })
      setItems(prev => prev.map(i => i.id === editModal.id ? editModal : i))
      setEditModal(null)
      showToast('Услуга обновлена')
    } catch (error) { showToast('Ошибка сохранения', 'error') }
  }

  const handleDelete = (item) => setDeleteModal(item)
  const confirmDelete = async () => {
    try {
      await axios.delete(`${API}/items/${deleteModal.id}`)
      setItems(prev => prev.filter(i => i.id !== deleteModal.id))
      setSelected(prev => prev.filter(id => id !== deleteModal.id))
      setDeleteModal(null)
      showToast('Услуга удалена')
    } catch (error) { showToast('Ошибка удаления', 'error') }
  }

  const viewEstimate = async (id) => {
    try {
      const res = await axios.get(`${API}/estimates/${id}`)
      setEstimateModal(res.data)
    } catch (error) { showToast('Ошибка загрузки сметы', 'error') }
  }

  const handleImport = async (e) => {
    const file = e.target.files[0]
    if (!file || !businessId) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await axios.post(`${API}/import?business_id=${businessId}`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      showToast(`Импортировано: ${res.data.imported} услуг`)
      const itemsRes = await axios.get(`${API}/categories/${res.data.category_id}/items`)
      setItems(prev => [...prev, ...itemsRes.data])
      e.target.value = ''
    } catch (error) {
      showToast('Ошибка импорта: ' + (error.response?.data?.detail || error.message), 'error')
    }
  }

  const total = items.filter(i => selected.includes(i.id)).reduce((sum, item) => sum + (parseFloat(item.base_price) || 0), 0)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-blue-600 text-white py-6">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold">Генератор смет</h1>
          <p className="mt-2 text-blue-100">Автосервис и мастерские</p>
        </div>
      </div>

      <div className="container mx-auto px-4 mt-6 max-w-4xl">
        <div className="flex gap-2 border-b">
          <button onClick={() => setActiveTab('create')} className={`px-6 py-3 font-medium ${activeTab === 'create' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>Создать смету</button>
          <button onClick={() => { setActiveTab('history'); loadEstimates() }} className={`px-6 py-3 font-medium ${activeTab === 'history' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`}>История смет ({estimates.length})</button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {activeTab === 'create' ? (
          <>
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Информация о клиенте</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Имя клиента *</label>
                  <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="Иванов Иван Иванович" value={clientName} onChange={(e) => setClientName(e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Телефон</label>
                  <input type="tel" className="w-full px-3 py-2 border border-gray-300 rounded-md" placeholder="+7 (999) 123-45-67" value={clientPhone} onChange={(e) => setClientPhone(e.target.value)} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Объект работ</label>
                <input 
                  type="text" 
                  className="w-full px-3 py-2 border border-gray-300 rounded-md" 
                  placeholder="Например: Toyota Camry, А123БВ77 / Куртка Аляска, р.52 / Квартира, ул. Ленина 10" 
                  value={workObject} 
                  onChange={(e) => setWorkObject(e.target.value)} 
                />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Импорт прайса из Excel</h2>
              <p className="text-sm text-gray-600 mb-4">Загрузите файл Excel с колонками: Наименование, Цена, Единица</p>
              <input type="file" accept=".xlsx,.xls" onChange={handleImport} className="w-full px-3 py-2 border border-gray-300 rounded-md" />
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Услуги ({items.length})</h2>
              <div className="space-y-2">
                {items.map(item => (
                  <div key={item.id} className="flex items-center p-4 border rounded-lg hover:bg-gray-50">
                    <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggleItem(item.id)} className="w-5 h-5 text-blue-600 rounded" />
                    <span className="flex-1 ml-3 text-gray-800">{item.name}</span>
                    <span className="font-semibold text-gray-900 mr-3">{item.base_price} ₽</span>
                    <button onClick={() => handleEdit(item)} className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-sm mr-2">Изменить</button>
                    <button onClick={() => handleDelete(item)} className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm">Удалить</button>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <div className="flex justify-between items-center mb-4">
                <span className="text-lg font-medium text-gray-700">Итого:</span>
                <span className="text-2xl font-bold text-blue-600">{total} ₽</span>
              </div>
              <button onClick={generateEstimate} disabled={loading || selected.length === 0} className={`w-full py-3 px-6 rounded-lg font-semibold text-white ${loading || selected.length === 0 ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}>
                {loading ? 'Создание сметы...' : 'Создать смету'}
              </button>
            </div>
          </>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">История смет</h2>
            {estimates.length === 0 ? (
              <p className="text-gray-500 text-center py-8">Сметы ещё не созданы</p>
            ) : (
              <div className="space-y-3">
                {estimates.map(est => (
                  <div key={est.id} className="border rounded-lg p-4 hover:bg-gray-50 flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-gray-800">{est.client_name}</p>
                      <p className="text-sm text-gray-500">{est.client_phone || 'Телефон не указан'}</p>
                      {est.work_object && <p className="text-sm text-blue-600 font-medium mt-1">🔧 {est.work_object}</p>}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-lg font-bold text-blue-600">{est.total} ₽</span>
                      <button onClick={() => viewEstimate(est.id)} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm mr-2">Подробнее</button>
                      <button onClick={() => window.open(`${API}/estimates/${est.id}/pdf`, '_blank')} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm">📄 Скачать PDF</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {editModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Редактировать услугу</h3>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Название</label><input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" value={editModal.name} onChange={(e) => setEditModal({ ...editModal, name: e.target.value })} /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Цена (₽)</label><input type="number" className="w-full px-3 py-2 border border-gray-300 rounded-md" value={editModal.base_price} onChange={(e) => setEditModal({ ...editModal, base_price: e.target.value })} /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Единица</label><input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-md" value={editModal.unit} onChange={(e) => setEditModal({ ...editModal, unit: e.target.value })} /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveEdit} className="flex-1 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Сохранить</button>
              <button onClick={() => setEditModal(null)} className="flex-1 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400">Отмена</button>
            </div>
          </div>
        </div>
      )}

      {deleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full">
            <h3 className="text-lg font-semibold mb-2">Удалить услугу?</h3>
            <p className="text-gray-600 mb-6">"{deleteModal.name}" будет удалена без возможности восстановления.</p>
            <div className="flex gap-2">
              <button onClick={confirmDelete} className="flex-1 py-2 bg-red-600 text-white rounded hover:bg-red-700">Удалить</button>
              <button onClick={() => setDeleteModal(null)} className="flex-1 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400">Отмена</button>
            </div>
          </div>
        </div>
      )}

      {estimateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg p-6 max-w-3xl w-full my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold">Смета #{estimateModal.id.slice(0, 8)}</h3>
              <button onClick={() => setEstimateModal(null)} className="text-gray-500 hover:text-gray-700 text-2xl ml-4">×</button>
            </div>
            <div className="mb-4 pb-4 border-b">
              <p className="text-gray-700"><strong>Клиент:</strong> {estimateModal.client_name}</p>
              <p className="text-gray-700"><strong>Телефон:</strong> {estimateModal.client_phone || 'не указан'}</p>
              {estimateModal.work_object && <p className="text-gray-700"><strong>Объект работ:</strong> {estimateModal.work_object}</p>}
            </div>
            <div className="space-y-2 mb-4">
              {estimateModal.items.map((item, idx) => (
                <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                  <span className="flex-1 mr-4">{item.name}</span>
                  <span className="text-gray-600 w-16 text-right">×{item.qty}</span>
                  <span className="font-semibold w-24 text-right">{item.subtotal} ₽</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between items-center pt-4 border-t-2 border-blue-600">
              <span className="text-lg font-semibold">Итого:</span>
              <span className="text-2xl font-bold text-blue-600">{estimateModal.total} ₽</span>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className={`fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${toast.type === 'error' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'}`}>{toast.message}</div>
      )}
    </div>
  )
}

export default App

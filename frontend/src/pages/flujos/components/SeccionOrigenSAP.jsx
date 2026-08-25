import { Input, Select } from 'antd'
import FiltroOData from './FiltroOData'

const ENDPOINTS_SAP = [
    { value: 'Items', label: 'Items (Productos)' },
    { value: 'BusinessPartners', label: 'BusinessPartners (Socios de negocio)' },
    { value: 'PurchaseOrders', label: 'PurchaseOrders (Ordenes de compra)' },
    { value: 'Orders', label: 'Orders (Pedidos de venta)' },
    { value: 'DeliveryNotes', label: 'DeliveryNotes (Notas de entrega)' },
    { value: 'StockTransfers', label: 'StockTransfers (Transferencias)' },
]

const SeccionOrigenSAP = ({ config, onChange }) => {
    const cambiar = (campo, valor) => {
        onChange({ ...config, [campo]: valor })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Origen de datos — SAP B1</h3>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Endpoint</label>
                    <Select
                        value={config.endpoint || undefined}
                        onChange={(val) => cambiar('endpoint', val)}
                        options={ENDPOINTS_SAP}
                        placeholder="Seleccionar endpoint"
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">Filtro OData ($filter)</label>
                    <FiltroOData
                        condiciones={config.filter_condiciones || []}
                        onChange={(nuevas) => cambiar('filter_condiciones', nuevas)}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionOrigenSAP

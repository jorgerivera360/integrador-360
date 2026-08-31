import { Input, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import FiltroOData from './FiltroOData'
import VariablesDinamicas from './VariablesDinamicas'

const SeccionOrigenSAP = ({ config, onChange }) => {
    const cambiar = (campo, valor) => {
        onChange({ ...config, [campo]: valor })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Origen de datos{' '}
                <Tooltip title="Configuración del origen de datos en SAP Business One. Selecciona el endpoint OData de SAP y define los filtros para limitar los registros consultados.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Endpoint{' '}
                        <Tooltip title="Nombre de la entidad OData de SAP B1 Service Layer. Ejemplos: Items, BusinessPartners, PurchaseOrders, Orders, DeliveryNotes, StockTransfers.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Input
                        value={config.endpoint || ''}
                        onChange={(e) => cambiar('endpoint', e.target.value)}
                        placeholder="ej: Items, BusinessPartners, PurchaseOrders"
                    />
                </div>

                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Parámetros{' '}
                        <Tooltip title="Condiciones OData ($filter) para limitar los registros que se consultan desde SAP. Se combinan con AND para formar el filtro final de la petición.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <FiltroOData
                        condiciones={config.filter_condiciones || []}
                        onChange={(nuevas) => cambiar('filter_condiciones', nuevas)}
                    />
                    <VariablesDinamicas />
                </div>
            </div>
        </div>
    )
}

export default SeccionOrigenSAP

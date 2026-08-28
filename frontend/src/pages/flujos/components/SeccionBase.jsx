import { Input, Select, Switch, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'

const OPCIONES_FLOW_TYPE = [
    { value: 'items', label: 'Productos (items)' },
    { value: 'customer', label: 'Clientes (customer)' },
    { value: 'supplier', label: 'Proveedores (supplier)' },
    { value: 'purchases', label: 'Compras (purchases)' },
    { value: 'sales', label: 'Ventas (sales)' },
]

const SeccionBase = ({ datos, onChange, esEdicion }) => {
    const cambiar = (campo) => (valor) => {
        onChange({ ...datos, [campo]: valor })
    }

    const cambiarInput = (campo) => (e) => {
        onChange({ ...datos, [campo]: e.target.value })
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Información del flujo{' '}
                <Tooltip title="Datos generales del flujo: nombre, tipo de procesamiento, programación cron y orden de ejecución en el arranque del scheduler">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Nombre del flujo</label>
                    <Input
                        value={datos.flow_name || ''}
                        onChange={cambiarInput('flow_name')}
                        placeholder="ej: compras, items, facturas"
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">Tipo de flujo</label>
                    <Select
                        value={datos.flow_type || undefined}
                        onChange={cambiar('flow_type')}
                        options={OPCIONES_FLOW_TYPE}
                        placeholder="Seleccionar tipo"
                        disabled={esEdicion}
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">Cron (schedule)</label>
                    <Input
                        className="flujo-input-mono"
                        value={datos.schedule_cron || ''}
                        onChange={cambiarInput('schedule_cron')}
                        placeholder="ej: */2 * * * *"
                    />
                </div>

                <div className="flujo-campo flujo-campo--switch">
                    <label className="flujo-campo__label">Activo</label>
                    <Switch
                        checked={datos.is_active}
                        onChange={cambiar('is_active')}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionBase

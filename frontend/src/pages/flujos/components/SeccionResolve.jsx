import { Input, Switch } from 'antd'
import { IconInfo } from '../icons'

const SeccionResolve = ({ erpType, flowType, config, onChange }) => {
    const esMaestro = flowType === 'items' || flowType === 'customer' || flowType === 'supplier'

    if (!esMaestro) {
        return (
            <div className="flujo-seccion">
                <div className="flujo-resolve-info">
                    <IconInfo style={{ color: '#1677ff', flexShrink: 0 }} />
                    <span>
                        La resolucion de maestros faltantes en transacciones usa la
                        configuracion de los maestros (items, customer, supplier) del mismo cliente.
                    </span>
                </div>
            </div>
        )
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Resolucion de maestros faltantes</h3>

            <div className="flujo-resolve-toggle">
                <Switch checked disabled />
                <span className="flujo-resolve-toggle__texto">
                    Siempre activo — cuando una transaccion referencia un maestro que no existe
                    en Odoo, se consulta el ERP y se crea automaticamente.
                </span>
            </div>

            {erpType === 'sap' && (
                <div className="flujo-campos" style={{ marginTop: 16 }}>
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">Campo de filtro (resolve_filter_field)</label>
                        <Input
                            className="flujo-input-mono"
                            value={config.resolve_filter_field || ''}
                            onChange={(e) => onChange({ ...config, resolve_filter_field: e.target.value })}
                            placeholder="ej: ItemCode, CardCode"
                        />
                    </div>
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">Template de filtro (resolve_filter_template)</label>
                        <Input
                            className="flujo-input-mono"
                            value={config.resolve_filter_template || ''}
                            onChange={(e) => onChange({ ...config, resolve_filter_template: e.target.value })}
                            placeholder="ej: ItemCode eq '{ref}'"
                        />
                    </div>
                </div>
            )}
        </div>
    )
}

export default SeccionResolve

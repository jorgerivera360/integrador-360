import { Input, Switch, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { IconInfo } from '../icons'

const DEFAULTS_WS = {
    items: 'AND f120_id IN ({refs}) ',
    customer: 'AND TRIM(f200_nit) IN ({refs}) ',
    supplier: 'AND TRIM(f200_nit) IN ({refs}) ',
}

const DEFAULTS_SAP = {
    items: { field: 'ItemCode', template: "ItemCode eq '{ref}'" },
    customer: { field: 'CardCode', template: "CardCode eq '{ref}'" },
    supplier: { field: 'CardCode', template: "CardCode eq '{ref}'" },
}

const SeccionResolve = ({ erpType, flowType, config, onChange }) => {
    const esMaestro = flowType === 'items' || flowType === 'customer' || flowType === 'supplier'

    if (!esMaestro) {
        return (
            <div className="flujo-seccion">
                <div className="flujo-resolve-info">
                    <IconInfo style={{ color: '#1677ff', flexShrink: 0 }} />
                    <span>
                        La resolución de maestros faltantes en transacciones usa la
                        configuración de los maestros (items, customer, supplier) del mismo cliente.
                    </span>
                </div>
            </div>
        )
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Resolución de maestros faltantes{' '}
                <Tooltip title="Cuando una transacción referencia un producto, cliente o proveedor que no existe en Odoo, el sistema consulta el ERP y lo crea automáticamente antes de procesar la transacción. Esta configuración define cómo se arma la consulta al ERP para buscar solo los registros faltantes.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="flujo-resolve-toggle">
                <Switch
                    checked={config.resolve_enabled !== false}
                    onChange={(checked) => onChange({ ...config, resolve_enabled: checked })}
                />
                <span className="flujo-resolve-toggle__texto">
                    {config.resolve_enabled !== false
                        ? 'Activo — cuando una transacción referencia un maestro que no existe en Odoo, se consulta el ERP y se crea automáticamente.'
                        : 'Desactivado — los maestros faltantes no se resolverán automáticamente. Las transacciones que referencien maestros inexistentes fallarán.'
                    }
                </span>
            </div>

            {config.resolve_enabled !== false && erpType === 'ws' && (
                <div className="flujo-campos" style={{ marginTop: 16 }}>
                    <div className="flujo-campo flujo-campo--ancho">
                        <label className="flujo-campo__label">
                            Cláusula de filtro SQL{' '}
                            <Tooltip title="Fragmento SQL que se inyecta en el WHERE de la consulta del maestro para traer solo los registros faltantes. El placeholder {refs} se reemplaza automáticamente por la lista de valores que faltan en Odoo. Usa comillas dobles porque SIESA trabaja con QUOTED_IDENTIFIER OFF.">
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </label>
                        <Input
                            className="flujo-input-mono"
                            value={config.resolve_sql_inject || ''}
                            onChange={(e) => onChange({ ...config, resolve_sql_inject: e.target.value })}
                            placeholder={DEFAULTS_WS[flowType] || 'AND campo IN ({refs}) '}
                        />
                    </div>
                </div>
            )}

            {config.resolve_enabled !== false && (erpType === 'sap' || erpType === 'connekta') && (
                <div className="flujo-campos" style={{ marginTop: 16 }}>
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">
                            Campo de búsqueda{' '}
                            <Tooltip title={erpType === 'sap'
                                ? 'Nombre del campo OData de SAP que identifica el registro. Se usa para armar el filtro dinámico que trae solo los maestros faltantes desde SAP. Para productos es el código del artículo, para socios de negocio es el código del socio.'
                                : 'Nombre del campo en la consulta Connekta que identifica el registro. Se usa para armar el filtro que trae solo los maestros faltantes. Si la consulta registrada en Connekta no acepta este filtro, dejarlo vacío y el sistema traerá todos los registros y filtrará internamente.'
                            }>
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </label>
                        <Input
                            className="flujo-input-mono"
                            value={config.resolve_filter_field || ''}
                            onChange={(e) => onChange({ ...config, resolve_filter_field: e.target.value })}
                            placeholder={DEFAULTS_SAP[flowType]?.field || 'ej: ItemCode'}
                        />
                    </div>
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">
                            Plantilla de filtro{' '}
                            <Tooltip title={erpType === 'sap'
                                ? "Plantilla OData que se repite por cada registro faltante. El placeholder {ref} se reemplaza por el valor de cada registro. Las plantillas se combinan con OR para formar un solo filtro. Ejemplo: si faltan 2 productos, se arma (ItemCode eq '001' or ItemCode eq '002')."
                                : "Plantilla que se repite por cada registro faltante. El placeholder {ref} se reemplaza por el valor de cada registro. Las plantillas se combinan con | y reemplazan los parámetros originales de la consulta. Ejemplo: si faltan 2 productos, se arma f120_id = 001|f120_id = 002."
                            }>
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </label>
                        <Input
                            className="flujo-input-mono"
                            value={config.resolve_filter_template || ''}
                            onChange={(e) => onChange({ ...config, resolve_filter_template: e.target.value })}
                            placeholder={erpType === 'sap'
                                ? (DEFAULTS_SAP[flowType]?.template || "ej: ItemCode eq '{ref}'")
                                : "ej: f120_id = {ref}"
                            }
                        />
                    </div>
                </div>
            )}
        </div>
    )
}

export default SeccionResolve

import { Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const SeccionConfigItems = ({ erpType, config, onChange }) => {
    const tieneMapping = erpType === 'connekta' || erpType === 'sap'
    const etiquetaCampoOrigen = erpType === 'sap' ? 'Campo SAP' : 'Campo Connekta'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Configuración del flujo — Productos{' '}
                <Tooltip title="Parámetros que definen cómo se procesan los productos antes de crearlos o actualizarlos en WMS. Incluye la transformación de campos del ERP, valores constantes y la equivalencia de unidades de medida">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            {tieneMapping && (
                <>
                    <h4 className="flujo-seccion__subtitulo">
                        Mapeo de campos{' '}
                        <Tooltip title="Renombra los campos que vienen del ERP a los nombres que el sistema espera internamente (alias canónicos). Por ejemplo, el ERP puede enviar un campo llamado 'Referencia_Item' pero el sistema necesita que se llame 'referencia'. Solo se renombran los campos listados aquí; los que no estén en la tabla se conservan con su nombre original.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </h4>

                    <div className="flujo-campo flujo-campo--ancho">
                        <TablaClaveValor
                            columnas={[etiquetaCampoOrigen, 'Alias canónico']}
                            datos={config.mapping_tabla || []}
                            onChange={(nuevos) => onChange({ ...config, mapping_tabla: nuevos })}
                            placeholders={['Referencia_Item', 'referencia']}
                        />
                    </div>

                    <h4 className="flujo-seccion__subtitulo" style={{ marginTop: 24 }}>
                        Valores fijos{' '}
                        <Tooltip title="Valores constantes que se asignan a todos los registros sin importar lo que traiga el ERP. Útil para campos que siempre tienen el mismo valor para este cliente, como el estado del documento o el porcentaje de impuesto. Los nombres de campo deben usar los alias canónicos (los nombres de la columna derecha del mapeo de campos).">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </h4>

                    <div className="flujo-campo flujo-campo--ancho">
                        <TablaClaveValor
                            columnas={['Campo', 'Valor fijo']}
                            datos={config.hardcodes_tabla || []}
                            onChange={(nuevos) => onChange({ ...config, hardcodes_tabla: nuevos })}
                            placeholders={['estado', 'draft']}
                        />
                    </div>
                </>
            )}

            <h4 className="flujo-seccion__subtitulo" style={tieneMapping ? { marginTop: 24 } : undefined}>
                Mapeo de unidades de medida{' '}
                <Tooltip title="Convierte el nombre de la unidad del ERP al nombre exacto en WMS. Sin este mapeo el producto no se puede crear porque la UOM es obligatoria. Ejemplo: UND → Unidades, KG → kg">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h4>

            <div className="flujo-campo flujo-campo--ancho">
                <TablaClaveValor
                    columnas={['Unidad ERP', 'Unidad WMS']}
                    datos={config.uom_mapping_tabla || []}
                    onChange={(nuevos) => onChange({ ...config, uom_mapping_tabla: nuevos })}
                    placeholders={['UND', 'Unidades']}
                />
            </div>
        </div>
    )
}

export default SeccionConfigItems

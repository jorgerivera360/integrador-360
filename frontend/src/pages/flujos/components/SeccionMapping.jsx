import { Input, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const SeccionMapping = ({ erpType, flowType, config, onChange }) => {
    const etiquetaCampoOrigen = erpType === 'sap' ? 'Campo SAP' : 'Campo Connekta'
    const mostrarMappingLineas = erpType === 'sap' && flowType !== 'items'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Mapeo y valores fijos{' '}
                <Tooltip title="Configuración que define cómo se transforman los datos que llegan del ERP antes de procesarlos. Incluye el renombramiento de campos de cabecera, de líneas de detalle (si aplica) y la asignación de valores constantes a todos los registros.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <h4 className="flujo-seccion__subtitulo">
                Mapeo de campos{' '}
                <Tooltip title={mostrarMappingLineas
                    ? 'Renombra los campos de cabecera del documento que vienen del ERP a los alias canónicos del sistema. Por ejemplo, "CardCode" → "proveedor". Solo se renombran los campos listados aquí; los que no estén se conservan con su nombre original. Para los campos que vienen dentro de las líneas de detalle, usar el mapeo de líneas de abajo.'
                    : 'Renombra los campos que vienen del ERP a los nombres que el sistema espera internamente (alias canónicos). Por ejemplo, el ERP puede enviar un campo llamado "Referencia_Item" pero el sistema necesita que se llame "referencia". Solo se renombran los campos listados aquí; los que no estén en la tabla se conservan con su nombre original.'
                }>
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

            {mostrarMappingLineas && (
                <>
                    <h4 className="flujo-seccion__subtitulo" style={{ marginTop: 24 }}>
                        Mapeo de líneas de detalle{' '}
                        <Tooltip title="Los documentos de SAP traen líneas anidadas dentro de cada registro (BPAddresses en terceros, DocumentLines en compras/ventas, StockTransferLines en transferencias). El sistema aplana estas líneas en filas individuales combinando la cabecera con cada línea. Este mapeo renombra los campos que vienen dentro de esas líneas, a diferencia del mapeo de campos de arriba que renombra los de cabecera.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </h4>

                    <div className="flujo-campos">
                        <div className="flujo-campo">
                            <label className="flujo-campo__label">
                                Campo origen de las líneas{' '}
                                <Tooltip title="Nombre del campo en la respuesta de SAP que contiene el array de líneas anidadas. Para terceros es 'BPAddresses' (direcciones), para compras/ventas es 'DocumentLines' (líneas del documento), para transferencias es 'StockTransferLines'. El sistema busca este campo dentro de cada registro y lo aplana.">
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </label>
                            <Input
                                className="flujo-input-mono"
                                value={config.mapping_lineas_campo || ''}
                                onChange={(e) => onChange({ ...config, mapping_lineas_campo: e.target.value })}
                                placeholder="ej: BPAddresses, DocumentLines, StockTransferLines"
                            />
                        </div>
                    </div>

                    <div className="flujo-campo flujo-campo--ancho" style={{ marginTop: 12 }}>
                        <TablaClaveValor
                            columnas={['Campo SAP (línea)', 'Alias canónico']}
                            datos={config.mapping_lineas_tabla || []}
                            onChange={(nuevos) => onChange({ ...config, mapping_lineas_tabla: nuevos })}
                            placeholders={['AddressName', 'sucursal']}
                        />
                    </div>
                </>
            )}

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
        </div>
    )
}

export default SeccionMapping

import { Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const SeccionMapping = ({ erpType, config, onChange }) => {
    const etiquetaCampoOrigen = erpType === 'sap' ? 'Campo SAP' : 'Campo Connekta'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Mapeo y valores fijos{' '}
                <Tooltip title="Configuración que define cómo se transforman los datos que llegan del ERP antes de procesarlos. Incluye el renombramiento de campos y la asignación de valores constantes a todos los registros">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

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
        </div>
    )
}

export default SeccionMapping

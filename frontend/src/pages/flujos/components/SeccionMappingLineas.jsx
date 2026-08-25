import { Input } from 'antd'
import TablaClaveValor from './TablaClaveValor'

const SeccionMappingLineas = ({ config, onChange }) => {
    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Mapping de lineas (detalle)</h3>
            <p className="flujo-seccion__ayuda">
                Los documentos de SAP traen lineas anidadas (BPAddresses, DocumentLines, StockTransferLines).
                El mapping de lineas aplana esas lineas en filas individuales.
            </p>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Nombre del campo de lineas</label>
                    <Input
                        className="flujo-input-mono"
                        value={config.mapping_lineas_campo || ''}
                        onChange={(e) => onChange({ ...config, mapping_lineas_campo: e.target.value })}
                        placeholder="ej: DocumentLines, BPAddresses, StockTransferLines"
                    />
                </div>

                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Mapping de campos de linea
                    </label>
                    <TablaClaveValor
                        columnas={['Campo SAP (linea)', 'Alias canonico']}
                        datos={config.mapping_lineas_tabla || []}
                        onChange={(nuevos) => onChange({ ...config, mapping_lineas_tabla: nuevos })}
                        placeholders={['ItemCode', 'producto']}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionMappingLineas

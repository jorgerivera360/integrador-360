import TablaClaveValor from './TablaClaveValor'

const SeccionMapping = ({ erpType, config, onChange }) => {
    const etiquetaCampoOrigen = erpType === 'sap' ? 'Campo SAP' : 'Campo SIESA'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Transformacion de datos</h3>

            <div className="flujo-campos">
                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Mapping (cabecera)
                        <span className="flujo-campo__hint">
                            Renombra campos del ERP a alias canonicos del integrador
                        </span>
                    </label>
                    <TablaClaveValor
                        columnas={[etiquetaCampoOrigen, 'Alias canonico']}
                        datos={config.mapping_tabla || []}
                        onChange={(nuevos) => onChange({ ...config, mapping_tabla: nuevos })}
                        placeholders={['ItemCode', 'referencia']}
                    />
                </div>

                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Hardcodes
                        <span className="flujo-campo__hint">
                            Valores fijos asignados despues del mapping (usa alias canonicos)
                        </span>
                    </label>
                    <TablaClaveValor
                        columnas={['Campo', 'Valor fijo']}
                        datos={config.hardcodes_tabla || []}
                        onChange={(nuevos) => onChange({ ...config, hardcodes_tabla: nuevos })}
                        placeholders={['estado', 'draft']}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionMapping

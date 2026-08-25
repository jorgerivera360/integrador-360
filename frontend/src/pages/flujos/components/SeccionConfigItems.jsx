import TablaClaveValor from './TablaClaveValor'

const SeccionConfigItems = ({ config, onChange }) => {
    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Configuracion del flujo — Productos</h3>

            <div className="flujo-campo flujo-campo--ancho">
                <label className="flujo-campo__label">
                    Mapeo de unidades de medida (uom_mapping)
                    <span className="flujo-campo__hint">
                        Convierte la unidad del ERP al nombre exacto en Odoo
                    </span>
                </label>
                <TablaClaveValor
                    columnas={['Unidad ERP', 'Unidad Odoo']}
                    datos={config.uom_mapping_tabla || []}
                    onChange={(nuevos) => onChange({ ...config, uom_mapping_tabla: nuevos })}
                    placeholders={['UND', 'Unidades']}
                />
            </div>
        </div>
    )
}

export default SeccionConfigItems

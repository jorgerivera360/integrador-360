import TablaClaveValor from './TablaClaveValor'

const SeccionConfigTransacciones = ({ flowType, config, onChange }) => {
    const titulo = flowType === 'purchases'
        ? 'Configuracion del flujo — Documentos de entrada'
        : 'Configuracion del flujo — Documentos de salida'

    const hint = flowType === 'purchases'
        ? 'Mapea la bodega del ERP al picking_type_id de Odoo'
        : 'Mapea la bodega del ERP al warehouse_id de Odoo'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">{titulo}</h3>

            <div className="flujo-campo flujo-campo--ancho">
                <label className="flujo-campo__label">
                    Mapeo de almacenes (warehouse_mapping)
                    <span className="flujo-campo__hint">{hint}</span>
                </label>
                <TablaClaveValor
                    columnas={['Bodega ERP', 'ID Odoo']}
                    datos={config.warehouse_mapping_tabla || []}
                    onChange={(nuevos) => onChange({ ...config, warehouse_mapping_tabla: nuevos })}
                    placeholders={['001', '15']}
                />
            </div>
        </div>
    )
}

export default SeccionConfigTransacciones

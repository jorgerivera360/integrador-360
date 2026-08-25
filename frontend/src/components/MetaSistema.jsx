import '@/styles/pagina.css'

/**
 * Metadatos de un registro: fechas, autores, ID interno.
 *
 * Va al pie de la sección, discreto. Es información de contexto —quién y
 * cuándo—, no datos con los que se trabaje, así que no compite visualmente
 * con el formulario.
 *
 * `items`: [{ label, valor }]. Los que vengan sin valor se omiten en vez de
 * ocupar espacio con un guion.
 */
const MetaSistema = ({ items = [] }) => {
    const visibles = items.filter(
        (item) => item.valor !== null && item.valor !== undefined && item.valor !== ''
    )

    if (visibles.length === 0) return null

    return (
        <div className="meta-sistema">
            {visibles.map((item) => (
                <span className="meta-sistema__item" key={item.label}>
                    {item.label}: <span className="meta-sistema__valor">{item.valor}</span>
                </span>
            ))}
        </div>
    )
}

export default MetaSistema

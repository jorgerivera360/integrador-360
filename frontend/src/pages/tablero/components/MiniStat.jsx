import { Skeleton } from 'antd'

/**
 * Contador compacto con punto de color.
 * `tono`: verde · naranja · rojo · azul (el azul pulsa, para "en curso").
 */
const MiniStat = ({ tono, etiqueta, valor, cargando = false }) => (
    <div className="tarjeta mini">
        <span className={`mini__punto mini__punto--${tono}`} />
        <span className="mini__etiqueta">{etiqueta}</span>
        {cargando ? (
            <span className="mini__valor">
                <Skeleton.Input active size="small" style={{ width: 40, height: 18 }} />
            </span>
        ) : (
            <span className="mini__valor">{valor}</span>
        )}
    </div>
)

export default MiniStat

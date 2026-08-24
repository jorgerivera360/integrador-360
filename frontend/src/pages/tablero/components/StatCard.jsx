import { Skeleton } from 'antd'

/**
 * Tarjeta de estadística: ícono con fondo de color + etiqueta + valor.
 * `tono` controla el fondo del ícono: azul · indigo · morado · verde.
 */
const StatCard = ({ icono, tono = 'azul', etiqueta, valor, valorVerde = false, cargando = false }) => (
    <div className="tarjeta stat">
        <div className={`stat__icono stat__icono--${tono}`}>{icono}</div>
        <div>
            <div className="stat__etiqueta">{etiqueta}</div>
            {cargando ? (
                <Skeleton.Input active size="small" style={{ width: 72, height: 30 }} />
            ) : (
                <div className={`stat__valor${valorVerde ? ' stat__valor--verde' : ''}`}>
                    {valor}
                </div>
            )}
        </div>
    </div>
)

export default StatCard

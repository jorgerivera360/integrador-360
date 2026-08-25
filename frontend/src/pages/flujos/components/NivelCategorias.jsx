import { Alert, Button, Spin } from 'antd'
import ErpTag from '@/components/ErpTag'
import ActivoTag from '@/components/ActivoTag'
import { useFlowsCliente, mensajeDeError } from '@/hooks/useFlujos'
import { IconProductos, IconClientes, IconProveedores, IconEntrada, IconSalida, IconVolver } from '../icons'

const CATEGORIAS = {
    items:     { titulo: 'Productos',   grupo: 'maestros',      icono: IconProductos,   color: '#1677ff' },
    customer:  { titulo: 'Clientes',    grupo: 'maestros',      icono: IconClientes,    color: '#52c41a' },
    supplier:  { titulo: 'Proveedores', grupo: 'maestros',      icono: IconProveedores, color: '#fa8c16' },
    purchases: { titulo: 'Entrada',     grupo: 'transacciones', icono: IconEntrada,     color: '#1677ff' },
    sales:     { titulo: 'Salida',      grupo: 'transacciones', icono: IconSalida,      color: '#52c41a' },
}

const NivelCategorias = ({ cliente, onSeleccionar, onVolver }) => {
    const { data: flows, isPending, isError, error, refetch } = useFlowsCliente(cliente.id)

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudieron cargar los flujos"
                description={mensajeDeError(error)}
                action={<Button size="small" onClick={() => refetch()}>Reintentar</Button>}
            />
        )
    }

    const conteo = {}
    if (flows) {
        for (const flow of flows) {
            conteo[flow.flow_type] = (conteo[flow.flow_type] || 0) + 1
        }
    }

    const totalFlows = flows?.length || 0

    const todasMaestros = Object.entries(CATEGORIAS).filter(([, c]) => c.grupo === 'maestros')
    const todasTransacciones = Object.entries(CATEGORIAS).filter(([, c]) => c.grupo === 'transacciones')

    return (
        <>
            <div className="flujo-cabecera-nivel">
                <button className="flujo-volver" onClick={onVolver}>
                    <IconVolver /> Volver
                </button>
            </div>

            <div className="flujo-cliente-head">
                <div className="flujo-cliente-head__info">
                    <h1 className="flujo-cliente-head__nombre">{cliente.name}</h1>
                    <div className="flujo-cliente-head__tags">
                        <ErpTag erpType={cliente.erp_type} />
                        <ActivoTag activo={cliente.is_active} />
                    </div>
                </div>
                <p className="flujo-cliente-head__meta">
                    {totalFlows} {totalFlows === 1 ? 'flujo configurado' : 'flujos configurados'}
                </p>
            </div>

            {isPending ? (
                <div className="flujo-cargando"><Spin /></div>
            ) : (
                <>
                    <div className="flujo-grupo">
                        <h3 className="flujo-grupo__titulo">Maestros</h3>
                        <div className="flujo-tarjetas">
                            {todasMaestros.map(([tipo, cat]) => {
                                const Icono = cat.icono
                                const cantidad = conteo[tipo] || 0
                                const vacia = cantidad === 0
                                return (
                                    <button
                                        key={tipo}
                                        className={`flujo-tarjeta ${vacia ? 'flujo-tarjeta--vacia' : ''}`}
                                        style={{ borderLeftColor: vacia ? '#d9d9d9' : cat.color }}
                                        onClick={() => onSeleccionar(tipo)}
                                    >
                                        <div
                                            className="flujo-tarjeta__icono"
                                            style={{ color: vacia ? '#bfbfbf' : cat.color }}
                                        >
                                            <Icono />
                                        </div>
                                        <div className="flujo-tarjeta__texto">
                                            <span className="flujo-tarjeta__titulo">{cat.titulo}</span>
                                            <span className={`flujo-tarjeta__conteo ${vacia ? 'flujo-tarjeta__conteo--vacio' : ''}`}>
                                                {vacia
                                                    ? 'Sin flujos'
                                                    : `${cantidad} ${cantidad === 1 ? 'flujo' : 'flujos'}`
                                                }
                                            </span>
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                    </div>

                    <div className="flujo-grupo">
                        <h3 className="flujo-grupo__titulo">Transacciones</h3>
                        <div className="flujo-tarjetas">
                            {todasTransacciones.map(([tipo, cat]) => {
                                const Icono = cat.icono
                                const cantidad = conteo[tipo] || 0
                                const vacia = cantidad === 0
                                return (
                                    <button
                                        key={tipo}
                                        className={`flujo-tarjeta ${vacia ? 'flujo-tarjeta--vacia' : ''}`}
                                        style={{ borderLeftColor: vacia ? '#d9d9d9' : cat.color }}
                                        onClick={() => onSeleccionar(tipo)}
                                    >
                                        <div
                                            className="flujo-tarjeta__icono"
                                            style={{ color: vacia ? '#bfbfbf' : cat.color }}
                                        >
                                            <Icono />
                                        </div>
                                        <div className="flujo-tarjeta__texto">
                                            <span className="flujo-tarjeta__titulo">{cat.titulo}</span>
                                            <span className={`flujo-tarjeta__conteo ${vacia ? 'flujo-tarjeta__conteo--vacio' : ''}`}>
                                                {vacia
                                                    ? 'Sin flujos'
                                                    : `${cantidad} ${cantidad === 1 ? 'flujo' : 'flujos'}`
                                                }
                                            </span>
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                    </div>
                </>
            )}
        </>
    )
}

export default NivelCategorias

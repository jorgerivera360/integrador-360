import { Alert, Button, Spin } from 'antd'
import ErpTag from '@/components/ErpTag'
import ActivoTag from '@/components/ActivoTag'
import { useFlowsCliente, mensajeDeError } from '@/hooks/useEjecuciones'
import { IconProductos, IconClientes, IconProveedores, IconEntrada, IconSalida, IconVolver } from '../icons'

const CATEGORIAS = {
    items:    { titulo: 'Productos',    grupo: 'maestros',       icono: IconProductos, color: '#1677ff' },
    customer: { titulo: 'Clientes',     grupo: 'maestros',       icono: IconClientes,  color: '#52c41a' },
    supplier: { titulo: 'Proveedores',  grupo: 'maestros',       icono: IconProveedores, color: '#fa8c16' },
    purchases: { titulo: 'Entrada',     grupo: 'transacciones',  icono: IconEntrada,   color: '#1677ff' },
    sales:    { titulo: 'Salida',       grupo: 'transacciones',  icono: IconSalida,    color: '#52c41a' },
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

    const tarjetasConFlows = Object.entries(CATEGORIAS).filter(([tipo]) => conteo[tipo] > 0)
    const grupoMaestros = tarjetasConFlows.filter(([, c]) => c.grupo === 'maestros')
    const grupoTransacciones = tarjetasConFlows.filter(([, c]) => c.grupo === 'transacciones')

    const totalFlows = flows?.length || 0

    return (
        <>
            <div className="ejec-cabecera-nivel">
                <button className="ejec-volver" onClick={onVolver}>
                    <IconVolver /> Volver
                </button>
            </div>

            <div className="ejec-cliente-head">
                <div className="ejec-cliente-head__info">
                    <h1 className="ejec-cliente-head__nombre">{cliente.name}</h1>
                    <div className="ejec-cliente-head__tags">
                        <ErpTag erpType={cliente.erp_type} />
                        <ActivoTag activo={cliente.is_active} />
                    </div>
                </div>
                <p className="ejec-cliente-head__meta">
                    {totalFlows} {totalFlows === 1 ? 'flujo configurado' : 'flujos configurados'}
                </p>
            </div>

            {isPending ? (
                <div className="ejec-cargando"><Spin /></div>
            ) : totalFlows === 0 ? (
                <div className="ejec-vacio">Este cliente no tiene flujos configurados</div>
            ) : (
                <>
                    {grupoMaestros.length > 0 && (
                        <div className="ejec-grupo">
                            <h3 className="ejec-grupo__titulo">Maestros</h3>
                            <div className="ejec-tarjetas">
                                {grupoMaestros.map(([tipo, cat]) => {
                                    const Icono = cat.icono
                                    return (
                                        <button
                                            key={tipo}
                                            className="ejec-tarjeta"
                                            style={{ borderLeftColor: cat.color }}
                                            onClick={() => onSeleccionar(tipo)}
                                        >
                                            <div className="ejec-tarjeta__icono" style={{ color: cat.color }}>
                                                <Icono />
                                            </div>
                                            <div className="ejec-tarjeta__texto">
                                                <span className="ejec-tarjeta__titulo">{cat.titulo}</span>
                                                <span className="ejec-tarjeta__conteo">
                                                    {conteo[tipo]} {conteo[tipo] === 1 ? 'flujo' : 'flujos'}
                                                </span>
                                            </div>
                                        </button>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {grupoTransacciones.length > 0 && (
                        <div className="ejec-grupo">
                            <h3 className="ejec-grupo__titulo">Transacciones</h3>
                            <div className="ejec-tarjetas">
                                {grupoTransacciones.map(([tipo, cat]) => {
                                    const Icono = cat.icono
                                    return (
                                        <button
                                            key={tipo}
                                            className="ejec-tarjeta"
                                            style={{ borderLeftColor: cat.color }}
                                            onClick={() => onSeleccionar(tipo)}
                                        >
                                            <div className="ejec-tarjeta__icono" style={{ color: cat.color }}>
                                                <Icono />
                                            </div>
                                            <div className="ejec-tarjeta__texto">
                                                <span className="ejec-tarjeta__titulo">{cat.titulo}</span>
                                                <span className="ejec-tarjeta__conteo">
                                                    {conteo[tipo]} {conteo[tipo] === 1 ? 'flujo' : 'flujos'}
                                                </span>
                                            </div>
                                        </button>
                                    )
                                })}
                            </div>
                        </div>
                    )}
                </>
            )}
        </>
    )
}

export default NivelCategorias

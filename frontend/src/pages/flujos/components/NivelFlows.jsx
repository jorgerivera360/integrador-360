import { Alert, Button, Spin, Table, message } from 'antd'
import ErpTag from '@/components/ErpTag'
import ActivoTag from '@/components/ActivoTag'
import EstadoTag from '@/components/EstadoTag'
import useHasRole from '@/hooks/useHasRole'
import { useFlowsCliente, useEjecutarFlow, mensajeDeError } from '@/hooks/useFlujos'
import { formatDesde } from '@/utils/format'
import { IconVolver, IconMas, IconPlay } from '../icons'

const TITULOS_TIPO = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Entrada',
    sales: 'Salida',
}

const NivelFlows = ({ cliente, flowType, onEditar, onCrear, onVolver }) => {
    const { data: todosFlows, isPending, isError, error, refetch } = useFlowsCliente(cliente.id)
    const ejecutar = useEjecutarFlow()
    const puedeEditar = useHasRole(['superadmin', 'admin'])

    const flows = todosFlows?.filter((f) => f.flow_type === flowType) || []
    const tituloTipo = TITULOS_TIPO[flowType] || flowType

    const handleEjecutar = (e, flow) => {
        e.stopPropagation()
        ejecutar.mutate(flow.id, {
            onSuccess: () => message.success(`Ejecucion de "${flow.flow_name}" iniciada`),
            onError: (err) => message.error(mensajeDeError(err, 'No se pudo iniciar la ejecucion')),
        })
    }

    const columnas = [
        {
            title: 'Nombre',
            dataIndex: 'flow_name',
            key: 'flow_name',
            render: (nombre) => (
                <span className="flujo-flow-link">{nombre}</span>
            ),
        },
        {
            title: 'Cron',
            dataIndex: 'schedule_cron',
            key: 'schedule_cron',
            width: 150,
            render: (cron) => (
                <span className="flujo-cron">{cron || '—'}</span>
            ),
        },
        {
            title: 'Orden',
            dataIndex: 'execution_order',
            key: 'execution_order',
            align: 'center',
            width: 80,
            className: 'celda-tenue',
        },
        {
            title: 'Estado',
            dataIndex: 'is_active',
            key: 'is_active',
            align: 'center',
            width: 120,
            render: (activo) => <ActivoTag activo={activo} />,
        },
        {
            title: 'Ultima ejecucion',
            key: 'ultima',
            className: 'celda-fecha',
            width: 180,
            render: () => '—',
        },
        ...(puedeEditar ? [{
            title: 'Acciones',
            key: 'acciones',
            align: 'center',
            width: 100,
            render: (_, flow) => (
                <Button
                    size="small"
                    type="primary"
                    ghost
                    disabled={!flow.is_active}
                    icon={<IconPlay />}
                    onClick={(e) => handleEjecutar(e, flow)}
                    loading={ejecutar.isPending && ejecutar.variables === flow.id}
                >
                    Ejecutar
                </Button>
            ),
        }] : []),
    ]

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

    return (
        <>
            <div className="flujo-cabecera-nivel">
                <button className="flujo-volver" onClick={onVolver}>
                    <IconVolver /> Volver
                </button>
            </div>

            <div className="flujo-flow-head">
                <div className="flujo-flow-head__izq">
                    <h1 className="flujo-flow-head__titulo">
                        {tituloTipo}
                        <span className="flujo-flow-head__separador">—</span>
                        {cliente.name}
                    </h1>
                    <ErpTag erpType={cliente.erp_type} />
                </div>
                {puedeEditar && (
                    <Button
                        type="primary"
                        icon={<IconMas />}
                        onClick={() => onCrear(flowType)}
                    >
                        Crear flujo
                    </Button>
                )}
            </div>

            {isPending ? (
                <div className="flujo-cargando"><Spin /></div>
            ) : (
                <div className="tarjeta-borde">
                    <Table
                        className="tabla-panel tabla-panel--clicable"
                        columns={columnas}
                        dataSource={flows}
                        rowKey="id"
                        scroll={{ x: 700 }}
                        onRow={(flow) => ({
                            onClick: () => onEditar(flow),
                        })}
                        pagination={false}
                        locale={{ emptyText: `No hay flujos de tipo ${tituloTipo.toLowerCase()}` }}
                    />
                </div>
            )}
        </>
    )
}

export default NivelFlows

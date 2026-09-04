import { useMemo } from 'react'
import { Alert, Button, Spin, Table, message } from 'antd'
import ErpTag from '@/components/ErpTag'
import ActivoTag from '@/components/ActivoTag'
import useHasRole from '@/hooks/useHasRole'
import { useFlowsClienteSummary, useEjecutarFlow, useCancelarFlow, mensajeDeError } from '@/hooks/useFlujos'
import { formatFechaHora } from '@/utils/format'
import { IconVolver, IconMas, IconPlay, IconStop } from '../icons'

const TITULOS_TIPO = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Entrada',
    sales: 'Salida',
}

const NivelFlows = ({ cliente, flowType, onEditar, onCrear, onVolver }) => {
    const { data: todosFlows, isPending, isError, error, refetch } = useFlowsClienteSummary(cliente.id)
    const ejecutar = useEjecutarFlow()
    const cancelar = useCancelarFlow()
    const puedeEditar = useHasRole(['superadmin', 'admin'])

    const flows = todosFlows?.filter((f) => f.flow_type === flowType) || []
    const tituloTipo = TITULOS_TIPO[flowType] || flowType

    const handleEjecutar = (e, flow) => {
        e.stopPropagation()
        ejecutar.mutate(flow.id, {
            onSuccess: () => message.success(`Ejecución de "${flow.flow_name}" iniciada`),
            onError: (err) => message.error(mensajeDeError(err, 'No se pudo iniciar la ejecución')),
        })
    }

    const handleCancelar = (e, flow) => {
        e.stopPropagation()
        cancelar.mutate(flow.id, {
            onSuccess: () => message.success(`Cancelación de "${flow.flow_name}" solicitada`),
            onError: (err) => message.error(mensajeDeError(err, 'No se pudo cancelar la ejecución')),
        })
    }

    const columnas = useMemo(() => [
        {
            title: 'Nombre',
            dataIndex: 'flow_name',
            key: 'flow_name',
            width: 200,
            sorter: (a, b) => a.flow_name.localeCompare(b.flow_name, 'es'),
            render: (nombre) => (
                <span className="flujo-flow-link">{nombre}</span>
            ),
        },
        {
            title: 'Cron',
            dataIndex: 'schedule_cron',
            key: 'schedule_cron',
            width: 150,
            sorter: (a, b) => (a.schedule_cron || '').localeCompare(b.schedule_cron || ''),
            render: (cron) => (
                <span className="flujo-cron">{cron || '—'}</span>
            ),
        },
        {
            title: 'Estado',
            dataIndex: 'is_active',
            key: 'is_active',
            align: 'center',
            width: 100,
            sorter: (a, b) => Number(a.is_active) - Number(b.is_active),
            render: (activo) => <ActivoTag activo={activo} />,
        },
        {
            title: 'Última ejecución',
            dataIndex: 'last_execution',
            key: 'ultima',
            className: 'celda-fecha',
            width: 180,
            sorter: (a, b) => new Date(a.last_execution || 0) - new Date(b.last_execution || 0),
            render: (fecha) => fecha ? formatFechaHora(fecha) : '—',
        },
        ...(puedeEditar ? [{
            title: 'Acciones',
            key: 'acciones',
            align: 'center',
            width: 200,
            render: (_, flow) => (
                <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
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
                    <Button
                        size="small"
                        danger
                        ghost
                        icon={<IconStop />}
                        onClick={(e) => handleCancelar(e, flow)}
                        loading={cancelar.isPending && cancelar.variables === flow.id}
                    >
                        Detener
                    </Button>
                </div>
            ),
        }] : []),
    ], [puedeEditar, ejecutar.isPending, ejecutar.variables, cancelar.isPending, cancelar.variables])

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

import { useMemo } from 'react'
import { Alert, Button, Spin, Table } from 'antd'
import ErpTag from '@/components/ErpTag'
import ActivoTag from '@/components/ActivoTag'
import { useFlowsCliente, mensajeDeError } from '@/hooks/useEjecuciones'
import { formatFechaHora } from '@/utils/format'
import { IconVolver } from '../icons'

const TITULOS_TIPO = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Entrada',
    sales: 'Salida',
}

const NivelFlows = ({ cliente, flowType, onSeleccionar, onVolver }) => {
    const { data: todosFlows, isPending, isError, error, refetch } = useFlowsCliente(cliente.id)

    const flows = todosFlows?.filter((f) => f.flow_type === flowType) || []
    const tituloTipo = TITULOS_TIPO[flowType] || flowType

    const columnas = useMemo(() => [
        {
            title: 'Nombre',
            dataIndex: 'flow_name',
            key: 'flow_name',
            width: 200,
            sorter: (a, b) => a.flow_name.localeCompare(b.flow_name, 'es'),
            render: (nombre) => (
                <span className="ejec-flow-link">{nombre}</span>
            ),
        },
        {
            title: 'Estado',
            dataIndex: 'is_active',
            key: 'is_active',
            align: 'center',
            width: 120,
            sorter: (a, b) => Number(a.is_active) - Number(b.is_active),
            render: (activo) => <ActivoTag activo={activo} />,
        },
        {
            title: 'Última ejecución',
            dataIndex: 'last_execution',
            key: 'ultima',
            width: 170,
            sorter: (a, b) => new Date(a.last_execution || 0) - new Date(b.last_execution || 0),
            render: (fecha) => fecha ? formatFechaHora(fecha) : '—',
        },
    ], [])

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
            <div className="ejec-cabecera-nivel">
                <button className="ejec-volver" onClick={onVolver}>
                    <IconVolver /> Volver
                </button>
            </div>

            <div className="ejec-flow-head">
                <h1 className="ejec-flow-head__titulo">
                    {tituloTipo}
                    <span className="ejec-flow-head__separador">—</span>
                    {cliente.name}
                </h1>
                <ErpTag erpType={cliente.erp_type} />
            </div>

            {isPending ? (
                <div className="ejec-cargando"><Spin /></div>
            ) : (
                <div className="tarjeta-borde">
                    <Table
                        className="tabla-panel tabla-panel--clicable"
                        columns={columnas}
                        dataSource={flows}
                        rowKey="id"
                        scroll={{ x: 500 }}
                        onRow={(flow) => ({
                            onClick: () => onSeleccionar(flow),
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

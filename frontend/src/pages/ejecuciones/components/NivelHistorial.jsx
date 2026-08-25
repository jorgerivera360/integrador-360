import { useState } from 'react'
import { Alert, Button, Select, Space, Spin, Table } from 'antd'
import ErpTag from '@/components/ErpTag'
import EstadoTag from '@/components/EstadoTag'
import { useHistorialEjecuciones, mensajeDeError } from '@/hooks/useEjecuciones'
import { formatFechaHora, formatDuracion } from '@/utils/format'
import DrawerEjecucion from './DrawerEjecucion'
import { IconVolver } from '../icons'

const OPCIONES_ESTADO = [
    { value: null, label: 'Todos' },
    { value: 'success', label: 'Exito' },
    { value: 'partial', label: 'Parcial' },
    { value: 'error', label: 'Error' },
    { value: 'running', label: 'En curso' },
]

const OPCIONES_DISPARADO = [
    { value: null, label: 'Todos' },
    { value: 'scheduler', label: 'Scheduler' },
    { value: 'manual', label: 'Manual' },
]

const DisparadoTag = ({ tipo }) => {
    const esManual = tipo === 'manual'
    return (
        <span
            className="tag-base"
            style={{
                color: esManual ? '#0958d9' : '#595959',
                background: esManual ? '#e6f4ff' : '#fafafa',
                borderColor: esManual ? '#91caff' : '#d9d9d9',
            }}
        >
            {tipo === 'scheduler' ? 'Scheduler' : tipo === 'manual' ? 'Manual' : tipo || '—'}
        </span>
    )
}

const NivelHistorial = ({ cliente, flow, onVolver }) => {
    const [filtros, setFiltros] = useState({ status: null, triggeredBy: null })
    const [drawerAbierto, setDrawerAbierto] = useState(false)
    const [ejecucionActiva, setEjecucionActiva] = useState(null)

    const { data: ejecuciones, isPending, isError, error, refetch } =
        useHistorialEjecuciones(flow.id, filtros)

    const cambiar = (campo) => (nuevo) => setFiltros({ ...filtros, [campo]: nuevo ?? null })

    const abrirDrawer = (ejecucion) => {
        setEjecucionActiva(ejecucion)
        setDrawerAbierto(true)
    }

    const columnas = [
        {
            title: '#',
            dataIndex: 'id',
            key: 'id',
            width: 70,
            className: 'celda-tenue',
        },
        {
            title: 'Fecha',
            dataIndex: 'started_at',
            key: 'started_at',
            className: 'celda-fecha',
            render: (fecha) => formatFechaHora(fecha),
        },
        {
            title: 'Duracion',
            key: 'duracion',
            width: 100,
            className: 'celda-tenue',
            render: (_, rec) => formatDuracion(rec.started_at, rec.finished_at),
        },
        {
            title: 'Estado',
            dataIndex: 'status',
            key: 'status',
            align: 'center',
            width: 110,
            render: (estado) => <EstadoTag estado={estado} />,
        },
        {
            title: 'Disparado por',
            dataIndex: 'triggered_by',
            key: 'triggered_by',
            align: 'center',
            width: 130,
            render: (tipo) => <DisparadoTag tipo={tipo} />,
        },
        {
            title: 'Creados',
            key: 'creados',
            align: 'center',
            width: 90,
            className: 'celda-tenue',
            render: (_, rec) => rec.result?.creados ?? '—',
        },
        {
            title: 'Fallidos',
            key: 'fallidos',
            align: 'center',
            width: 90,
            render: (_, rec) => {
                const n = rec.result?.fallidos?.length ?? rec.result?.fallidos_count ?? 0
                return (
                    <span className={n > 0 ? 'ejec-fallidos--rojo' : 'celda-tenue'}>
                        {n}
                    </span>
                )
            },
        },
    ]

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar el historial"
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
                <div>
                    <h1 className="ejec-flow-head__titulo">
                        {flow.flow_name}
                        <span className="ejec-flow-head__separador">—</span>
                        {cliente.name}
                    </h1>
                    <p className="ejec-flow-head__sub">Historial de ejecuciones</p>
                </div>
                <ErpTag erpType={cliente.erp_type} />
            </div>

            <Space className="ejec-filtros" wrap size={12}>
                <Select
                    className="ejec-filtros__select"
                    placeholder="Estado: todos"
                    value={filtros.status}
                    onChange={cambiar('status')}
                    options={OPCIONES_ESTADO}
                    allowClear
                />
                <Select
                    className="ejec-filtros__select"
                    placeholder="Disparado por: todos"
                    value={filtros.triggeredBy}
                    onChange={cambiar('triggeredBy')}
                    options={OPCIONES_DISPARADO}
                    allowClear
                />
            </Space>

            {isPending ? (
                <div className="ejec-cargando"><Spin /></div>
            ) : (
                <div className="tarjeta-borde">
                    <Table
                        className="tabla-panel tabla-panel--clicable"
                        columns={columnas}
                        dataSource={ejecuciones}
                        rowKey="id"
                        scroll={{ x: 700 }}
                        onRow={(ejecucion) => ({
                            onClick: () => abrirDrawer(ejecucion),
                        })}
                        pagination={{
                            pageSize: 15,
                            showSizeChanger: false,
                            showTotal: (total, [desde, hasta]) =>
                                `Mostrando ${desde}-${hasta} de ${total} ejecuciones`,
                        }}
                        locale={{ emptyText: 'No hay ejecuciones registradas' }}
                    />
                </div>
            )}

            <DrawerEjecucion
                ejecucion={ejecucionActiva}
                abierto={drawerAbierto}
                onCerrar={() => setDrawerAbierto(false)}
            />
        </>
    )
}

export default NivelHistorial

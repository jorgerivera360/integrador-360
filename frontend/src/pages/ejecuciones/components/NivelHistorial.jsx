import { useState, useMemo } from 'react'
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

    const columnas = useMemo(() => [
        {
            title: 'Fecha',
            dataIndex: 'started_at',
            key: 'started_at',
            width: 170,
            defaultSortOrder: 'descend',
            sorter: (a, b) => new Date(a.started_at) - new Date(b.started_at),
            render: (fecha) => formatFechaHora(fecha),
        },
        {
            title: 'Duración',
            key: 'duracion',
            width: 100,
            className: 'celda-tenue',
            sorter: (a, b) => {
                const da = new Date(a.finished_at) - new Date(a.started_at)
                const db = new Date(b.finished_at) - new Date(b.started_at)
                return (da || 0) - (db || 0)
            },
            render: (_, rec) => formatDuracion(rec.started_at, rec.finished_at),
        },
        {
            title: 'Estado',
            dataIndex: 'status',
            key: 'status',
            align: 'center',
            width: 110,
            sorter: (a, b) => (a.status || '').localeCompare(b.status || '', 'es'),
            render: (estado) => <EstadoTag estado={estado} />,
        },
        {
            title: 'Disparado por',
            dataIndex: 'triggered_by',
            key: 'triggered_by',
            align: 'center',
            width: 130,
            sorter: (a, b) => (a.triggered_by || '').localeCompare(b.triggered_by || '', 'es'),
            render: (tipo) => <DisparadoTag tipo={tipo} />,
        },
        {
            title: 'Creados',
            key: 'creados',
            align: 'center',
            width: 90,
            className: 'celda-tenue',
            sorter: (a, b) => (a.result?.creados ?? 0) - (b.result?.creados ?? 0),
            render: (_, rec) => rec.result?.creados ?? '—',
        },
        {
            title: 'Actualizados',
            key: 'actualizados',
            align: 'center',
            width: 110,
            className: 'celda-tenue',
            sorter: (a, b) => (a.result?.actualizados ?? 0) - (b.result?.actualizados ?? 0),
            render: (_, rec) => rec.result?.actualizados ?? '—',
        },
        {
            title: 'Fallidos',
            key: 'fallidos',
            align: 'center',
            width: 90,
            sorter: (a, b) => {
                const fa = a.result?.fallidos?.length ?? a.result?.fallidos_count ?? 0
                const fb = b.result?.fallidos?.length ?? b.result?.fallidos_count ?? 0
                return fa - fb
            },
            render: (_, rec) => {
                const n = rec.result?.fallidos?.length ?? rec.result?.fallidos_count ?? 0
                return (
                    <span className={n > 0 ? 'ejec-fallidos--rojo' : 'celda-tenue'}>
                        {n}
                    </span>
                )
            },
        },
    ], [])

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

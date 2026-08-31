import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Table } from 'antd'
import EstadoTag from '@/components/EstadoTag'
import DrawerEjecucion from '@/pages/ejecuciones/components/DrawerEjecucion'
import { formatDuracion, formatFechaHora } from '@/utils/format'
import '@/pages/ejecuciones/ejecuciones.css'

const columnas = [
    {
        title: 'Cliente',
        key: 'cliente',
        width: 150,
        render: (_, fila) => fila.client_name || fila.client_slug || '—',
    },
    {
        title: 'Flujo',
        dataIndex: 'flow_name',
        key: 'flujo',
        width: 150,
    },
    {
        title: 'Estado',
        dataIndex: 'status',
        key: 'estado',
        width: 100,
        render: (estado) => <EstadoTag estado={estado} />,
    },
    {
        title: 'Fecha',
        dataIndex: 'started_at',
        key: 'fecha',
        width: 180,
        className: 'celda-num',
        render: (inicio) => formatFechaHora(inicio),
    },
    {
        title: 'Duración',
        key: 'duracion',
        width: 100,
        className: 'celda-num',
        render: (_, fila) => formatDuracion(fila.started_at, fila.finished_at),
    },
    {
        title: 'Disparado por',
        dataIndex: 'triggered_by',
        key: 'disparado',
        width: 120,
    },
]

const TablaRecientes = ({ ejecuciones = [], cargando = false }) => {
    const [drawerAbierto, setDrawerAbierto] = useState(false)
    const [ejecucionActiva, setEjecucionActiva] = useState(null)

    const abrirDrawer = (ejecucion) => {
        setEjecucionActiva(ejecucion)
        setDrawerAbierto(true)
    }

    return (
        <div className="tarjeta panel-tabla">
            <div className="panel-tabla__head">
                <span className="panel-tabla__titulo">Ejecuciones</span>
                <Link to="/ejecuciones">Ver todas</Link>
            </div>

            <Table
                className="tabla-panel tabla-panel--clicable"
                columns={columnas}
                dataSource={ejecuciones}
                rowKey="id"
                loading={cargando}
                pagination={{ pageSize: 10, showSizeChanger: false, size: 'small' }}
                scroll={{ x: 860 }}
                onRow={(ejecucion) => ({
                    onClick: () => abrirDrawer(ejecucion),
                })}
                locale={{
                    emptyText: 'Sin ejecuciones',
                }}
            />

            <DrawerEjecucion
                ejecucion={ejecucionActiva}
                abierto={drawerAbierto}
                onCerrar={() => setDrawerAbierto(false)}
            />
        </div>
    )
}

export default TablaRecientes

import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Table } from 'antd'
import EstadoTag, { etiquetaEstado } from '@/components/EstadoTag'
import FiltrosEjecuciones, { FILTROS_VACIOS, hayFiltros } from '@/components/FiltrosEjecuciones'
import { formatDuracion, formatFechaHora } from '@/utils/format'
import { contiene } from '@/utils/texto'

/** El nombre del cliente puede venir nulo; el slug siempre está. */
const nombreCliente = (fila) => fila.client_name || fila.client_slug || '—'

const columnas = [
    {
        title: 'Cliente',
        key: 'cliente',
        render: (_, fila) => nombreCliente(fila),
    },
    {
        title: 'Flujo',
        dataIndex: 'flow_name',
        key: 'flujo',
    },
    {
        title: 'Estado',
        dataIndex: 'status',
        key: 'estado',
        render: (estado) => <EstadoTag estado={estado} />,
    },
    {
        title: 'Fecha',
        dataIndex: 'started_at',
        key: 'fecha',
        className: 'celda-num',
        render: (inicio) => formatFechaHora(inicio),
    },
    {
        title: 'Duración',
        key: 'duracion',
        className: 'celda-num',
        render: (_, fila) => formatDuracion(fila.started_at, fila.finished_at),
    },
    {
        title: 'Disparado por',
        dataIndex: 'triggered_by',
        key: 'disparado',
    },
]

function aplicarFiltros(filas, filtros) {
    const desde = filtros.rango?.[0]?.startOf('day').valueOf()
    const hasta = filtros.rango?.[1]?.endOf('day').valueOf()

    return filas.filter((fila) => {
        if (!contiene(nombreCliente(fila), filtros.cliente)) return false
        if (!contiene(fila.flow_name, filtros.flujo)) return false

        // Se busca por el texto visible ('Éxito'), no por el valor crudo,
        // que es el que ve el usuario en la tabla.
        if (!contiene(etiquetaEstado(fila.status), filtros.estado)) return false

        if (desde || hasta) {
            const inicio = new Date(fila.started_at).getTime()
            if (Number.isNaN(inicio)) return false
            if (desde && inicio < desde) return false
            if (hasta && inicio > hasta) return false
        }

        return true
    })
}

/**
 * Últimas ejecuciones del tablero.
 *
 * Los filtros son en memoria sobre lo que ya trajo /dashboard/status
 * (las 10 más recientes). Para filtrar el histórico completo está la
 * pantalla de Ejecuciones.
 */
const TablaRecientes = ({ ejecuciones = [], cargando = false }) => {
    const [filtros, setFiltros] = useState(FILTROS_VACIOS)

    const filtradas = useMemo(
        () => aplicarFiltros(ejecuciones, filtros),
        [ejecuciones, filtros]
    )

    const filtrando = hayFiltros(filtros)

    return (
        <div className="tarjeta panel-tabla">
            <div className="panel-tabla__head">
                <span className="panel-tabla__titulo">Últimas ejecuciones</span>
                <Link to="/ejecuciones">Ver todas</Link>
            </div>

            <div className="panel-tabla__filtros">
                <FiltrosEjecuciones valor={filtros} onChange={setFiltros} />
                {filtrando && (
                    <span className="panel-tabla__conteo">
                        {filtradas.length} de {ejecuciones.length}
                    </span>
                )}
            </div>

            <Table
                columns={columnas}
                dataSource={filtradas}
                rowKey="id"
                loading={cargando}
                pagination={false}
                scroll={{ x: 860 }}
                locale={{
                    emptyText: filtrando
                        ? 'Ninguna ejecución coincide con los filtros'
                        : 'Sin ejecuciones registradas',
                }}
            />
        </div>
    )
}

export default TablaRecientes

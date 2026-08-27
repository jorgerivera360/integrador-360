import { useMemo, useState } from 'react'
import { Alert, Button, Table, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import useDebounce from '@/hooks/useDebounce'
import { useCambios, LIMITE_CAMBIOS } from '@/hooks/useCambios'
import { mensajeDeError } from '@/hooks/useClientes'
import { ACCIONES, etiquetaAccion } from '@/config/auditoria'
import { formatFechaHora } from '@/utils/format'
import FiltrosAuditoria, { FILTROS_VACIOS } from './components/FiltrosAuditoria'
import DetalleCambio from './components/DetalleCambio'
import { IconBorrar, IconCrear, IconEditar, IconTabla } from './icons'
import '@/styles/pagina.css'
import './auditoria.css'

const ICONO_ACCION = {
    create: <IconCrear />,
    update: <IconEditar />,
    delete: <IconBorrar />,
}

const AccionTag = ({ accion }) => {
    const config = ACCIONES[accion]
    if (!config) return <span className="celda-tenue">{accion || '—'}</span>

    return (
        <span
            className="accion-tag"
            style={{ color: config.color, background: config.fondo, borderColor: config.borde }}
        >
            {ICONO_ACCION[accion]}
            {config.label}
        </span>
    )
}

const NOMBRE_MODULO = {
    flows: 'Flujos',
    clients: 'Clientes',
    users: 'Usuarios',
}

function nombreModulo(tabla) {
    return NOMBRE_MODULO[tabla] || tabla
}

/** Valores únicos de un campo, para poblar un desplegable. */
function opcionesDe(filas, obtenerValor, obtenerEtiqueta = obtenerValor) {
    const mapa = new Map()
    filas.forEach((fila) => {
        const valor = obtenerValor(fila)
        if (valor === null || valor === undefined || valor === '') return
        if (!mapa.has(valor)) mapa.set(valor, obtenerEtiqueta(fila) ?? String(valor))
    })
    return [...mapa.entries()]
        .map(([value, label]) => ({ value, label }))
        .sort((a, b) => String(a.label).localeCompare(String(b.label), 'es'))
}

const columnas = [
    {
        title: 'Usuario',
        key: 'usuario',
        render: (_, cambio) =>
            cambio.changed_by_name ? (
                <div>
                    <div className="celda-usuario__nombre">{cambio.changed_by_name}</div>
                    <div className="celda-usuario__email">{cambio.changed_by_email}</div>
                </div>
            ) : (
                <span className="celda-tenue">Sistema</span>
            ),
    },
    {
        title: 'Acción',
        dataIndex: 'action',
        key: 'action',
        align: 'center',
        render: (accion) => <AccionTag accion={accion} />,
    },
    {
        title: 'Módulo',
        dataIndex: 'table_name',
        key: 'table_name',
        render: (tabla) => (
            <span className="celda-tabla">
                <IconTabla />
                {nombreModulo(tabla)}
            </span>
        ),
    },
    {
        title: 'Fecha',
        dataIndex: 'changed_at',
        key: 'changed_at',
        className: 'celda-fecha',
        defaultSortOrder: 'descend',
        sorter: (a, b) => new Date(a.changed_at) - new Date(b.changed_at),
        render: (fecha) => formatFechaHora(fecha),
    },
]

const AuditoriaPage = () => {
    const [filtros, setFiltros] = useState(FILTROS_VACIOS)

    // El ID se difiere: se escribe dígito a dígito y cada cambio va al servidor.
    const registroDiferido = useDebounce(filtros.recordId, 400)
    const { data: cambios, isPending, isError, error, refetch } = useCambios({
        recordId: registroDiferido,
    })

    const filas = useMemo(() => cambios ?? [], [cambios])

    // Las opciones salen de los datos crudos, antes de filtrar en memoria: así
    // el desplegable no se queda con una sola opción al usarlo.
    const opcionesTabla = useMemo(
        () => opcionesDe(filas, (f) => f.table_name, (f) => nombreModulo(f.table_name)),
        [filas]
    )
    const opcionesAccion = useMemo(
        () => opcionesDe(filas, (f) => f.action, (f) => etiquetaAccion(f.action)),
        [filas]
    )
    const opcionesUsuario = useMemo(
        () => opcionesDe(filas, (f) => f.changed_by, (f) => f.changed_by_name),
        [filas]
    )

    const filtradas = useMemo(
        () =>
            filas.filter((fila) => {
                if (filtros.tableName && fila.table_name !== filtros.tableName) return false
                if (filtros.action && fila.action !== filtros.action) return false
                if (filtros.changedBy && fila.changed_by !== filtros.changedBy) return false
                return true
            }),
        [filas, filtros.tableName, filtros.action, filtros.changedBy]
    )

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar el historial de cambios"
                description={mensajeDeError(error)}
                action={
                    <Button size="small" onClick={() => refetch()}>
                        Reintentar
                    </Button>
                }
            />
        )
    }

    const alcanzoElTope = filas.length >= LIMITE_CAMBIOS

    return (
        <>
            <div className="pagina-head">
                <div>
                    <h1 className="pagina-head__titulo">
                        Auditoría{' '}
                        <Tooltip title="Registro de todas las modificaciones realizadas en la configuración del sistema">
                            <InfoCircleOutlined style={{ fontSize: 16, color: '#8c8c8c', cursor: 'pointer', verticalAlign: 'middle' }} />
                        </Tooltip>
                    </h1>
                </div>
            </div>

            <FiltrosAuditoria
                valor={filtros}
                onChange={setFiltros}
                tablas={opcionesTabla}
                acciones={opcionesAccion}
                usuarios={opcionesUsuario}
            />

            {alcanzoElTope && !filtros.recordId && (
                <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message={`Se muestran los ${LIMITE_CAMBIOS} cambios más recientes. Para consultar más atrás, filtra por ID de registro.`}
                />
            )}

            <div className="tarjeta-borde">
                <Table
                    className="tabla-panel"
                    columns={columnas}
                    dataSource={filtradas}
                    rowKey="id"
                    loading={isPending}
                    scroll={{ x: 700 }}
                    expandable={{
                        expandedRowRender: (cambio) => <DetalleCambio cambio={cambio} />,
                        rowExpandable: (cambio) =>
                            Boolean(cambio.changed_fields || cambio.previous_values),
                    }}
                    pagination={{
                        pageSize: 15,
                        showSizeChanger: false,
                        showTotal: (total, [desde, hasta]) =>
                            `Mostrando ${desde}-${hasta} de ${total} cambios`,
                    }}
                    locale={{ emptyText: 'No hay cambios registrados que coincidan' }}
                />
            </div>
        </>
    )
}

export default AuditoriaPage

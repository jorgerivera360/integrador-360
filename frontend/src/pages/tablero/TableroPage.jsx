import { useMemo, useState } from 'react'
import { Alert, Button } from 'antd'
import { useDashboardStatus } from '@/hooks/useDashboard'
import { formatNumero, formatPorcentaje } from '@/utils/format'
import { etiquetaEstado } from '@/components/EstadoTag'
import FiltrosEjecuciones, { FILTROS_VACIOS, hayFiltros } from '@/components/FiltrosEjecuciones'
import { contiene } from '@/utils/texto'
import StatCard from './components/StatCard'
import MiniStat from './components/MiniStat'
import TablaRecientes from './components/TablaRecientes'
import {
    IconClientesActivos,
    IconFlujosActivos,
    IconEjecuciones24h,
    IconTasaExito,
} from './icons'
import './tablero.css'

const nombreCliente = (fila) => fila.client_name || fila.client_slug || '—'

function aplicarFiltros(filas, filtros) {
    const desde = filtros.rango?.[0]?.startOf('day').valueOf()
    const hasta = filtros.rango?.[1]?.endOf('day').valueOf()

    return filas.filter((fila) => {
        if (!contiene(nombreCliente(fila), filtros.cliente)) return false
        if (!contiene(fila.flow_name, filtros.flujo)) return false
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

function calcularContadores(ejecuciones) {
    return {
        total: ejecuciones.length,
        exitosas: ejecuciones.filter((e) => e.status === 'success').length,
        parciales: ejecuciones.filter((e) => e.status === 'partial').length,
        errores: ejecuciones.filter((e) => e.status === 'error').length,
        en_curso: ejecuciones.filter((e) => e.status === 'running').length,
    }
}

const TableroPage = () => {
    const { data, isPending, isError, error, refetch } = useDashboardStatus()
    const [filtros, setFiltros] = useState(FILTROS_VACIOS)

    const todasLasEjecuciones = data?.recent_executions || []

    const filtradas = useMemo(
        () => aplicarFiltros(todasLasEjecuciones, filtros),
        [todasLasEjecuciones, filtros]
    )

    const filtrando = hayFiltros(filtros)
    const contadores = useMemo(() => calcularContadores(filtradas), [filtradas])

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar el tablero"
                description={error?.response?.data?.detail || error?.message}
                action={
                    <Button size="small" onClick={() => refetch()}>
                        Reintentar
                    </Button>
                }
            />
        )
    }

    const clientes = data?.clients
    const flujos = data?.flows

    return (
        <div className="tablero">
            <div className="tablero__cabecera">
                <p className="tablero__periodo">
                    Resumen de actividad de las últimas 48 horas
                    {filtrando && (
                        <span className="tablero__filtro-activo">
                            {' '}— filtrado: {filtradas.length} de {todasLasEjecuciones.length} ejecuciones
                        </span>
                    )}
                </p>
                <FiltrosEjecuciones valor={filtros} onChange={setFiltros} mostrarFecha={false} />
            </div>

            <div className="tablero__grid-stats">
                <StatCard
                    icono={<IconClientesActivos />}
                    tono="azul"
                    etiqueta="Clientes Activos"
                    valor={formatNumero(clientes?.activos)}
                    cargando={isPending}
                />
                <StatCard
                    icono={<IconFlujosActivos />}
                    tono="indigo"
                    etiqueta="Flujos Activos"
                    valor={formatNumero(flujos?.activos)}
                    cargando={isPending}
                />
                <StatCard
                    icono={<IconEjecuciones24h />}
                    tono="morado"
                    etiqueta="Ejecuciones (48h)"
                    valor={formatNumero(contadores.total)}
                    cargando={isPending}
                />
                <StatCard
                    icono={<IconTasaExito />}
                    tono="verde"
                    etiqueta="Tasa de Éxito"
                    valor={formatPorcentaje(contadores.exitosas, contadores.total)}
                    valorVerde
                    cargando={isPending}
                />
            </div>

            <div className="tablero__grid-mini">
                <MiniStat
                    tono="verde"
                    etiqueta="Exitosas"
                    valor={formatNumero(contadores.exitosas)}
                    cargando={isPending}
                />
                <MiniStat
                    tono="naranja"
                    etiqueta="Parciales"
                    valor={formatNumero(contadores.parciales)}
                    cargando={isPending}
                />
                <MiniStat
                    tono="rojo"
                    etiqueta="Errores"
                    valor={formatNumero(contadores.errores)}
                    cargando={isPending}
                />
                <MiniStat
                    tono="azul"
                    etiqueta="En curso"
                    valor={formatNumero(contadores.en_curso)}
                    cargando={isPending}
                />
            </div>

            {!isPending && contadores.total === 0 && (
                <p className="tablero__sin-datos">
                    {filtrando
                        ? 'Ninguna ejecución coincide con los filtros.'
                        : 'Sin ejecuciones en las últimas 48 horas.'}
                </p>
            )}

            <TablaRecientes
                ejecuciones={filtradas}
                cargando={isPending}
            />
        </div>
    )
}

export default TableroPage

import { Alert, Button } from 'antd'
import { useDashboardStatus } from '@/hooks/useDashboard'
import { formatNumero, formatPorcentaje } from '@/utils/format'
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

const TableroPage = () => {
    const { data, isPending, isError, error, refetch } = useDashboardStatus()

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
    const ejecuciones = data?.executions_24h

    return (
        <div className="tablero">
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
                    etiqueta="Ejecuciones (24h)"
                    valor={formatNumero(ejecuciones?.total)}
                    cargando={isPending}
                />
                <StatCard
                    icono={<IconTasaExito />}
                    tono="verde"
                    etiqueta="Tasa de Éxito"
                    valor={formatPorcentaje(ejecuciones?.exitosas, ejecuciones?.total)}
                    valorVerde
                    cargando={isPending}
                />
            </div>

            <div className="tablero__grid-mini">
                <MiniStat
                    tono="verde"
                    etiqueta="Exitosas"
                    valor={formatNumero(ejecuciones?.exitosas)}
                    cargando={isPending}
                />
                <MiniStat
                    tono="naranja"
                    etiqueta="Parciales"
                    valor={formatNumero(ejecuciones?.parciales)}
                    cargando={isPending}
                />
                <MiniStat
                    tono="rojo"
                    etiqueta="Errores"
                    valor={formatNumero(ejecuciones?.errores)}
                    cargando={isPending}
                />
                <MiniStat
                    tono="azul"
                    etiqueta="En curso"
                    valor={formatNumero(ejecuciones?.en_curso)}
                    cargando={isPending}
                />
            </div>

            {!isPending && ejecuciones?.total === 0 && (
                <p className="tablero__sin-datos">
                    Sin ejecuciones en las últimas 24 horas. La tabla de abajo muestra el
                    historial completo, sin importar la fecha.
                </p>
            )}

            <TablaRecientes
                ejecuciones={data?.recent_executions}
                cargando={isPending}
            />
        </div>
    )
}

export default TableroPage

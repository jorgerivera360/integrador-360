import { Drawer } from 'antd'
import EstadoTag from '@/components/EstadoTag'
import { formatFechaHora, formatDuracion } from '@/utils/format'

const DISPARADO_LABEL = {
    scheduler: 'Scheduler',
    manual: 'Manual',
    api: 'API',
}

const DrawerEjecucion = ({ ejecucion, abierto, onCerrar }) => {
    if (!ejecucion) return null

    const resultado = ejecucion.result || {}
    const fallidos = resultado.fallidos || []
    const tieneError = Boolean(ejecucion.error_message)

    return (
        <Drawer
            title={
                <div className="drawer-titulo">
                    <span>Ejecucion #{ejecucion.id}</span>
                    <EstadoTag estado={ejecucion.status} />
                </div>
            }
            open={abierto}
            onClose={onCerrar}
            width={450}
            destroyOnClose
        >
            <div className="drawer-seccion">
                <h4 className="drawer-seccion__titulo">Informacion general</h4>
                <div className="drawer-grid">
                    <div className="drawer-campo">
                        <span className="drawer-campo__label">Fecha inicio</span>
                        <span className="drawer-campo__valor">{formatFechaHora(ejecucion.started_at)}</span>
                    </div>
                    <div className="drawer-campo">
                        <span className="drawer-campo__label">Fecha fin</span>
                        <span className="drawer-campo__valor">{formatFechaHora(ejecucion.finished_at)}</span>
                    </div>
                    <div className="drawer-campo">
                        <span className="drawer-campo__label">Duracion</span>
                        <span className="drawer-campo__valor">
                            {formatDuracion(ejecucion.started_at, ejecucion.finished_at)}
                        </span>
                    </div>
                    <div className="drawer-campo">
                        <span className="drawer-campo__label">Disparado por</span>
                        <span className="drawer-campo__valor">
                            {DISPARADO_LABEL[ejecucion.triggered_by] || ejecucion.triggered_by}
                        </span>
                    </div>
                    {ejecucion.triggered_user && (
                        <div className="drawer-campo">
                            <span className="drawer-campo__label">Usuario</span>
                            <span className="drawer-campo__valor">{ejecucion.triggered_user}</span>
                        </div>
                    )}
                </div>
            </div>

            <div className="drawer-seccion">
                <h4 className="drawer-seccion__titulo">Resultado</h4>
                <div className="drawer-grid">
                    <CampoResultado label="Total" valor={resultado.total} />
                    <CampoResultado label="Creados" valor={resultado.creados} />
                    <CampoResultado label="Actualizados" valor={resultado.actualizados} />
                    <CampoResultado label="Descartados" valor={resultado.descartados} />
                    <CampoResultado
                        label="Fallidos"
                        valor={resultado.fallidos?.length ?? resultado.fallidos_count ?? 0}
                        esError={(resultado.fallidos?.length ?? resultado.fallidos_count ?? 0) > 0}
                    />
                </div>
            </div>

            {fallidos.length > 0 && (
                <div className="drawer-seccion">
                    <h4 className="drawer-seccion__titulo">
                        Fallidos ({fallidos.length})
                    </h4>
                    <div className="drawer-fallidos">
                        {fallidos.map((item, i) => (
                            <div key={i} className="drawer-fallido">
                                <span className="drawer-fallido__ref">
                                    {item.referencia || item.identificacion || `#${i + 1}`}
                                </span>
                                <span className="drawer-fallido__razon">
                                    {item.razon || item.reason || 'Sin detalle'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {tieneError && (
                <div className="drawer-error">
                    <div className="drawer-error__titulo">Error</div>
                    <pre className="drawer-error__texto">{ejecucion.error_message}</pre>
                </div>
            )}
        </Drawer>
    )
}

const CampoResultado = ({ label, valor, esError }) => {
    const valorFinal = valor ?? 0
    return (
        <div className="drawer-campo">
            <span className="drawer-campo__label">{label}</span>
            <span className={`drawer-campo__valor ${esError ? 'drawer-campo__valor--error' : ''}`}>
                {valorFinal}
            </span>
        </div>
    )
}

export default DrawerEjecucion

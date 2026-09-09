import { Alert, App, Button, Popconfirm, Tag } from 'antd'
import { useProvisionarContenedor, useEliminarContenedor, useEstadoProvision, mensajeDeError } from '@/hooks/useClientes'

const ESTADOS = {
    running: { color: 'success', texto: 'Activa' },
    exited: { color: 'error', texto: 'Detenida' },
    restarting: { color: 'warning', texto: 'Reiniciando' },
    created: { color: 'default', texto: 'Creada' },
    paused: { color: 'warning', texto: 'Pausada' },
}

const IconAuto = (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" width={26} height={26} strokeWidth={1.6} {...props}>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 6v6l4 2" />
    </svg>
)

const ProvisionContenedor = ({ cliente }) => {
    const { message } = App.useApp()
    const provisionar = useProvisionarContenedor(cliente.id)
    const eliminarContenedor = useEliminarContenedor(cliente.id)
    const { data: estado, isLoading, refetch } = useEstadoProvision(cliente.id)

    const existe = estado?.exists === true
    const inCompose = estado?.in_compose === true
    const containerRunning = estado?.container_running === true
    const statusDocker = estado?.status
    const estiloEstado = ESTADOS[statusDocker] || { color: 'default', texto: statusDocker || 'Desconocido' }

    const handleProvisionar = async () => {
        try {
            const resultado = await provisionar.mutateAsync()
            if (resultado?.success) {
                message.success('Automatización activada')
                refetch()
            } else {
                message.error(resultado?.msg || 'Error al activar automatización')
            }
        } catch (err) {
            message.error(mensajeDeError(err))
        }
    }

    return (
        <div className="seccion" style={{ marginBottom: 0 }}>
            <div className="seccion__titulo">Automatización</div>
            <p className="seccion__sub">
                Activa la ejecución automática de los flujos programados para este cliente.
                Los flujos con cron configurado se ejecutarán según su programación.
            </p>
            <div className="seccion__linea" />

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20 }}>
                <div className="test__icono test__icono--azul">
                    <IconAuto stroke="#1677ff" />
                </div>
                <div style={{ flex: 1 }}>
                    {isLoading ? (
                        <Tag>Consultando...</Tag>
                    ) : existe ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                            {statusDocker && <Tag color={estiloEstado.color}>{estiloEstado.texto}</Tag>}
                            {inCompose && !containerRunning && !statusDocker && (
                                <Tag color="warning">Configurada sin iniciar</Tag>
                            )}
                        </div>
                    ) : (
                        <div>
                            <Tag color="default">No activada</Tag>
                            <p style={{ margin: '12px 0 0', fontSize: 13, color: '#8b93a1' }}>
                                La automatización no está activada. Al activarla, los flujos
                                con cron configurado comenzarán a ejecutarse automáticamente.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {provisionar.isError && (
                <Alert
                    type="error"
                    showIcon
                    style={{ marginTop: 16 }}
                    message={mensajeDeError(provisionar.error)}
                />
            )}

            <div style={{ marginTop: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    {!existe && (
                        <Button
                            type="primary"
                            loading={provisionar.isPending}
                            onClick={handleProvisionar}
                        >
                            Activar automatización
                        </Button>
                    )}

                    {existe && (
                        <Popconfirm
                            title="Desactivar automatización"
                            description="Se detendrá la ejecución automática de los flujos. El cliente y sus flujos no se borran."
                            onConfirm={async () => {
                                try {
                                    const r = await eliminarContenedor.mutateAsync()
                                    if (r?.success) {
                                        message.success('Automatización desactivada')
                                        refetch()
                                    } else {
                                        message.error(r?.msg || 'No se pudo desactivar')
                                    }
                                } catch (err) {
                                    message.error(mensajeDeError(err))
                                }
                            }}
                            okText="Desactivar"
                            okButtonProps={{ danger: true }}
                            cancelText="Cancelar"
                        >
                            <Button danger loading={eliminarContenedor.isPending}>
                                Desactivar automatización
                            </Button>
                        </Popconfirm>
                    )}
                </div>

                {existe && statusDocker === 'running' && (
                    <Alert
                        type="success"
                        showIcon
                        style={{ marginTop: 12 }}
                        message="La automatización está activa. Los flujos programados se ejecutan según su cron."
                    />
                )}

                {existe && statusDocker && statusDocker !== 'running' && (
                    <Alert
                        type="warning"
                        showIcon
                        style={{ marginTop: 12 }}
                        message={`La automatización está en estado "${estiloEstado.texto}". Revisa los logs en el servidor.`}
                    />
                )}

                {inCompose && !containerRunning && !statusDocker && (
                    <Alert
                        type="info"
                        showIcon
                        style={{ marginTop: 12 }}
                        message="La automatización está configurada pero no se ha iniciado. Desactívala y vuelve a activar."
                    />
                )}
            </div>
        </div>
    )
}

export default ProvisionContenedor

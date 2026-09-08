import { Alert, App, Button, Popconfirm, Tag } from 'antd'
import { useProvisionarContenedor, useEliminarContenedor, useEstadoProvision, mensajeDeError } from '@/hooks/useClientes'

const ESTADOS_CONTENEDOR = {
    running: { color: 'success', texto: 'Corriendo' },
    exited: { color: 'error', texto: 'Detenido' },
    restarting: { color: 'warning', texto: 'Reiniciando' },
    created: { color: 'default', texto: 'Creado' },
    paused: { color: 'warning', texto: 'Pausado' },
}

const IconContenedor = (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" width={26} height={26} strokeWidth={1.6} {...props}>
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <path d="M3 9h18M9 3v18" />
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
    const estiloEstado = ESTADOS_CONTENEDOR[statusDocker] || { color: 'default', texto: statusDocker || 'Desconocido' }
    const containerName = estado?.container || `integrador-${cliente.client_id}`

    const handleProvisionar = async () => {
        try {
            const resultado = await provisionar.mutateAsync()
            if (resultado?.success) {
                message.success(resultado.msg)
                refetch()
            } else {
                message.error(resultado?.msg || 'Error al provisionar')
            }
        } catch (err) {
            message.error(mensajeDeError(err))
        }
    }

    return (
        <div className="seccion" style={{ marginBottom: 0 }}>
            <div className="seccion__titulo">Contenedor Docker</div>
            <p className="seccion__sub">
                Cada cliente corre en su propio contenedor. Aquí puedes provisionar
                uno nuevo o verificar el estado del existente.
            </p>
            <div className="seccion__linea" />

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20 }}>
                <div className="test__icono test__icono--azul">
                    <IconContenedor stroke="#1677ff" />
                </div>
                <div style={{ flex: 1 }}>
                    <div style={{ marginBottom: 8 }}>
                        <span style={{ fontFamily: "'Fira Code', Consolas, monospace", fontSize: 14, color: '#1a1a2e' }}>
                            {containerName}
                        </span>
                    </div>

                    {isLoading ? (
                        <Tag>Consultando...</Tag>
                    ) : existe ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                            {containerRunning && <Tag color={estiloEstado.color}>{estiloEstado.texto}</Tag>}
                            {!containerRunning && statusDocker && <Tag color={estiloEstado.color}>{estiloEstado.texto}</Tag>}
                            {inCompose && <Tag color="blue">En docker-compose</Tag>}
                            {!containerRunning && !statusDocker && inCompose && (
                                <Tag color="warning">Sin iniciar</Tag>
                            )}
                        </div>
                    ) : (
                        <div>
                            <Tag color="default">No provisionado</Tag>
                            <p style={{ margin: '12px 0 0', fontSize: 13, color: '#8b93a1' }}>
                                El contenedor aún no existe. Al provisionarlo se agregará
                                a docker-compose.yml y se levantará automáticamente.
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
                            Provisionar contenedor
                        </Button>
                    )}

                    {existe && (
                        <Popconfirm
                            title="Eliminar contenedor"
                            description="Se detendrá el contenedor y se quitará de docker-compose.yml. El cliente y sus flujos no se borran."
                            onConfirm={async () => {
                                try {
                                    const r = await eliminarContenedor.mutateAsync()
                                    if (r?.success) {
                                        message.success(r.msg)
                                        refetch()
                                    } else {
                                        message.error(r?.msg || 'No se pudo eliminar')
                                    }
                                } catch (err) {
                                    message.error(mensajeDeError(err))
                                }
                            }}
                            okText="Eliminar"
                            okButtonProps={{ danger: true }}
                            cancelText="Cancelar"
                        >
                            <Button danger loading={eliminarContenedor.isPending}>
                                Eliminar contenedor
                            </Button>
                        </Popconfirm>
                    )}
                </div>

                {existe && statusDocker !== 'running' && (
                    <Alert
                        type="warning"
                        showIcon
                        style={{ marginTop: 12 }}
                        message={`El contenedor existe pero está en estado "${statusDocker}". Revisa los logs en el servidor.`}
                    />
                )}

                {existe && statusDocker === 'running' && (
                    <Alert
                        type="success"
                        showIcon
                        style={{ marginTop: 12 }}
                        message="El contenedor está corriendo correctamente"
                    />
                )}
            </div>
        </div>
    )
}

export default ProvisionContenedor

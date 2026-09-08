import { Alert, App, Button, Tag } from 'antd'
import { useProvisionarContenedor, useEstadoProvision, mensajeDeError } from '@/hooks/useClientes'

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
    const { data: estado, isLoading, refetch } = useEstadoProvision(cliente.id)

    const existe = estado?.exists === true
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
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <Tag color={estiloEstado.color}>{estiloEstado.texto}</Tag>
                            <span style={{ fontSize: 13, color: '#8b93a1' }}>
                                El contenedor ya está provisionado
                            </span>
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
                {!existe && (
                    <Button
                        type="primary"
                        loading={provisionar.isPending}
                        onClick={handleProvisionar}
                    >
                        Provisionar contenedor
                    </Button>
                )}

                {existe && statusDocker !== 'running' && (
                    <Alert
                        type="warning"
                        showIcon
                        style={{ marginTop: 8 }}
                        message={`El contenedor existe pero está en estado "${statusDocker}". Revisa los logs en el servidor.`}
                    />
                )}

                {existe && statusDocker === 'running' && (
                    <Alert
                        type="success"
                        showIcon
                        message="El contenedor está corriendo correctamente"
                    />
                )}
            </div>
        </div>
    )
}

export default ProvisionContenedor

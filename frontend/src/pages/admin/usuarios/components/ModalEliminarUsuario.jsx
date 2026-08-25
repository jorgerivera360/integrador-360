import { useEffect } from 'react'
import { Alert, Modal } from 'antd'
import RolBadge from '@/components/RolBadge'
import { useEliminarUsuario } from '@/hooks/useUsuarios'
import { mensajeDeError } from '@/hooks/useClientes'
import { IconAdvertencia } from '../icons'

/**
 * Confirmación de borrado de usuario.
 *
 * Más liviana que la de clientes: aquí no hay cascada de datos, solo se
 * pierde el acceso al panel. Por eso no se pide escribir nada.
 */
const ModalEliminarUsuario = ({ abierto, usuario, onCerrar, onEliminado }) => {
    const eliminar = useEliminarUsuario()
    const { reset } = eliminar // referencia estable; el objeto cambia en cada render

    useEffect(() => {
        if (abierto) reset()
    }, [abierto, reset])

    const confirmar = async () => {
        await eliminar.mutateAsync(usuario.id)
        onEliminado?.(usuario)
        onCerrar()
    }

    return (
        <Modal
            open={abierto}
            onCancel={onCerrar}
            onOk={confirmar}
            okText="Eliminar usuario"
            cancelText="Cancelar"
            okButtonProps={{ danger: true }}
            confirmLoading={eliminar.isPending}
            width={440}
            destroyOnClose
            title={
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <IconAdvertencia width={20} height={20} style={{ color: '#cf1322' }} />
                    ¿Eliminar usuario?
                </span>
            }
        >
            <p style={{ fontSize: 13.5, color: 'rgba(0,0,0,.55)', margin: 0 }}>
                Se eliminará permanentemente a:
            </p>

            <div className="borrar-usuario__card">
                <div className="borrar-usuario__nombre">{usuario?.name}</div>
                <div className="borrar-usuario__email">{usuario?.email}</div>
                <RolBadge rol={usuario?.role} />
            </div>

            <p style={{ fontSize: 13.5, color: 'rgba(0,0,0,.55)', margin: 0, lineHeight: 1.5 }}>
                El usuario no podrá volver a ingresar al panel. Esta acción no se puede deshacer.
            </p>

            {eliminar.isError && (
                <Alert
                    type="error"
                    showIcon
                    style={{ marginTop: 16 }}
                    message={mensajeDeError(eliminar.error)}
                />
            )}
        </Modal>
    )
}

export default ModalEliminarUsuario

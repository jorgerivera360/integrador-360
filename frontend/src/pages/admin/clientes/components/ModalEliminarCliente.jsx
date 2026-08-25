import { useEffect, useState } from 'react'
import { Alert, Input, Modal } from 'antd'
import { useEliminarCliente, mensajeDeError } from '@/hooks/useClientes'
import { IconAdvertencia } from '../icons'

const EN_CASCADA = [
    'Todos los flujos configurados del cliente',
    'Todo el historial de ejecuciones',
    'Los registros de auditoría asociados',
]

/**
 * Confirmación de borrado.
 *
 * El DELETE de la API borra en cascada por las FK de flows y executions,
 * y no hay deshacer: por eso se exige escribir el client_id, igual que
 * hace GitHub para borrar un repositorio.
 */
const ModalEliminarCliente = ({ abierto, cliente, onCerrar, onEliminado }) => {
    const [confirmacion, setConfirmacion] = useState('')
    const eliminar = useEliminarCliente()
    const { reset } = eliminar // referencia estable; el objeto cambia en cada render

    useEffect(() => {
        if (abierto) {
            setConfirmacion('')
            reset()
        }
    }, [abierto, reset])

    const puedeEliminar = confirmacion.trim() === cliente?.client_id

    const confirmar = async () => {
        await eliminar.mutateAsync(cliente.id)
        onEliminado?.(cliente)
        onCerrar()
    }

    return (
        <Modal
            open={abierto}
            onCancel={onCerrar}
            onOk={confirmar}
            okText="Eliminar permanentemente"
            cancelText="Cancelar"
            okButtonProps={{ danger: true, disabled: !puedeEliminar }}
            confirmLoading={eliminar.isPending}
            width={480}
            title={
                <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <IconAdvertencia width={20} height={20} style={{ color: '#cf1322' }} />
                    ¿Eliminar cliente {cliente?.name}?
                </span>
            }
            destroyOnClose
        >
            <p style={{ fontSize: 13.5, color: 'rgba(0,0,0,.55)', margin: 0 }}>
                Esta acción es irreversible. Se eliminarán permanentemente:
            </p>

            <div className="borrar__cascada">
                {EN_CASCADA.map((texto) => (
                    <div className="borrar__item" key={texto}>
                        <span aria-hidden="true">✕</span>
                        {texto}
                    </div>
                ))}
            </div>

            <p className="borrar__aviso">
                Las credenciales en GCP Secret Manager y el contenedor Docker NO se eliminan
                automáticamente.
            </p>

            <label className="campo-label" htmlFor="confirmar-borrado">
                Escribe el ID del cliente para confirmar
            </label>
            <Input
                id="confirmar-borrado"
                className="campo-mono"
                style={{ marginTop: 8 }}
                placeholder={cliente?.client_id}
                value={confirmacion}
                onChange={(evento) => setConfirmacion(evento.target.value)}
                onPressEnter={() => puedeEliminar && confirmar()}
                autoComplete="off"
            />

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

export default ModalEliminarCliente

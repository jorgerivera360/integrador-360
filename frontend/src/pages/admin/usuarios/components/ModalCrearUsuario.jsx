import { useEffect } from 'react'
import { Alert, Form, Input, Modal, Select } from 'antd'
import RolBadge from '@/components/RolBadge'
import { DOMINIO_CORPORATIVO, OPCIONES_ROL, ROLES, ROLES_INFO } from '@/config/roles'
import { useCrearUsuario } from '@/hooks/useUsuarios'
import { mensajeDeError } from '@/hooks/useClientes'

/**
 * Alta de usuario.
 *
 * No lleva switch de estado: POST /users/ no acepta `is_active` y siempre
 * crea activo. Desactivar se hace desde el detalle.
 */
const ModalCrearUsuario = ({ abierto, onCerrar, onCreado }) => {
    const [form] = Form.useForm()
    const crear = useCrearUsuario()
    const { reset } = crear // referencia estable; el objeto cambia en cada render

    // Se observa el Select para pintar la insignia y su descripción.
    const rolElegido = Form.useWatch('role', form)
    const info = ROLES_INFO[rolElegido]

    useEffect(() => {
        if (!abierto) return
        reset()
        form.setFieldsValue({ email: '', name: '', role: ROLES.VIEWER })
    }, [abierto, form, reset])

    const enviar = async () => {
        const valores = await form.validateFields()
        const { data } = await crear.mutateAsync({
            email: valores.email.trim(),
            name: valores.name.trim(),
            role: valores.role,
        })
        onCreado?.(data)
        onCerrar()
    }

    return (
        <Modal
            open={abierto}
            onCancel={onCerrar}
            onOk={enviar}
            okText="Crear usuario"
            cancelText="Cancelar"
            confirmLoading={crear.isPending}
            width={480}
            destroyOnClose
            title={
                <div>
                    <div>Nuevo usuario</div>
                    <div style={{ fontSize: 13, fontWeight: 400, color: '#8b93a1', marginTop: 4 }}>
                        Podrá ingresar al panel con su cuenta de Google ({DOMINIO_CORPORATIVO})
                    </div>
                </div>
            }
        >
            <Form form={form} layout="vertical" onFinish={enviar} style={{ marginTop: 8 }}>
                <Form.Item
                    name="email"
                    label={<span className="campo-label">Correo electrónico</span>}
                    rules={[
                        { required: true, message: 'El correo es obligatorio' },
                        { type: 'email', message: 'No parece un correo válido' },
                        {
                            // /auth/login rechaza cualquier otro dominio, así que un
                            // usuario fuera de él nunca podría entrar.
                            validator: (_, valor) =>
                                !valor || valor.trim().toLowerCase().endsWith(DOMINIO_CORPORATIVO)
                                    ? Promise.resolve()
                                    : Promise.reject(
                                          new Error(`El correo debe terminar en ${DOMINIO_CORPORATIVO}`)
                                      ),
                        },
                    ]}
                >
                    <Input placeholder={`nombre${DOMINIO_CORPORATIVO}`} autoComplete="off" />
                </Form.Item>

                <Form.Item
                    name="name"
                    label={<span className="campo-label">Nombre completo</span>}
                    rules={[{ required: true, message: 'El nombre es obligatorio' }]}
                >
                    <Input placeholder="ej: Ana López" autoComplete="off" />
                </Form.Item>

                <Form.Item
                    name="role"
                    label={<span className="campo-label">Rol</span>}
                    rules={[{ required: true, message: 'Elige un rol' }]}
                    style={{ marginBottom: info ? 0 : 24 }}
                >
                    <Select options={OPCIONES_ROL} />
                </Form.Item>

                {info && (
                    <div className="rol-info" style={{ marginBottom: 24 }}>
                        <RolBadge rol={rolElegido} />
                        <span className="rol-info__desc">{info.descripcion}</span>
                    </div>
                )}
            </Form>

            <Alert
                type="info"
                showIcon
                message="Los nuevos usuarios se crean activos. Para desactivar uno sin eliminarlo, entra a su detalle."
            />

            {crear.isError && (
                <Alert
                    type="error"
                    showIcon
                    style={{ marginTop: 16 }}
                    message={mensajeDeError(crear.error)}
                />
            )}
        </Modal>
    )
}

export default ModalCrearUsuario

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, App, Button, Form, Input, Select, Skeleton, Switch, Tooltip } from 'antd'
import MetaSistema from '@/components/MetaSistema'
import RolBadge from '@/components/RolBadge'
import useAuthStore from '@/store/authStore'
import { useUsuario, useActualizarUsuario } from '@/hooks/useUsuarios'
import { mensajeDeError } from '@/hooks/useClientes'
import { useSetBreadcrumb } from '@/layouts/BreadcrumbContext'
import { DOMINIO_CORPORATIVO, OPCIONES_ROL, ROLES_INFO } from '@/config/roles'
import { formatDesde, formatFecha, formatFechaHora } from '@/utils/format'
import ModalEliminarUsuario from './components/ModalEliminarUsuario'
import { IconPapelera } from './icons'
import '@/styles/pagina.css'
import '@/pages/admin/clientes/clientes.css'
import './usuarios.css'

const AYUDA_ESTADO =
    'Los usuarios inactivos no pueden ingresar al panel aunque tengan cuenta de Google.'

const UsuarioDetallePage = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const { message, modal } = App.useApp()
    const [form] = Form.useForm()

    const usuarioActual = useAuthStore((estado) => estado.user)
    const { data: usuario, isPending, isError, error, refetch } = useUsuario(id)
    const actualizar = useActualizarUsuario()

    const [modalBorrar, setModalBorrar] = useState(false)

    // Se observa el Select para que la descripción del rol acompañe al cambio.
    const rolElegido = Form.useWatch('role', form)
    const info = ROLES_INFO[rolElegido]

    useSetBreadcrumb(usuario?.name)

    useEffect(() => {
        if (usuario) form.setFieldsValue(usuario)
    }, [usuario, form])

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar el usuario"
                description={mensajeDeError(error)}
                action={
                    <Button size="small" onClick={() => refetch()}>
                        Reintentar
                    </Button>
                }
            />
        )
    }

    if (isPending || !usuario) {
        return <Skeleton active paragraph={{ rows: 8 }} />
    }

    // La API lo rechaza con 400 (users.py:116); aquí se avisa antes.
    const esUnoMismo = usuario.id === usuarioActual?.id

    const guardar = async () => {
        const valores = await form.validateFields()
        await actualizar.mutateAsync({
            id: usuario.id,
            datos: {
                email: valores.email.trim(),
                name: valores.name.trim(),
                role: valores.role,
                is_active: valores.is_active,
            },
        })
        message.success('Cambios guardados')
    }

    const cancelar = () => {
        if (!form.isFieldsTouched()) {
            navigate('/admin/usuarios')
            return
        }

        modal.confirm({
            title: '¿Descartar los cambios?',
            content: 'Los cambios que hiciste en este usuario no se guardarán.',
            okText: 'Descartar',
            okButtonProps: { danger: true },
            cancelText: 'Seguir editando',
            onOk: () => navigate('/admin/usuarios'),
        })
    }

    return (
        <>
            <div className="cliente-head">
                <div>
                    <div className="cliente-head__linea">
                        <h1 className="cliente-head__nombre">{usuario.name}</h1>
                        <RolBadge rol={usuario.role} />
                        <span
                            className={`estado-punto estado-punto--${usuario.is_active ? 'activo' : 'inactivo'}`}
                        >
                            <span className="estado-punto__marca" />
                            {usuario.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                    </div>
                    <p className="cliente-head__meta">
                        {usuario.email} · Último acceso: {formatDesde(usuario.last_login)} ·
                        Creado: {formatFecha(usuario.created_at)}
                    </p>
                </div>

                <Tooltip title={esUnoMismo ? 'No puedes eliminarte a ti mismo' : undefined}>
                    {/* El span deja que el tooltip funcione con el botón deshabilitado */}
                    <span>
                        <Button
                            danger
                            icon={<IconPapelera />}
                            disabled={esUnoMismo}
                            onClick={() => setModalBorrar(true)}
                        >
                            Eliminar usuario
                        </Button>
                    </span>
                </Tooltip>
            </div>

            <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
                <div className="seccion">
                    <div className="seccion__titulo">Datos del usuario</div>
                    <div className="seccion__linea" />

                    <div className="grid-2">
                        <div className="columna">
                            <Form.Item
                                name="email"
                                label={<span className="campo-label">Correo electrónico</span>}
                                rules={[
                                    { required: true, message: 'El correo es obligatorio' },
                                    { type: 'email', message: 'No parece un correo válido' },
                                    {
                                        validator: (_, valor) =>
                                            !valor ||
                                            valor.trim().toLowerCase().endsWith(DOMINIO_CORPORATIVO)
                                                ? Promise.resolve()
                                                : Promise.reject(
                                                      new Error(
                                                          `El correo debe terminar en ${DOMINIO_CORPORATIVO}`
                                                      )
                                                  ),
                                    },
                                ]}
                                style={{ marginBottom: 0 }}
                            >
                                <Input className="campo-ancho" autoComplete="off" />
                            </Form.Item>

                            <Form.Item
                                name="name"
                                label={<span className="campo-label">Nombre completo</span>}
                                rules={[{ required: true, message: 'El nombre es obligatorio' }]}
                                style={{ marginBottom: 0 }}
                            >
                                <Input className="campo-ancho" autoComplete="off" />
                            </Form.Item>
                        </div>

                        <div className="columna">
                            <div>
                                <Form.Item
                                    name="role"
                                    label={<span className="campo-label">Rol</span>}
                                    rules={[{ required: true, message: 'Elige un rol' }]}
                                    style={{ marginBottom: 0 }}
                                >
                                    <Select className="campo-ancho" options={OPCIONES_ROL} />
                                </Form.Item>

                                {info && (
                                    <div className="rol-info">
                                        <RolBadge rol={rolElegido} />
                                        <span className="rol-info__desc">{info.descripcion}</span>
                                    </div>
                                )}
                            </div>

                            <Form.Item
                                name="is_active"
                                label={<span className="campo-label">Estado del usuario</span>}
                                valuePropName="checked"
                                extra={AYUDA_ESTADO}
                                style={{ marginBottom: 0 }}
                            >
                                <Switch checkedChildren="Activo" unCheckedChildren="Inactivo" />
                            </Form.Item>
                        </div>
                    </div>

                    <MetaSistema
                        items={[
                            { label: 'Creado', valor: formatFechaHora(usuario.created_at) },
                            { label: 'Actualizado', valor: formatFechaHora(usuario.updated_at) },
                            {
                                label: 'Último acceso',
                                valor: usuario.last_login
                                    ? formatFechaHora(usuario.last_login)
                                    : 'Nunca',
                            },
                            { label: 'ID interno', valor: usuario.id },
                        ]}
                    />
                </div>
            </Form>

            {actualizar.isError && (
                <Alert
                    type="error"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message={mensajeDeError(actualizar.error)}
                />
            )}

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Button type="primary" loading={actualizar.isPending} onClick={guardar}>
                    Guardar cambios
                </Button>
                <Button onClick={cancelar}>Cancelar</Button>
            </div>

            <ModalEliminarUsuario
                abierto={modalBorrar}
                usuario={usuario}
                onCerrar={() => setModalBorrar(false)}
                onEliminado={(borrado) => {
                    message.success(`Usuario "${borrado.name}" eliminado`)
                    navigate('/admin/usuarios', { replace: true })
                }}
            />
        </>
    )
}

export default UsuarioDetallePage

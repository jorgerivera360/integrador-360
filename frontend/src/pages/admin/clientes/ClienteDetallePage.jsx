import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, App, Button, Form, Input, Select, Skeleton, Switch, Tabs, Tooltip } from 'antd'
import ActivoTag from '@/components/ActivoTag'
import ErpTag from '@/components/ErpTag'
import MetaSistema from '@/components/MetaSistema'
import useHasRole from '@/hooks/useHasRole'
import { useCliente, useActualizarCliente, mensajeDeError } from '@/hooks/useClientes'
import { useSetBreadcrumb } from '@/layouts/BreadcrumbContext'
import { OPCIONES_ERP } from '@/config/erp'
import { ROLES } from '@/config/navigation'
import { formatFecha, formatFechaHora } from '@/utils/format'
import ModalEliminarCliente from './components/ModalEliminarCliente'
import TestConexiones from './components/TestConexiones'
import { IconAdvertencia, IconInfo, IconPapelera } from './icons'
import '@/styles/pagina.css'
import './clientes.css'

const AYUDA_ID =
    'Identificador interno del cliente, distinto del nombre visible. Debe coincidir ' +
    'con el nombre del secret en GCP (integrador-{id}) y con la variable CLIENT_ID ' +
    'del contenedor Docker.'

const AYUDA_ERP =
    'Determina qué conector y transformador usa el integrador para este cliente. ' +
    'Cambiarlo afecta a todos sus flujos.'

const AYUDA_ESTADO =
    'Los clientes inactivos no pueden ejecutar flujos ni recibir ejecuciones manuales desde la API.'

/** Etiqueta con ícono de ayuda al lado. */
const Etiqueta = ({ children, ayuda, alerta }) => (
    <span className="campo-label">
        {children}
        {ayuda && (
            <Tooltip title={ayuda}>
                <span style={{ cursor: 'help', display: 'inline-flex' }}>
                    <IconInfo width={15} height={15} style={{ color: '#bfbfbf' }} />
                </span>
            </Tooltip>
        )}
        {alerta && (
            <Tooltip title={alerta}>
                <span style={{ cursor: 'help', display: 'inline-flex' }}>
                    <IconAdvertencia style={{ color: '#faad14' }} />
                </span>
            </Tooltip>
        )}
    </span>
)

const ClienteDetallePage = () => {
    const { id } = useParams()
    const navigate = useNavigate()
    const { message, modal } = App.useApp()
    const [form] = Form.useForm()

    const puedeEditar = useHasRole([ROLES.SUPERADMIN, ROLES.ADMIN])
    const puedeEliminar = useHasRole([ROLES.SUPERADMIN])

    const { data: cliente, isPending, isError, error, refetch } = useCliente(id)
    const actualizar = useActualizarCliente(id)

    const [modalBorrar, setModalBorrar] = useState(false)

    useSetBreadcrumb(cliente?.name)

    // Los valores del servidor mandan: al recargar o guardar, el formulario
    // vuelve a reflejar lo que hay en BD.
    useEffect(() => {
        if (cliente) form.setFieldsValue(cliente)
    }, [cliente, form])

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar el cliente"
                description={mensajeDeError(error)}
                action={
                    <Button size="small" onClick={() => refetch()}>
                        Reintentar
                    </Button>
                }
            />
        )
    }

    if (isPending || !cliente) {
        return <Skeleton active paragraph={{ rows: 8 }} />
    }

    const guardar = async () => {
        const valores = await form.validateFields()
        await actualizar.mutateAsync({
            client_id: valores.client_id.trim(),
            name: valores.name.trim(),
            erp_type: valores.erp_type,
            is_active: valores.is_active,
        })
        message.success('Cambios guardados')
    }

    /**
     * Cancelar vuelve al listado. Si hay ediciones sin guardar se pide
     * confirmación: salir en silencio y perderlas sería peor que preguntar.
     */
    const cancelar = () => {
        if (!form.isFieldsTouched()) {
            navigate('/admin/clientes')
            return
        }

        modal.confirm({
            title: '¿Descartar los cambios?',
            content: 'Los cambios que hiciste en este cliente no se guardarán.',
            okText: 'Descartar',
            okButtonProps: { danger: true },
            cancelText: 'Seguir editando',
            onOk: () => navigate('/admin/clientes'),
        })
    }

    const pestanaInformacion = (
        <>
            <Form form={form} layout="vertical" initialValues={cliente} disabled={!puedeEditar}>
                <div className="seccion">
                    <div className="seccion__titulo">Datos del cliente</div>
                    <div className="seccion__linea" />

                    <div className="grid-2">
                        <div className="columna">
                            <Form.Item
                                name="client_id"
                                label={
                                    <Etiqueta
                                        ayuda={AYUDA_ID}
                                        alerta="Cambiarlo rompe la correspondencia con el secret de GCP y con el CLIENT_ID del contenedor, que hay que renombrar a mano."
                                    >
                                        ID del cliente
                                    </Etiqueta>
                                }
                                rules={[
                                    { required: true, message: 'El ID es obligatorio' },
                                    {
                                        pattern: /^[a-z0-9_-]+$/,
                                        message: 'Solo minúsculas, números, guion y guion bajo',
                                    },
                                ]}
                                style={{ marginBottom: 0 }}
                            >
                                <Input className="campo-mono campo-ancho" autoComplete="off" />
                            </Form.Item>

                            <Form.Item
                                name="name"
                                label={<Etiqueta>Nombre del cliente</Etiqueta>}
                                rules={[{ required: true, message: 'El nombre es obligatorio' }]}
                                style={{ marginBottom: 0 }}
                            >
                                <Input className="campo-ancho" autoComplete="off" />
                            </Form.Item>

                            <Form.Item
                                name="erp_type"
                                label={<Etiqueta ayuda={AYUDA_ERP}>ERP conectado</Etiqueta>}
                                rules={[{ required: true, message: 'Elige un tipo de ERP' }]}
                                style={{ marginBottom: 0 }}
                            >
                                <Select className="campo-ancho" options={OPCIONES_ERP} />
                            </Form.Item>
                        </div>

                        <div className="columna">
                            <Form.Item
                                name="is_active"
                                label={<Etiqueta ayuda={AYUDA_ESTADO}>Estado del cliente</Etiqueta>}
                                valuePropName="checked"
                                style={{ marginBottom: 0 }}
                            >
                                <Switch checkedChildren="Activo" unCheckedChildren="Inactivo" />
                            </Form.Item>
                        </div>
                    </div>

                    <MetaSistema
                        items={[
                            { label: 'Creado', valor: formatFechaHora(cliente.created_at) },
                            { label: 'Actualizado', valor: formatFechaHora(cliente.updated_at) },
                            { label: 'Creado por', valor: cliente.created_by },
                            { label: 'Actualizado por', valor: cliente.updated_by },
                            { label: 'ID interno', valor: cliente.id },
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

            {puedeEditar && (
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <Button type="primary" loading={actualizar.isPending} onClick={guardar}>
                        Guardar cambios
                    </Button>
                    <Button onClick={cancelar}>Cancelar</Button>
                </div>
            )}
        </>
    )

    return (
        <>
            <div className="cliente-head">
                <div>
                    <div className="cliente-head__linea">
                        <h1 className="cliente-head__nombre">{cliente.name}</h1>
                        <ErpTag erpType={cliente.erp_type} />
                        <ActivoTag activo={cliente.is_active} />
                    </div>
                    <p className="cliente-head__meta">
                        ID: {cliente.client_id} · Creado: {formatFecha(cliente.created_at)} ·
                        Última actualización: {formatFecha(cliente.updated_at)}
                    </p>
                </div>

                {puedeEliminar && (
                    <Button danger icon={<IconPapelera />} onClick={() => setModalBorrar(true)}>
                        Eliminar cliente
                    </Button>
                )}
            </div>

            <Tabs
                defaultActiveKey="info"
                style={{ marginTop: 8 }}
                items={[
                    { key: 'info', label: 'Información', children: pestanaInformacion },
                    {
                        key: 'test',
                        label: 'Test de conexiones',
                        children: <TestConexiones cliente={cliente} />,
                    },
                ]}
            />

            <ModalEliminarCliente
                abierto={modalBorrar}
                cliente={cliente}
                onCerrar={() => setModalBorrar(false)}
                onEliminado={(borrado) => {
                    message.success(`Cliente "${borrado.name}" eliminado`)
                    navigate('/admin/clientes', { replace: true })
                }}
            />
        </>
    )
}

export default ClienteDetallePage

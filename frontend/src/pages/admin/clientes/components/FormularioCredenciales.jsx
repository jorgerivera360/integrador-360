import { useEffect, useState } from 'react'
import { Alert, App, Button, Form, Input, Popconfirm } from 'antd'
import { etiquetaErp } from '@/config/erp'
import {
    useProbarConexionConCredenciales,
    useGuardarCredenciales,
    useEliminarCredenciales,
    useEstadoCredenciales,
    useCredenciales,
    mensajeDeError,
} from '@/hooks/useClientes'
import { IconCheck, IconEquis, IconServidor, IconNube, IconPapelera } from '../icons'

// --- Campos ERP por tipo ---

const CAMPOS_WS = [
    { name: 'url', label: 'URL del Web Service', required: true },
    { name: 'conexion', label: 'Nombre de conexión', required: true },
    { name: 'compania', label: 'Compañía', required: true },
    { name: 'usuario', label: 'Usuario', required: true },
    { name: 'clave', label: 'Clave', required: true, password: true },
    { name: 'proveedor', label: 'Proveedor', required: true },
    { name: 'proxy_host', label: 'Proxy Host', required: false },
    { name: 'proxy_port', label: 'Proxy Port', required: false },
]

const CAMPOS_CONNEKTA = [
    { name: 'url', label: 'URL', required: true },
    { name: 'urlqa', label: 'URL QA', required: false },
    { name: 'idcompania', label: 'Compañía', required: true },
    { name: 'connikey', label: 'ConniKey', required: true },
    { name: 'connitoken', label: 'ConniToken', required: true, password: true },
]

const CAMPOS_SAP = [
    { name: 'url', label: 'URL Service Layer', required: true },
    { name: 'compania', label: 'Compañía (base de datos)', required: true },
    { name: 'usuario', label: 'Usuario', required: true },
    { name: 'clave', label: 'Clave', required: true, password: true },
]

const CAMPOS_WMS = [
    { name: 'url', label: 'URL del WMS', required: true },
    { name: 'database', label: 'Base de datos', required: true },
    { name: 'usuario', label: 'Usuario', required: true },
    { name: 'clave', label: 'Clave', required: true, password: true },
]

const CAMPOS_ERP = {
    ws: CAMPOS_WS,
    connekta: CAMPOS_CONNEKTA,
    sap: CAMPOS_SAP,
}

// --- Resultado de test ---

const ResultadoTest = ({ resultado, error }) => {
    const fallo = Boolean(error)
    const exito = !fallo && resultado?.success === true
    const hayResultado = fallo || Boolean(resultado)

    if (!hayResultado) return null

    const detalle = fallo ? mensajeDeError(error) : resultado?.msg

    return (
        <div className={`resultado resultado--${exito ? 'ok' : 'error'}`}>
            <div className="resultado__head">
                {exito ? <IconCheck /> : <IconEquis />}
                {exito ? 'Conexión exitosa' : 'Conexión fallida'}
            </div>
            <div className="resultado__cuerpo">
                <div className="resultado__detalle">{detalle}</div>
            </div>
        </div>
    )
}

// --- Componente principal ---

const FormularioCredenciales = ({ cliente }) => {
    const { message } = App.useApp()
    const [form] = Form.useForm()
    const [erpTesteado, setErpTesteado] = useState(false)
    const [wmsTesteado, setWmsTesteado] = useState(false)

    const erpType = cliente.erp_type
    const tieneErp = erpType !== 'excel'
    const camposErp = CAMPOS_ERP[erpType] || []

    const { data: estadoCred, isLoading: cargandoEstado } = useEstadoCredenciales(cliente.id)
    const { data: credGuardadas } = useCredenciales(cliente.id)
    const probarErp = useProbarConexionConCredenciales(cliente.id, 'erp')
    const probarWms = useProbarConexionConCredenciales(cliente.id, 'odoo')
    const guardar = useGuardarCredenciales(cliente.id)
    const eliminar = useEliminarCredenciales(cliente.id)

    const credencialesExisten = estadoCred?.exists === true

    // Precargar formulario con credenciales guardadas
    useEffect(() => {
        if (!credGuardadas?.exists) return
        const campos = {}
        if (credGuardadas.erp) {
            Object.entries(credGuardadas.erp).forEach(([key, val]) => {
                campos[`erp_${key}`] = val
            })
        }
        if (credGuardadas.odoo) {
            Object.entries(credGuardadas.odoo).forEach(([key, val]) => {
                campos[`wms_${key}`] = val
            })
        }
        form.setFieldsValue(campos)
    }, [credGuardadas, form])

    const obtenerCredencialesErp = () => {
        const valores = form.getFieldsValue()
        const erp = {}
        camposErp.forEach((campo) => {
            const val = valores[`erp_${campo.name}`]
            erp[campo.name] = val || (campo.required ? '' : null)
        })
        return erp
    }

    const obtenerCredencialesWms = () => {
        const valores = form.getFieldsValue()
        return {
            url: valores.wms_url || '',
            database: valores.wms_database || '',
            usuario: valores.wms_usuario || '',
            clave: valores.wms_clave || '',
        }
    }

    const handleProbarErp = async () => {
        const erp = obtenerCredencialesErp()
        const resultado = await probarErp.mutateAsync({ erp })
        if (resultado?.success) setErpTesteado(true)
    }

    const handleProbarWms = async () => {
        const odoo = obtenerCredencialesWms()
        const resultado = await probarWms.mutateAsync({ odoo })
        if (resultado?.success) setWmsTesteado(true)
    }

    const handleGuardar = async () => {
        try {
            await form.validateFields()
        } catch {
            message.warning('Completa todos los campos obligatorios')
            return
        }

        const erp = tieneErp ? obtenerCredencialesErp() : {}
        const odoo = obtenerCredencialesWms()

        const resultado = await guardar.mutateAsync({ erp, odoo })
        if (resultado?.success) {
            message.success('Credenciales guardadas exitosamente')
        } else {
            message.error(resultado?.msg || 'Error al guardar credenciales')
        }
    }

    const handleValuesChange = () => {
        setErpTesteado(false)
        setWmsTesteado(false)
        probarErp.reset()
        probarWms.reset()
    }

    return (
        <div className="seccion" style={{ marginBottom: 0 }}>
            <div className="seccion__titulo">Credenciales de integración</div>
            <p className="seccion__sub">
                Configura las credenciales del ERP y del WMS para este cliente.
                Prueba ambas conexiones antes de guardar.
            </p>

            {!cargandoEstado && (
                <Alert
                    type={credencialesExisten ? 'success' : 'info'}
                    showIcon
                    style={{ marginTop: 12 }}
                    message={
                        credencialesExisten
                            ? 'Credenciales configuradas'
                            : 'No hay credenciales guardadas para este cliente'
                    }
                />
            )}

            <div className="seccion__linea" />

            <Form
                form={form}
                layout="vertical"
                onValuesChange={handleValuesChange}
            >
                <div className="grid-2">
                    {/* --- Columna ERP --- */}
                    <div className="columna">
                        <div className="cred-seccion-head">
                            <div className="test__icono test__icono--azul">
                                <IconServidor />
                            </div>
                            <div>
                                <div className="test__titulo">
                                    {tieneErp ? `ERP — ${etiquetaErp(erpType)}` : 'ERP — No aplica'}
                                </div>
                                <p className="test__sub" style={{ marginBottom: 0 }}>
                                    {tieneErp
                                        ? 'Credenciales de conexión al ERP del cliente'
                                        : 'Excel no requiere credenciales de ERP'}
                                </p>
                            </div>
                        </div>

                        {tieneErp ? (
                            <>
                                {camposErp.map((campo) => (
                                    <Form.Item
                                        key={campo.name}
                                        name={`erp_${campo.name}`}
                                        label={campo.label}
                                        rules={campo.required ? [{ required: true, message: `${campo.label} es obligatorio` }] : []}
                                        style={{ marginBottom: 12 }}
                                    >
                                        {campo.password
                                            ? <Input.Password autoComplete="off" />
                                            : <Input autoComplete="off" />
                                        }
                                    </Form.Item>
                                ))}

                                <Button
                                    type="primary"
                                    loading={probarErp.isPending}
                                    onClick={handleProbarErp}
                                >
                                    Probar conexión ERP
                                </Button>

                                <ResultadoTest
                                    resultado={probarErp.data}
                                    error={probarErp.isError ? probarErp.error : null}
                                />
                            </>
                        ) : (
                            <Alert
                                type="info"
                                showIcon
                                message="Los clientes Excel solo necesitan credenciales de WMS"
                            />
                        )}
                    </div>

                    {/* --- Columna WMS --- */}
                    <div className="columna">
                        <div className="cred-seccion-head">
                            <div className="test__icono test__icono--verde">
                                <IconNube />
                            </div>
                            <div>
                                <div className="test__titulo">WMS</div>
                                <p className="test__sub" style={{ marginBottom: 0 }}>
                                    Credenciales de la instancia de WMS donde se carga la información
                                </p>
                            </div>
                        </div>

                        {CAMPOS_WMS.map((campo) => (
                            <Form.Item
                                key={campo.name}
                                name={`wms_${campo.name}`}
                                label={campo.label}
                                rules={[{ required: true, message: `${campo.label} es obligatorio` }]}
                                style={{ marginBottom: 12 }}
                            >
                                {campo.password
                                    ? <Input.Password autoComplete="off" />
                                    : <Input autoComplete="off" />
                                }
                            </Form.Item>
                        ))}

                        <Button
                            loading={probarWms.isPending}
                            onClick={handleProbarWms}
                            style={{ background: '#52c41a', color: '#fff', borderColor: '#52c41a', boxShadow: '0 2px 6px rgba(82,196,26,.24)' }}
                        >
                            Probar conexión WMS
                        </Button>

                        <ResultadoTest
                            resultado={probarWms.data}
                            error={probarWms.isError ? probarWms.error : null}
                        />
                    </div>
                </div>
            </Form>

            {/* --- Acciones --- */}
            <div style={{ marginTop: 24, borderTop: '1px solid #f0f0f0', paddingTop: 20 }}>
                {guardar.isError && (
                    <Alert
                        type="error"
                        showIcon
                        style={{ marginBottom: 16 }}
                        message={mensajeDeError(guardar.error)}
                    />
                )}

                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    <Button
                        type="primary"
                        size="large"
                        loading={guardar.isPending}
                        onClick={handleGuardar}
                        disabled={tieneErp ? (!erpTesteado || !wmsTesteado) : !wmsTesteado}
                    >
                        Guardar credenciales
                    </Button>

                    {(tieneErp ? (!erpTesteado || !wmsTesteado) : !wmsTesteado) && (
                        <span style={{ fontSize: 13, color: '#8b93a1' }}>
                            Prueba {tieneErp ? 'ambas conexiones' : 'la conexión WMS'} antes de guardar
                        </span>
                    )}

                    <Popconfirm
                        title="Eliminar credenciales"
                        description="Se eliminará el secret de GCP y el archivo local. El cliente y sus flujos no se borran."
                        onConfirm={async () => {
                            try {
                                const r = await eliminar.mutateAsync()
                                if (r?.success) message.success('Credenciales eliminadas')
                                else message.error(r?.msg || 'No se pudieron eliminar')
                            } catch (err) {
                                message.error(mensajeDeError(err))
                            }
                        }}
                        okText="Eliminar"
                        okButtonProps={{ danger: true }}
                        cancelText="Cancelar"
                    >
                        <Button
                            danger
                            icon={<IconPapelera />}
                            loading={eliminar.isPending}
                            style={{ marginLeft: 'auto' }}
                        >
                            Eliminar credenciales
                        </Button>
                    </Popconfirm>
                </div>
            </div>
        </div>
    )
}

export default FormularioCredenciales

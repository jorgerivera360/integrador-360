import { useState } from 'react'
import { Alert, Button, Form, Input, InputNumber, Modal, Select, Switch, Upload } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { OPCIONES_ERP } from '@/config/erp'
import { testErpStandalone, testOdooStandalone, uploadSshKeyStandalone } from '@/services/clients'
import { IconCheck, IconEquis } from '../icons'

// --- Campos ERP por tipo ---

const CAMPOS_ERP = {
    ws: [
        { name: 'url', label: 'URL del Web Service', required: true },
        { name: 'conexion', label: 'Nombre de conexión', required: true },
        { name: 'compania', label: 'Compañía', required: true },
        { name: 'usuario', label: 'Usuario', required: true },
        { name: 'clave', label: 'Clave', required: true, password: true },
        { name: 'proveedor', label: 'Proveedor', required: true },
        { name: 'proxy_host', label: 'Proxy Host', required: false },
        { name: 'proxy_port', label: 'Proxy Port', required: false },
    ],
    connekta: [
        { name: 'url', label: 'URL', required: true },
        { name: 'urlqa', label: 'URL QA', required: false },
        { name: 'idcompania', label: 'Compañía', required: true },
        { name: 'connikey', label: 'ConniKey', required: true },
        { name: 'connitoken', label: 'ConniToken', required: true, password: true },
    ],
    sap: [
        { name: 'url', label: 'URL Service Layer', required: true },
        { name: 'compania', label: 'Compañía (base de datos)', required: true },
        { name: 'usuario', label: 'Usuario', required: true },
        { name: 'clave', label: 'Clave', required: true, password: true },
    ],
}

const CAMPOS_WMS = [
    { name: 'url', label: 'URL del WMS', required: true },
    { name: 'database', label: 'Base de datos', required: true },
    { name: 'usuario', label: 'Usuario', required: true },
    { name: 'clave', label: 'Clave', required: true, password: true },
]

const OPCIONES_TIPO = [
    ...OPCIONES_ERP,
]

const ResultadoInline = ({ resultado, error, label }) => {
    const fallo = Boolean(error)
    const exito = !fallo && resultado?.success === true
    if (!fallo && !resultado) return null

    const detalle = fallo ? (error?.response?.data?.detail || error?.message || 'Error') : resultado?.msg

    return (
        <div className={`resultado resultado--${exito ? 'ok' : 'error'}`} style={{ marginTop: 12 }}>
            <div className="resultado__head">
                {exito ? <IconCheck /> : <IconEquis />}
                {exito ? `${label}: conexión exitosa` : `${label}: conexión fallida`}
            </div>
            <div className="resultado__cuerpo">
                <div className="resultado__detalle">{detalle}</div>
            </div>
        </div>
    )
}

const ModalProbarConexion = ({ abierto, onCerrar }) => {
    const [form] = Form.useForm()
    const [erpType, setErpType] = useState(null)
    const [probandoErp, setProbandoErp] = useState(false)
    const [probandoWms, setProbandoWms] = useState(false)
    const [resultadoErp, setResultadoErp] = useState(null)
    const [resultadoWms, setResultadoWms] = useState(null)
    const [errorErp, setErrorErp] = useState(null)
    const [errorWms, setErrorWms] = useState(null)
    const [sshEnabled, setSshEnabled] = useState(false)
    const [sshKeyPath, setSshKeyPath] = useState('')
    const [sshFileName, setSshFileName] = useState('')
    const [subiendoLlave, setSubiendoLlave] = useState(false)

    const tieneErp = erpType && erpType !== 'excel'
    const camposErp = CAMPOS_ERP[erpType] || []

    const resetResultados = () => {
        setResultadoErp(null)
        setResultadoWms(null)
        setErrorErp(null)
        setErrorWms(null)
    }

    const handleTipoChange = (valor) => {
        setErpType(valor)
        form.resetFields()
        resetResultados()
        setSshEnabled(false)
        setSshKeyPath('')
        setSshFileName('')
    }

    const handleSshFileChange = async (info) => {
        const file = info.file
        if (!file) return
        setSubiendoLlave(true)
        try {
            const resp = await uploadSshKeyStandalone(file)
            const path = resp.data?.key_path || ''
            setSshKeyPath(path)
            setSshFileName(file.name)
        } catch (err) {
            console.error('Error al subir llave SSH:', err)
        } finally {
            setSubiendoLlave(false)
        }
    }

    const handleProbarErp = async () => {
        if (!tieneErp) return
        setProbandoErp(true)
        setResultadoErp(null)
        setErrorErp(null)
        try {
            const valores = form.getFieldsValue()
            const erp = { tipo: erpType }
            camposErp.forEach((c) => {
                erp[c.name] = valores[`erp_${c.name}`] || (c.required ? '' : null)
            })
            if (sshEnabled) {
                erp.ssh_enabled = true
                erp.ssh_host = valores.erp_ssh_host || ''
                erp.ssh_port = valores.erp_ssh_port || 22
                erp.ssh_user = valores.erp_ssh_user || ''
                erp.ssh_key_path = sshKeyPath
                erp.ssh_password = valores.erp_ssh_password || ''
            }
            const resp = await testErpStandalone({ erp })
            setResultadoErp(resp.data)
        } catch (err) {
            setErrorErp(err)
        } finally {
            setProbandoErp(false)
        }
    }

    const handleProbarWms = async () => {
        setProbandoWms(true)
        setResultadoWms(null)
        setErrorWms(null)
        try {
            const valores = form.getFieldsValue()
            const odoo = {
                url: valores.wms_url || '',
                database: valores.wms_database || '',
                usuario: valores.wms_usuario || '',
                clave: valores.wms_clave || '',
            }
            const resp = await testOdooStandalone({ odoo })
            setResultadoWms(resp.data)
        } catch (err) {
            setErrorWms(err)
        } finally {
            setProbandoWms(false)
        }
    }

    const handleCerrar = () => {
        setErpType(null)
        form.resetFields()
        resetResultados()
        setSshEnabled(false)
        setSshKeyPath('')
        setSshFileName('')
        onCerrar()
    }

    return (
        <Modal
            open={abierto}
            onCancel={handleCerrar}
            title="Probar conexión"
            footer={null}
            width={560}
            destroyOnClose
        >
            <p style={{ fontSize: 13, color: '#8b93a1', margin: '0 0 16px' }}>
                Prueba la conectividad con un ERP o WMS sin necesidad de crear el cliente.
            </p>

            <div style={{ marginBottom: 16 }}>
                <label className="campo-label" style={{ marginBottom: 8, display: 'block' }}>
                    Tipo de ERP
                </label>
                <Select
                    placeholder="Selecciona el tipo de ERP"
                    options={OPCIONES_TIPO}
                    value={erpType}
                    onChange={handleTipoChange}
                    style={{ width: '100%' }}
                />
            </div>

            {erpType && (
                <Form form={form} layout="vertical" onValuesChange={resetResultados}>
                    {/* Campos ERP */}
                    {tieneErp && (
                        <div style={{ marginBottom: 16 }}>
                            <div className="seccion__titulo" style={{ fontSize: 14, marginBottom: 12 }}>
                                Credenciales ERP
                            </div>

                            {/* --- Túnel SSH (opcional) — arriba de los campos ERP --- */}
                            <div style={{
                                border: '1px solid #d9d9d9',
                                borderRadius: 8,
                                padding: '12px 16px',
                                marginBottom: 16,
                                background: sshEnabled ? '#f6ffed' : '#fafafa',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: sshEnabled ? 12 : 0 }}>
                                    <Switch
                                        checked={sshEnabled}
                                        onChange={(checked) => {
                                            setSshEnabled(checked)
                                            resetResultados()
                                        }}
                                        size="small"
                                    />
                                    <span style={{ fontWeight: 500, fontSize: 13 }}>
                                        Túnel SSH
                                    </span>
                                    <span style={{ fontSize: 12, color: '#8b93a1' }}>
                                        Conectar a través de un servidor intermedio
                                    </span>
                                </div>

                                {sshEnabled && (
                                    <>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px', gap: 8 }}>
                                            <Form.Item
                                                name="erp_ssh_host"
                                                label="Host SSH"
                                                rules={[{ required: true, message: 'Host SSH es obligatorio' }]}
                                                style={{ marginBottom: 8 }}
                                            >
                                                <Input placeholder="192.168.1.100" autoComplete="off" />
                                            </Form.Item>
                                            <Form.Item
                                                name="erp_ssh_port"
                                                label="Puerto"
                                                initialValue={22}
                                                style={{ marginBottom: 8 }}
                                            >
                                                <InputNumber min={1} max={65535} style={{ width: '100%' }} />
                                            </Form.Item>
                                        </div>
                                        <Form.Item
                                            name="erp_ssh_user"
                                            label="Usuario SSH"
                                            rules={[{ required: true, message: 'Usuario SSH es obligatorio' }]}
                                            style={{ marginBottom: 8 }}
                                        >
                                            <Input placeholder="ubuntu" autoComplete="off" />
                                        </Form.Item>
                                        <div style={{ marginBottom: 8 }}>
                                            <label style={{ display: 'block', marginBottom: 4, fontSize: 14 }}>
                                                Llave SSH (.pem / .ppk)
                                            </label>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <Upload
                                                    accept=".pem,.ppk,.key"
                                                    showUploadList={false}
                                                    beforeUpload={() => false}
                                                    onChange={handleSshFileChange}
                                                >
                                                    <Button
                                                        icon={<UploadOutlined />}
                                                        loading={subiendoLlave}
                                                    >
                                                        Seleccionar archivo
                                                    </Button>
                                                </Upload>
                                                {sshFileName && (
                                                    <span style={{ fontSize: 13, color: '#52c41a' }}>
                                                        {sshFileName}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <Form.Item
                                            name="erp_ssh_password"
                                            label="Contraseña SSH (si no usa llave)"
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input.Password placeholder="Opcional si usa llave" autoComplete="off" />
                                        </Form.Item>
                                    </>
                                )}
                            </div>

                            {camposErp.map((campo) => (
                                <Form.Item
                                    key={campo.name}
                                    name={`erp_${campo.name}`}
                                    label={campo.label}
                                    rules={campo.required ? [{ required: true, message: `${campo.label} es obligatorio` }] : []}
                                    style={{ marginBottom: 10 }}
                                >
                                    {campo.password
                                        ? <Input.Password autoComplete="off" />
                                        : <Input autoComplete="off" />
                                    }
                                </Form.Item>
                            ))}
                            <Button
                                type="primary"
                                loading={probandoErp}
                                onClick={handleProbarErp}
                            >
                                Probar conexión ERP
                            </Button>
                            <ResultadoInline resultado={resultadoErp} error={errorErp} label="ERP" />
                        </div>
                    )}

                    {/* Campos WMS */}
                    <div style={{ marginBottom: 8, borderTop: tieneErp ? '1px solid #f0f0f0' : 'none', paddingTop: tieneErp ? 16 : 0 }}>
                        <div className="seccion__titulo" style={{ fontSize: 14, marginBottom: 12 }}>
                            Credenciales WMS
                        </div>
                        {CAMPOS_WMS.map((campo) => (
                            <Form.Item
                                key={campo.name}
                                name={`wms_${campo.name}`}
                                label={campo.label}
                                rules={[{ required: true, message: `${campo.label} es obligatorio` }]}
                                style={{ marginBottom: 10 }}
                            >
                                {campo.password
                                    ? <Input.Password autoComplete="off" />
                                    : <Input autoComplete="off" />
                                }
                            </Form.Item>
                        ))}
                        <Button
                            loading={probandoWms}
                            onClick={handleProbarWms}
                            style={{ background: '#52c41a', color: '#fff', borderColor: '#52c41a', boxShadow: '0 2px 6px rgba(82,196,26,.24)' }}
                        >
                            Probar conexión WMS
                        </Button>
                        <ResultadoInline resultado={resultadoWms} error={errorWms} label="WMS" />
                    </div>
                </Form>
            )}
        </Modal>
    )
}

export default ModalProbarConexion

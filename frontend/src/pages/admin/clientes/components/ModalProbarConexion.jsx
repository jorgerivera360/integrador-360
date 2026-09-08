import { useState } from 'react'
import { Alert, Button, Form, Input, Modal, Select } from 'antd'
import { OPCIONES_ERP } from '@/config/erp'
import { testErpStandalone, testOdooStandalone } from '@/services/clients'
import { IconCheck, IconEquis } from '../icons'

// --- Campos ERP por tipo ---

const CAMPOS_ERP = {
    ws: [
        { name: 'url', label: 'URL del Web Service', required: true },
        { name: 'conexion', label: 'Nombre de conexión', required: true },
        { name: 'compania', label: 'ID Compañía', required: true },
        { name: 'usuario', label: 'Usuario', required: true },
        { name: 'clave', label: 'Clave', required: true, password: true },
        { name: 'proveedor', label: 'Proveedor', required: true },
        { name: 'proxy_host', label: 'Proxy Host', required: false },
        { name: 'proxy_port', label: 'Proxy Port', required: false },
    ],
    connekta: [
        { name: 'url', label: 'URL', required: true },
        { name: 'urlqa', label: 'URL QA', required: false },
        { name: 'idcompania', label: 'ID Compañía', required: true },
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

// Opciones sin Excel (no tiene ERP que probar de forma independiente, y WMS se prueba igual)
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

/**
 * Modal para probar conexiones sin tener un cliente creado.
 * Usa un client_id temporal (0) — los endpoints de test con body
 * no necesitan que el cliente exista en BD cuando se envían credenciales.
 *
 * Nota: el endpoint requiere un client_id en la URL, pero con body
 * de credenciales no lo usa para cargar de GCP. Usamos el ID del
 * primer cliente disponible o un ID especial.
 */
const ModalProbarConexion = ({ abierto, onCerrar }) => {
    const [form] = Form.useForm()
    const [erpType, setErpType] = useState(null)
    const [probandoErp, setProbandoErp] = useState(false)
    const [probandoWms, setProbandoWms] = useState(false)
    const [resultadoErp, setResultadoErp] = useState(null)
    const [resultadoWms, setResultadoWms] = useState(null)
    const [errorErp, setErrorErp] = useState(null)
    const [errorWms, setErrorWms] = useState(null)

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

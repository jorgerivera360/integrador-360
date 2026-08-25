import { useEffect } from 'react'
import { Alert, Form, Input, Modal, Select, Tooltip } from 'antd'
import { OPCIONES_ERP } from '@/config/erp'
import { useCrearCliente, mensajeDeError } from '@/hooks/useClientes'
import { IconInfo } from '../icons'

const AYUDA_ID =
    'Debe ser único. Se usará como nombre del secret en GCP (integrador-{id}) ' +
    'y como CLIENT_ID del contenedor Docker.'

const ModalCrearCliente = ({ abierto, onCerrar, onCreado }) => {
    const [form] = Form.useForm()
    const crear = useCrearCliente()
    const { reset } = crear // referencia estable; el objeto `crear` cambia en cada render

    // Formulario limpio en cada apertura, incluido el error del intento anterior.
    useEffect(() => {
        if (abierto) {
            form.resetFields()
            reset()
        }
    }, [abierto, form, reset])

    const enviar = async () => {
        const valores = await form.validateFields()
        const { data } = await crear.mutateAsync({
            client_id: valores.client_id.trim(),
            name: valores.name.trim(),
            erp_type: valores.erp_type,
        })
        onCreado?.(data)
        onCerrar()
    }

    return (
        <Modal
            title="Nuevo cliente"
            open={abierto}
            onCancel={onCerrar}
            onOk={enviar}
            okText="Crear cliente"
            cancelText="Cancelar"
            confirmLoading={crear.isPending}
            width={520}
            destroyOnClose
        >
            <Form
                form={form}
                layout="vertical"
                initialValues={{ erp_type: 'ws' }}
                onFinish={enviar}
            >
                <Form.Item
                    name="client_id"
                    label={
                        <span className="campo-label">
                            ID del cliente
                            <Tooltip title={AYUDA_ID}>
                                <span style={{ cursor: 'help' }}>
                                    <IconInfo width={15} height={15} style={{ color: '#bfbfbf' }} />
                                </span>
                            </Tooltip>
                        </span>
                    }
                    rules={[
                        { required: true, message: 'El ID es obligatorio' },
                        {
                            pattern: /^[a-z0-9_-]+$/,
                            message: 'Solo minúsculas, números, guion y guion bajo',
                        },
                        { max: 50, message: 'Máximo 50 caracteres' },
                    ]}
                >
                    <Input className="campo-mono" placeholder="ej: fenixcol" autoComplete="off" />
                </Form.Item>

                <Form.Item
                    name="name"
                    label={<span className="campo-label">Nombre</span>}
                    rules={[{ required: true, message: 'El nombre es obligatorio' }]}
                >
                    <Input placeholder="ej: Fenix Colombia" autoComplete="off" />
                </Form.Item>

                <Form.Item
                    name="erp_type"
                    label={<span className="campo-label">Tipo de ERP</span>}
                    rules={[{ required: true, message: 'Elige un tipo de ERP' }]}
                >
                    <Select options={OPCIONES_ERP} />
                </Form.Item>
            </Form>

            {crear.isError && (
                <Alert type="error" showIcon message={mensajeDeError(crear.error)} />
            )}
        </Modal>
    )
}

export default ModalCrearCliente

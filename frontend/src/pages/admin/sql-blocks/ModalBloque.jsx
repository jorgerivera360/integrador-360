import { useEffect } from 'react'
import { Modal, Form, Input, Select, InputNumber, Checkbox, Button, Space } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'

const { TextArea } = Input

const BLOCK_TYPES = [
    { value: 'base', label: 'Consulta base' },
    { value: 'campo', label: 'Campo' },
    { value: 'filtro', label: 'Filtro' },
]

const ENTITY_OPTIONS = [
    { value: 'items', label: 'Productos' },
    { value: 'customer', label: 'Clientes' },
    { value: 'supplier', label: 'Proveedores' },
    { value: 'purchases', label: 'Compras' },
    { value: 'sales', label: 'Ventas' },
]

const VARIABLE_TYPES = [
    { value: 'number', label: 'Numero' },
    { value: 'text', label: 'Texto' },
    { value: 'list', label: 'Lista (comas)' },
]

const ModalBloque = ({ open, bloque, bases, onOk, onCancel, loading }) => {
    const [form] = Form.useForm()
    const esEdicion = Boolean(bloque?.id)
    const blockType = Form.useWatch('block_type', form)

    useEffect(() => {
        if (open) {
            if (bloque) {
                const entityList = (bloque.entity_types || '').split(',').map((s) => s.trim()).filter(Boolean)
                form.setFieldsValue({
                    ...bloque,
                    entity_types_list: entityList,
                    variables: bloque.variables || [],
                })
            } else {
                form.resetFields()
                form.setFieldsValue({ block_type: 'campo', sort_order: 0, variables: [] })
            }
        }
    }, [open, bloque, form])

    const handleOk = () => {
        form.validateFields().then((values) => {
            const data = {
                ...values,
                entity_types: (values.entity_types_list || []).join(','),
            }
            delete data.entity_types_list
            onOk(data)
        })
    }

    return (
        <Modal
            title={esEdicion ? 'Editar bloque SQL' : 'Crear bloque SQL'}
            open={open}
            onOk={handleOk}
            onCancel={onCancel}
            confirmLoading={loading}
            width={720}
            okText="Guardar"
            cancelText="Cancelar"
        >
            <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
                <Form.Item name="name" label="Nombre" rules={[{ required: true, message: 'Obligatorio' }]}>
                    <Input />
                </Form.Item>

                <Form.Item name="description" label="Descripcion">
                    <TextArea rows={2} />
                </Form.Item>

                <Space size="middle" style={{ width: '100%' }}>
                    <Form.Item name="block_type" label="Tipo" rules={[{ required: true }]} style={{ minWidth: 160 }}>
                        <Select options={BLOCK_TYPES} disabled={esEdicion} />
                    </Form.Item>

                    <Form.Item name="sort_order" label="Orden" style={{ minWidth: 100 }}>
                        <InputNumber min={0} />
                    </Form.Item>
                </Space>

                <Form.Item
                    name="entity_types_list"
                    label="Entidades"
                    rules={[{ required: true, message: 'Selecciona al menos una entidad' }]}
                >
                    <Checkbox.Group options={ENTITY_OPTIONS} />
                </Form.Item>

                {blockType !== 'filtro' && (
                    <Form.Item
                        name="requires_block_id"
                        label="Requiere consulta base"
                    >
                        <Select
                            allowClear
                            placeholder="Ninguna (independiente)"
                            options={bases.map((b) => ({ value: b.id, label: b.name }))}
                        />
                    </Form.Item>
                )}

                {blockType !== 'filtro' && (
                    <Form.Item name="select_fragment" label="Fragmento SELECT">
                        <TextArea rows={4} spellCheck={false} style={{ fontFamily: 'monospace', fontSize: 13 }} />
                    </Form.Item>
                )}

                {blockType === 'base' && (
                    <p style={{ color: '#888', fontSize: 12, marginTop: -12, marginBottom: 16 }}>
                        Incluye todo: SET QUOTED_IDENTIFIER, SELECT, FROM, JOINs base, WHERE base y GROUP BY si aplica.
                    </p>
                )}

                {blockType === 'campo' && (
                    <>
                        <Form.Item name="join_fragment" label="Fragmento JOIN (opcional)">
                            <TextArea rows={3} spellCheck={false} style={{ fontFamily: 'monospace', fontSize: 13 }} />
                        </Form.Item>

                        <Form.Item name="group_by_fragment" label="Fragmento GROUP BY (opcional)">
                            <Input spellCheck={false} style={{ fontFamily: 'monospace', fontSize: 13 }} />
                        </Form.Item>
                    </>
                )}

                {blockType === 'filtro' && (
                    <Form.Item
                        name="where_fragment"
                        label="Condicion WHERE"
                        rules={[{ required: blockType === 'filtro', message: 'Obligatorio para filtros' }]}
                    >
                        <TextArea rows={3} spellCheck={false} style={{ fontFamily: 'monospace', fontSize: 13 }} />
                    </Form.Item>
                )}

                <Form.List name="variables">
                    {(fields, { add, remove }) => (
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <span style={{ fontWeight: 500 }}>Variables</span>
                                <Button type="dashed" size="small" icon={<PlusOutlined />} onClick={() => add({ name: '', label: '', type: 'text', default: '' })}>
                                    Agregar
                                </Button>
                            </div>
                            {fields.map(({ key, name, ...rest }) => (
                                <Space key={key} align="start" style={{ display: 'flex', marginBottom: 4 }}>
                                    <Form.Item {...rest} name={[name, 'name']} rules={[{ required: true, message: 'Nombre' }]}>
                                        <Input placeholder="nombre" style={{ width: 120 }} />
                                    </Form.Item>
                                    <Form.Item {...rest} name={[name, 'label']}>
                                        <Input placeholder="Etiqueta" style={{ width: 160 }} />
                                    </Form.Item>
                                    <Form.Item {...rest} name={[name, 'type']}>
                                        <Select options={VARIABLE_TYPES} style={{ width: 130 }} />
                                    </Form.Item>
                                    <Form.Item {...rest} name={[name, 'default']}>
                                        <Input placeholder="Default" style={{ width: 100 }} />
                                    </Form.Item>
                                    <Button icon={<DeleteOutlined />} danger size="small" onClick={() => remove(name)} />
                                </Space>
                            ))}
                        </div>
                    )}
                </Form.List>

                {esEdicion && (
                    <Form.Item name="is_active" valuePropName="checked" style={{ marginTop: 16 }}>
                        <Checkbox>Activo</Checkbox>
                    </Form.Item>
                )}
            </Form>
        </Modal>
    )
}

export default ModalBloque

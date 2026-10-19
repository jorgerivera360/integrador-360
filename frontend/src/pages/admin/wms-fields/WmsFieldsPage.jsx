import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Button, Tag, Select, Input, Switch, Popconfirm, App, Tooltip, Modal, Form } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons'
import useHasRole from '@/hooks/useHasRole'
import { useSetBreadcrumb } from '@/layouts/BreadcrumbContext'
import { getWmsFields, createWmsField, updateWmsField, deleteWmsField } from '@/services/wmsFields'
import BotonVolver from '@/components/BotonVolver'
import '@/styles/pagina.css'

const UBICACIONES = [
    { value: 'cabecera', label: 'Cabecera' },
    { value: 'linea', label: 'L\u00ednea' },
]

const TIPOS = [
    { value: 'texto', label: 'Texto' },
    { value: 'entero', label: 'Entero' },
    { value: 'decimal', label: 'Decimal' },
    { value: 'booleano', label: 'Booleano' },
]

const MODELOS = [
    { value: 'sale.order', label: 'sale.order', color: 'blue' },
    { value: 'purchase.order', label: 'purchase.order', color: 'green' },
    { value: 'stock.picking', label: 'stock.picking', color: 'orange' },
]

const COLOR_UBICACION = { cabecera: 'purple', linea: 'cyan' }

const WmsFieldsPage = () => {
    const queryClient = useQueryClient()
    const { message } = App.useApp()
    const puedeEditar = useHasRole(['superadmin', 'admin'])
    const puedeBorrar = useHasRole(['superadmin'])
    useSetBreadcrumb('Campos WMS')

    const [modalOpen, setModalOpen] = useState(false)
    const [editando, setEditando] = useState(null)
    const [form] = Form.useForm()

    const { data: campos, isPending } = useQuery({
        queryKey: ['wms-fields'],
        queryFn: () => getWmsFields(),
    })

    const mutCrear = useMutation({
        mutationFn: createWmsField,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['wms-fields'] })
            message.success('Campo creado')
            cerrarModal()
        },
        onError: (err) => message.error(err.response?.data?.detail || 'Error al crear'),
    })

    const mutActualizar = useMutation({
        mutationFn: ({ id, data }) => updateWmsField(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['wms-fields'] })
            message.success('Campo actualizado')
            cerrarModal()
        },
        onError: (err) => message.error(err.response?.data?.detail || 'Error al actualizar'),
    })

    const mutBorrar = useMutation({
        mutationFn: deleteWmsField,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['wms-fields'] })
            message.success('Campo eliminado')
        },
    })

    const abrirCrear = () => {
        setEditando(null)
        form.resetFields()
        form.setFieldsValue({ tipo_valor: 'texto', ubicacion: 'linea', modelos: [], is_active: true })
        setModalOpen(true)
    }

    const abrirEditar = (registro) => {
        setEditando(registro)
        form.setFieldsValue(registro)
        setModalOpen(true)
    }

    const cerrarModal = () => {
        setModalOpen(false)
        setEditando(null)
        form.resetFields()
    }

    const guardar = () => {
        form.validateFields().then((values) => {
            if (editando) {
                mutActualizar.mutate({ id: editando.id, data: values })
            } else {
                mutCrear.mutate(values)
            }
        })
    }

    const columnas = [
        {
            title: 'Campo origen',
            dataIndex: 'campo_origen',
            key: 'campo_origen',
            render: (v) => <code style={{ fontSize: 12.5 }}>{v}</code>,
        },
        {
            title: 'Campo WMS',
            dataIndex: 'campo_destino',
            key: 'campo_destino',
            render: (v) => <code style={{ fontSize: 12.5 }}>{v}</code>,
        },
        {
            title: 'Ubicaci\u00f3n',
            dataIndex: 'ubicacion',
            key: 'ubicacion',
            width: 100,
            render: (v) => <Tag color={COLOR_UBICACION[v]}>{v === 'cabecera' ? 'Cabecera' : 'L\u00ednea'}</Tag>,
        },
        {
            title: 'Modelos',
            dataIndex: 'modelos',
            key: 'modelos',
            render: (modelos) => (modelos || []).map((m) => {
                const info = MODELOS.find((o) => o.value === m)
                return <Tag key={m} color={info?.color || 'default'} style={{ fontSize: 11 }}>{m}</Tag>
            }),
        },
        {
            title: 'Tipo',
            dataIndex: 'tipo_valor',
            key: 'tipo_valor',
            width: 80,
        },
        {
            title: 'Default',
            dataIndex: 'valor_default',
            key: 'valor_default',
            width: 80,
            render: (v) => v != null ? <code style={{ fontSize: 11 }}>{v}</code> : <span style={{ color: '#bfbfbf' }}>&mdash;</span>,
        },
        {
            title: 'Activo',
            dataIndex: 'is_active',
            key: 'is_active',
            width: 70,
            render: (v) => v ? <Tag color="green">S\u00ed</Tag> : <Tag>No</Tag>,
        },
    ]

    if (puedeEditar) {
        columnas.push({
            title: '',
            key: 'acciones',
            width: 80,
            render: (_, registro) => (
                <div style={{ display: 'flex', gap: 4 }}>
                    <Button
                        type="text" size="small" icon={<EditOutlined />}
                        onClick={() => abrirEditar(registro)}
                    />
                    {puedeBorrar && (
                        <Popconfirm
                            title="Eliminar este campo?"
                            onConfirm={() => mutBorrar.mutate(registro.id)}
                        >
                            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
                        </Popconfirm>
                    )}
                </div>
            ),
        })
    }

    return (
        <>
            <BotonVolver to="/admin" />

            <div className="pagina-head">
                <div>
                    <h1 className="pagina-head__titulo">
                        Campos WMS{' '}
                        <Tooltip title="Mapeo de campos del ERP hacia campos de Odoo. Cuando un campo del transform coincide con uno de esta tabla, el core lo incluye autom\u00e1ticamente en el payload que env\u00eda al WMS.">
                            <InfoCircleOutlined style={{ fontSize: 16, color: '#8c8c8c' }} />
                        </Tooltip>
                    </h1>
                </div>
                {puedeEditar && (
                    <Button type="primary" icon={<PlusOutlined />} onClick={abrirCrear}>
                        Agregar campo
                    </Button>
                )}
            </div>

            <div className="tarjeta-borde">
                <Table
                    dataSource={campos || []}
                    columns={columnas}
                    rowKey="id"
                    loading={isPending}
                    size="small"
                    pagination={false}
                />
            </div>

            <Modal
                title={editando ? 'Editar campo WMS' : 'Nuevo campo WMS'}
                open={modalOpen}
                onCancel={cerrarModal}
                onOk={guardar}
                confirmLoading={mutCrear.isPending || mutActualizar.isPending}
                okText={editando ? 'Guardar' : 'Crear'}
                width={520}
            >
                <Form form={form} layout="vertical" size="small" style={{ marginTop: 16 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <Form.Item
                            name="campo_origen" label="Campo origen (del transform)"
                            rules={[{ required: true, message: 'Obligatorio' }]}
                            tooltip="Nombre del campo como viene del SQL/mapping. Ej: lote, sub_bodega, bodega_siesa"
                        >
                            <Input placeholder="lote" />
                        </Form.Item>
                        <Form.Item
                            name="campo_destino" label="Campo WMS (Odoo)"
                            rules={[{ required: true, message: 'Obligatorio' }]}
                            tooltip="Nombre del campo en el modelo de Odoo. Ej: lot_name, block_location_origin"
                        >
                            <Input placeholder="lot_name" />
                        </Form.Item>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <Form.Item
                            name="ubicacion" label="Ubicaci\u00f3n en el payload"
                            rules={[{ required: true }]}
                            tooltip="'Cabecera' = en el dict principal del create. 'L\u00ednea' = dentro de cada order_line o move."
                        >
                            <Select options={UBICACIONES} />
                        </Form.Item>
                        <Form.Item
                            name="tipo_valor" label="Tipo de valor"
                            rules={[{ required: true }]}
                            tooltip="C\u00f3mo se convierte el valor antes de enviarlo. 'Texto' lo env\u00eda tal cual, 'Entero' convierte a int, etc."
                        >
                            <Select options={TIPOS} />
                        </Form.Item>
                    </div>

                    <Form.Item
                        name="modelos" label="Modelos donde aplica"
                        rules={[{ required: true, message: 'Selecciona al menos un modelo' }]}
                        tooltip="En qu\u00e9 modelos de Odoo se agrega este campo al crear un registro."
                    >
                        <Select mode="multiple" options={MODELOS} placeholder="Seleccionar modelos..." />
                    </Form.Item>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        <Form.Item
                            name="valor_default" label="Valor por defecto"
                            tooltip="Si el campo no viene en la fila, se env\u00eda este valor. Dejar vac\u00edo = no enviar nada si no viene."
                        >
                            <Input placeholder="Vac\u00edo = no enviar" />
                        </Form.Item>
                        <Form.Item name="is_active" label="Activo" valuePropName="checked">
                            <Switch />
                        </Form.Item>
                    </div>

                    <Form.Item name="descripcion" label="Descripci\u00f3n">
                        <Input.TextArea rows={2} placeholder="Para qu\u00e9 se usa este campo..." />
                    </Form.Item>
                </Form>
            </Modal>
        </>
    )
}

export default WmsFieldsPage

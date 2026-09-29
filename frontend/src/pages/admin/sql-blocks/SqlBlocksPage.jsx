import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Table, Button, Tag, Switch, Tabs, Popconfirm, message, Space, Empty } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import useHasRole from '@/hooks/useHasRole'
import { getSqlBlocks, createSqlBlock, updateSqlBlock, deleteSqlBlock } from '@/services/sqlBlocks'
import ModalBloque from './ModalBloque'

const ENTITY_LABELS = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Compras',
    sales: 'Ventas',
}

const ENTITY_COLORS = {
    items: 'blue',
    customer: 'green',
    supplier: 'orange',
    purchases: 'purple',
    sales: 'cyan',
}

const SqlBlocksPage = () => {
    const queryClient = useQueryClient()
    const puedeEditar = useHasRole(['superadmin', 'admin'])
    const puedeBorrar = useHasRole(['superadmin'])

    const [modalOpen, setModalOpen] = useState(false)
    const [bloqueActual, setBloqueActual] = useState(null)
    const [tabActiva, setTabActiva] = useState('base')

    const { data: bloques = [], isLoading } = useQuery({
        queryKey: ['sql-blocks'],
        queryFn: () => getSqlBlocks(),
    })

    const crear = useMutation({
        mutationFn: createSqlBlock,
        onSuccess: () => {
            message.success('Bloque creado')
            queryClient.invalidateQueries({ queryKey: ['sql-blocks'] })
            cerrarModal()
        },
        onError: (err) => message.error(err.response?.data?.detail || 'Error al crear'),
    })

    const actualizar = useMutation({
        mutationFn: ({ id, data }) => updateSqlBlock(id, data),
        onSuccess: () => {
            message.success('Bloque actualizado')
            queryClient.invalidateQueries({ queryKey: ['sql-blocks'] })
            cerrarModal()
        },
        onError: (err) => message.error(err.response?.data?.detail || 'Error al actualizar'),
    })

    const eliminar = useMutation({
        mutationFn: deleteSqlBlock,
        onSuccess: () => {
            message.success('Bloque eliminado')
            queryClient.invalidateQueries({ queryKey: ['sql-blocks'] })
        },
        onError: (err) => message.error(err.response?.data?.detail || 'Error al eliminar'),
    })

    const cerrarModal = () => {
        setModalOpen(false)
        setBloqueActual(null)
    }

    const abrirCrear = () => {
        setBloqueActual({ block_type: tabActiva })
        setModalOpen(true)
    }

    const abrirEditar = (bloque) => {
        setBloqueActual(bloque)
        setModalOpen(true)
    }

    const handleGuardar = (data) => {
        if (bloqueActual?.id) {
            actualizar.mutate({ id: bloqueActual.id, data })
        } else {
            crear.mutate(data)
        }
    }

    const handleToggleActivo = (bloque) => {
        actualizar.mutate({ id: bloque.id, data: { is_active: !bloque.is_active } })
    }

    const bases = bloques.filter((b) => b.block_type === 'base')

    const renderEntities = (entityTypes) => {
        const tipos = (entityTypes || '').split(',').map((s) => s.trim()).filter(Boolean)
        return tipos.map((t) => (
            <Tag key={t} color={ENTITY_COLORS[t] || 'default'} style={{ fontSize: 11 }}>
                {ENTITY_LABELS[t] || t}
            </Tag>
        ))
    }

    const columnasBases = [
        { title: 'Nombre', dataIndex: 'name', key: 'name', width: 250 },
        { title: 'Descripcion', dataIndex: 'description', key: 'description', ellipsis: true },
        {
            title: 'Entidades', dataIndex: 'entity_types', key: 'entity_types', width: 300,
            render: renderEntities,
        },
        {
            title: 'Activo', dataIndex: 'is_active', key: 'is_active', width: 80,
            render: (activo, record) => (
                <Switch size="small" checked={activo} onChange={() => handleToggleActivo(record)} disabled={!puedeEditar} />
            ),
        },
        {
            title: '', key: 'acciones', width: 100,
            render: (_, record) => (
                <Space size="small">
                    {puedeEditar && <Button size="small" icon={<EditOutlined />} onClick={() => abrirEditar(record)} />}
                    {puedeBorrar && (
                        <Popconfirm title="Eliminar este bloque?" onConfirm={() => eliminar.mutate(record.id)}>
                            <Button size="small" icon={<DeleteOutlined />} danger />
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ]

    const columnasCampos = [
        { title: 'Nombre', dataIndex: 'name', key: 'name', width: 220 },
        { title: 'Descripcion', dataIndex: 'description', key: 'description', ellipsis: true },
        {
            title: 'Entidades', dataIndex: 'entity_types', key: 'entity_types', width: 280,
            render: renderEntities,
        },
        {
            title: 'Requiere', dataIndex: 'requires_block_id', key: 'requires', width: 200,
            render: (id) => {
                if (!id) return <span style={{ color: '#999' }}>-</span>
                const base = bases.find((b) => b.id === id)
                return base ? <Tag>{base.name}</Tag> : <Tag color="red">ID {id}</Tag>
            },
        },
        {
            title: 'Variables', dataIndex: 'variables', key: 'variables', width: 100,
            render: (vars) => vars?.length ? <Tag color="blue">{vars.length}</Tag> : '-',
        },
        {
            title: 'Activo', dataIndex: 'is_active', key: 'is_active', width: 80,
            render: (activo, record) => (
                <Switch size="small" checked={activo} onChange={() => handleToggleActivo(record)} disabled={!puedeEditar} />
            ),
        },
        {
            title: '', key: 'acciones', width: 100,
            render: (_, record) => (
                <Space size="small">
                    {puedeEditar && <Button size="small" icon={<EditOutlined />} onClick={() => abrirEditar(record)} />}
                    {puedeBorrar && (
                        <Popconfirm title="Eliminar este bloque?" onConfirm={() => eliminar.mutate(record.id)}>
                            <Button size="small" icon={<DeleteOutlined />} danger />
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ]

    const columnasFiltros = [
        { title: 'Nombre', dataIndex: 'name', key: 'name', width: 220 },
        { title: 'Descripcion', dataIndex: 'description', key: 'description', ellipsis: true },
        {
            title: 'WHERE', dataIndex: 'where_fragment', key: 'where', width: 300,
            render: (w) => <code style={{ fontSize: 12 }}>{w}</code>,
        },
        {
            title: 'Entidades', dataIndex: 'entity_types', key: 'entity_types', width: 280,
            render: renderEntities,
        },
        {
            title: 'Variables', dataIndex: 'variables', key: 'variables', width: 100,
            render: (vars) => vars?.length ? <Tag color="blue">{vars.length}</Tag> : '-',
        },
        {
            title: 'Activo', dataIndex: 'is_active', key: 'is_active', width: 80,
            render: (activo, record) => (
                <Switch size="small" checked={activo} onChange={() => handleToggleActivo(record)} disabled={!puedeEditar} />
            ),
        },
        {
            title: '', key: 'acciones', width: 100,
            render: (_, record) => (
                <Space size="small">
                    {puedeEditar && <Button size="small" icon={<EditOutlined />} onClick={() => abrirEditar(record)} />}
                    {puedeBorrar && (
                        <Popconfirm title="Eliminar este bloque?" onConfirm={() => eliminar.mutate(record.id)}>
                            <Button size="small" icon={<DeleteOutlined />} danger />
                        </Popconfirm>
                    )}
                </Space>
            ),
        },
    ]

    const items = [
        {
            key: 'base',
            label: `Consultas base (${bloques.filter((b) => b.block_type === 'base').length})`,
            children: (
                <Table
                    dataSource={bloques.filter((b) => b.block_type === 'base')}
                    columns={columnasBases}
                    rowKey="id"
                    loading={isLoading}
                    size="small"
                    pagination={false}
                    locale={{ emptyText: <Empty description="No hay consultas base" /> }}
                />
            ),
        },
        {
            key: 'campo',
            label: `Campos (${bloques.filter((b) => b.block_type === 'campo').length})`,
            children: (
                <Table
                    dataSource={bloques.filter((b) => b.block_type === 'campo')}
                    columns={columnasCampos}
                    rowKey="id"
                    loading={isLoading}
                    size="small"
                    pagination={false}
                    locale={{ emptyText: <Empty description="No hay bloques de campo" /> }}
                />
            ),
        },
        {
            key: 'filtro',
            label: `Filtros (${bloques.filter((b) => b.block_type === 'filtro').length})`,
            children: (
                <Table
                    dataSource={bloques.filter((b) => b.block_type === 'filtro')}
                    columns={columnasFiltros}
                    rowKey="id"
                    loading={isLoading}
                    size="small"
                    pagination={false}
                    locale={{ emptyText: <Empty description="No hay bloques de filtro" /> }}
                />
            ),
        },
    ]

    return (
        <div style={{ padding: '0 4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h1 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>Configuracion SQL</h1>
                {puedeEditar && (
                    <Button type="primary" icon={<PlusOutlined />} onClick={abrirCrear}>
                        Crear bloque
                    </Button>
                )}
            </div>

            <p style={{ color: '#666', marginBottom: 20, fontSize: 13 }}>
                Bloques reutilizables para armar consultas SQL de flujos SIESA WS sin escribir codigo.
                Los flujos en modo visual eligen una consulta base, activan campos y agregan filtros.
            </p>

            <Tabs items={items} activeKey={tabActiva} onChange={setTabActiva} />

            <ModalBloque
                open={modalOpen}
                bloque={bloqueActual}
                bases={bases}
                onOk={handleGuardar}
                onCancel={cerrarModal}
                loading={crear.isPending || actualizar.isPending}
            />
        </div>
    )
}

export default SqlBlocksPage

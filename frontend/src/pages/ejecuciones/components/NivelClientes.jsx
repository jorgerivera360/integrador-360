import { useState } from 'react'
import { Alert, Button, Input, Select, Space, Table } from 'antd'
import ErpTag from '@/components/ErpTag'
import ActivoTag from '@/components/ActivoTag'
import useDebounce from '@/hooks/useDebounce'
import { useClientesEjecuciones, mensajeDeError } from '@/hooks/useEjecuciones'
import { OPCIONES_ERP } from '@/config/erp'
import { IconFlecha, IconLupa } from '../icons'

const FILTROS_VACIOS = { search: '', erpType: null, isActive: null }

const columnas = [
    {
        title: 'Cliente',
        dataIndex: 'name',
        key: 'name',
        className: 'celda-nombre',
        sorter: (a, b) => a.name.localeCompare(b.name, 'es'),
    },
    {
        title: 'ERP',
        dataIndex: 'erp_type',
        key: 'erp_type',
        align: 'center',
        render: (erpType) => <ErpTag erpType={erpType} />,
    },
    {
        title: 'Flujos',
        key: 'flujos',
        align: 'center',
        className: 'celda-tenue',
        render: () => '—',
    },
    {
        title: 'Estado',
        dataIndex: 'is_active',
        key: 'is_active',
        align: 'center',
        render: (activo) => <ActivoTag activo={activo} />,
    },
    {
        title: 'Última ejecución',
        key: 'ultima',
        className: 'celda-fecha',
        render: () => '—',
    },
    {
        key: 'flecha',
        align: 'right',
        width: 48,
        render: () => (
            <span className="celda-flecha">
                <IconFlecha />
            </span>
        ),
    },
]

const NivelClientes = ({ onSeleccionar }) => {
    const [filtros, setFiltros] = useState(FILTROS_VACIOS)
    const busquedaDiferida = useDebounce(filtros.search, 300)

    const { data: clientes, isPending, isError, error, refetch } =
        useClientesEjecuciones({ ...filtros, search: busquedaDiferida })

    const cambiar = (campo) => (nuevo) => setFiltros({ ...filtros, [campo]: nuevo ?? null })

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar la lista de clientes"
                description={mensajeDeError(error)}
                action={<Button size="small" onClick={() => refetch()}>Reintentar</Button>}
            />
        )
    }

    return (
        <>
            <div className="pagina-head">
                <div>
                    <h1 className="pagina-head__titulo">Ejecuciones</h1>
                    <p className="pagina-head__sub">
                        Historial de ejecuciones de los flujos de integración
                    </p>
                </div>
            </div>

            <Space className="ejec-filtros" wrap size={12}>
                <Input
                    className="ejec-filtros__buscador"
                    placeholder="Buscar cliente..."
                    prefix={<IconLupa style={{ color: 'rgba(0,0,0,.3)' }} />}
                    value={filtros.search}
                    onChange={(e) => setFiltros({ ...filtros, search: e.target.value })}
                    allowClear
                />
                <Select
                    className="ejec-filtros__select"
                    placeholder="ERP: todos"
                    value={filtros.erpType}
                    onChange={cambiar('erpType')}
                    options={OPCIONES_ERP}
                    allowClear
                />
                <Select
                    className="ejec-filtros__select ejec-filtros__select--corto"
                    placeholder="Estado: todos"
                    value={filtros.isActive}
                    onChange={cambiar('isActive')}
                    options={[
                        { value: true, label: 'Activo' },
                        { value: false, label: 'Inactivo' },
                    ]}
                    allowClear
                />
            </Space>

            <div className="tarjeta-borde">
                <Table
                    className="tabla-panel tabla-panel--clicable"
                    columns={columnas}
                    dataSource={clientes}
                    rowKey="id"
                    loading={isPending}
                    scroll={{ x: 800 }}
                    onRow={(cliente) => ({
                        onClick: () => onSeleccionar(cliente),
                    })}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: false,
                        showTotal: (total, [desde, hasta]) =>
                            `Mostrando ${desde}-${hasta} de ${total} clientes`,
                    }}
                    locale={{ emptyText: 'Ningún cliente coincide con los filtros' }}
                />
            </div>
        </>
    )
}

export default NivelClientes

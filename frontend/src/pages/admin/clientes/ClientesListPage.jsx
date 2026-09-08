import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, App, Button, Table, Tooltip } from 'antd'
import ActivoTag from '@/components/ActivoTag'
import ErpTag from '@/components/ErpTag'
import { etiquetaErp } from '@/config/erp'
import useHasRole from '@/hooks/useHasRole'
import { useClientes, mensajeDeError } from '@/hooks/useClientes'
import { ROLES } from '@/config/navigation'
import { formatFechaHora } from '@/utils/format'
import FiltrosClientes, { FILTROS_VACIOS } from './components/FiltrosClientes'
import ModalCrearCliente from './components/ModalCrearCliente'
import ModalProbarConexion from './components/ModalProbarConexion'
import { IconFlecha, IconInfo, IconMas } from './icons'
import '@/styles/pagina.css'
import './clientes.css'

const columnas = [
    {
        title: 'ID Cliente',
        dataIndex: 'client_id',
        key: 'client_id',
        width: 150,
        className: 'celda-nombre',
        sorter: (a, b) => a.client_id.localeCompare(b.client_id, 'es'),
    },
    {
        title: 'Nombre',
        dataIndex: 'name',
        key: 'name',
        width: 180,
        className: 'celda-nombre',
        sorter: (a, b) => a.name.localeCompare(b.name, 'es'),
    },
    {
        title: 'ERP',
        dataIndex: 'erp_type',
        key: 'erp_type',
        width: 100,
        align: 'center',
        sorter: (a, b) => etiquetaErp(a.erp_type).localeCompare(etiquetaErp(b.erp_type), 'es'),
        render: (erpType) => <ErpTag erpType={erpType} />,
    },
    {
        title: 'Estado',
        dataIndex: 'is_active',
        key: 'is_active',
        width: 100,
        align: 'center',
        sorter: (a, b) => Number(b.is_active) - Number(a.is_active),
        render: (activo) => <ActivoTag activo={activo} />,
    },
    {
        title: 'Fecha Creación',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 180,
        className: 'celda-fecha',
        sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
        render: (fecha) => formatFechaHora(fecha),
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

const ClientesListPage = () => {
    const navigate = useNavigate()
    const { message } = App.useApp()
    const puedeCrear = useHasRole([ROLES.SUPERADMIN, ROLES.ADMIN])

    const [filtros, setFiltros] = useState(FILTROS_VACIOS)
    const [modalAbierto, setModalAbierto] = useState(false)
    const [modalProbar, setModalProbar] = useState(false)

    const { data: clientes, isPending, isError, error, refetch } =
        useClientes(filtros)

    const opcionesCliente = useMemo(() => {
        if (!clientes) return []
        return clientes.map((c) => ({ value: c.name, label: c.name }))
    }, [clientes])

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar la lista de clientes"
                description={mensajeDeError(error)}
                action={
                    <Button size="small" onClick={() => refetch()}>
                        Reintentar
                    </Button>
                }
            />
        )
    }

    return (
        <>
            <div className="pagina-head">
                <div>
                    <h1 className="pagina-head__titulo">
                        Clientes
                        <Tooltip title="Gestión de empresas clientes conectadas al integrador">
                            <IconInfo className="pagina-head__info" />
                        </Tooltip>
                    </h1>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                    <Button onClick={() => setModalProbar(true)}>
                        Probar conexión
                    </Button>
                    {puedeCrear && (
                        <Button type="primary" icon={<IconMas />} onClick={() => setModalAbierto(true)}>
                            Crear cliente
                        </Button>
                    )}
                </div>
            </div>

            <FiltrosClientes valor={filtros} onChange={setFiltros} opcionesCliente={opcionesCliente} />

            <div className="tarjeta-borde">
                <Table
                    className="tabla-panel tabla-panel--clicable"
                    showSorterTooltip={false}
                    columns={columnas}
                    dataSource={clientes}
                    rowKey="id"
                    loading={isPending}
                    scroll={{ x: 900 }}
                    onRow={(cliente) => ({
                        onClick: () => navigate(`/admin/clientes/${cliente.id}`),
                    })}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: false,
                        // La API no pagina /clients/: devuelve todo y paginamos aquí.
                        showTotal: (total, [desde, hasta]) =>
                            `Mostrando ${desde}-${hasta} de ${total} clientes`,
                    }}
                    locale={{ emptyText: 'Ningún cliente coincide con los filtros' }}
                />
            </div>

            <ModalCrearCliente
                abierto={modalAbierto}
                onCerrar={() => setModalAbierto(false)}
                onCreado={(cliente) => {
                    message.success(`Cliente "${cliente.name}" creado`)
                    navigate(`/admin/clientes/${cliente.id}`)
                }}
            />

            <ModalProbarConexion
                abierto={modalProbar}
                onCerrar={() => setModalProbar(false)}
            />
        </>
    )
}

export default ClientesListPage

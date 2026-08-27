import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, App, Button, Table, Tooltip } from 'antd'
import ActivoTag from '@/components/ActivoTag'
import ErpTag from '@/components/ErpTag'
import { etiquetaErp } from '@/config/erp'
import useHasRole from '@/hooks/useHasRole'
import useDebounce from '@/hooks/useDebounce'
import { useClientes, mensajeDeError } from '@/hooks/useClientes'
import { ROLES } from '@/config/navigation'
import { formatFechaHora } from '@/utils/format'
import FiltrosClientes, { FILTROS_VACIOS } from './components/FiltrosClientes'
import ModalCrearCliente from './components/ModalCrearCliente'
import { IconFlecha, IconInfo, IconMas } from './icons'
import '@/styles/pagina.css'
import './clientes.css'

const columnas = [
    {
        title: 'ID Cliente',
        dataIndex: 'client_id',
        key: 'client_id',
        className: 'celda-nombre',
        sorter: (a, b) => a.client_id.localeCompare(b.client_id, 'es'),
    },
    {
        title: 'Nombre',
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
        sorter: (a, b) => etiquetaErp(a.erp_type).localeCompare(etiquetaErp(b.erp_type), 'es'),
        render: (erpType) => <ErpTag erpType={erpType} />,
    },
    {
        title: 'Estado',
        dataIndex: 'is_active',
        key: 'is_active',
        align: 'center',
        sorter: (a, b) => Number(b.is_active) - Number(a.is_active),
        render: (activo) => <ActivoTag activo={activo} />,
    },
    {
        title: 'Fecha Creación',
        dataIndex: 'created_at',
        key: 'created_at',
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

    // Solo la búsqueda se difiere; los selects disparan de inmediato.
    const busquedaDiferida = useDebounce(filtros.search, 300)
    const { data: clientes, isPending, isError, error, refetch } =
        useClientes({ ...filtros, search: busquedaDiferida })

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

                {puedeCrear && (
                    <Button type="primary" icon={<IconMas />} onClick={() => setModalAbierto(true)}>
                        Crear cliente
                    </Button>
                )}
            </div>

            <FiltrosClientes valor={filtros} onChange={setFiltros} />

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
        </>
    )
}

export default ClientesListPage

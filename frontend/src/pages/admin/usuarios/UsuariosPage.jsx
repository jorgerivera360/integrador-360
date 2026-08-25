import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, App, Button, Input, Select, Space, Table, Tooltip } from 'antd'
import RolBadge from '@/components/RolBadge'
import { useUsuarios } from '@/hooks/useUsuarios'
import useDebounce from '@/hooks/useDebounce'
import { mensajeDeError } from '@/hooks/useClientes'
import { formatDesde, formatFechaHora } from '@/utils/format'
import ModalCrearUsuario from './components/ModalCrearUsuario'
import { IconFlecha, IconInfo, IconMas } from './icons'
import '@/styles/pagina.css'
import './usuarios.css'

const EstadoUsuario = ({ activo }) => (
    <span className={`estado-punto estado-punto--${activo ? 'activo' : 'inactivo'}`}>
        <span className="estado-punto__marca" />
        {activo ? 'Activo' : 'Inactivo'}
    </span>
)

const FILTROS_VACIOS = { search: '', role: null, isActive: null }

const columnas = [
    {
        title: 'Nombre',
        dataIndex: 'name',
        key: 'name',
        className: 'celda-nombre',
        sorter: (a, b) => a.name.localeCompare(b.name, 'es'),
    },
    {
        title: 'Email',
        dataIndex: 'email',
        key: 'email',
        className: 'celda-tenue',
        sorter: (a, b) => a.email.localeCompare(b.email, 'es'),
    },
    {
        title: 'Rol',
        dataIndex: 'role',
        key: 'role',
        align: 'center',
        sorter: (a, b) => a.role.localeCompare(b.role, 'es'),
        render: (rol) => <RolBadge rol={rol} />,
    },
    {
        title: 'Estado',
        dataIndex: 'is_active',
        key: 'is_active',
        align: 'center',
        sorter: (a, b) => Number(b.is_active) - Number(a.is_active),
        render: (activo) => <EstadoUsuario activo={activo} />,
    },
    {
        title: 'Último acceso',
        dataIndex: 'last_login',
        key: 'last_login',
        className: 'celda-tenue',
        sorter: (a, b) => new Date(a.last_login || 0) - new Date(b.last_login || 0),
        render: (fecha) =>
            fecha ? (
                <span title={formatFechaHora(fecha)}>{formatDesde(fecha)}</span>
            ) : (
                <span className="celda-nunca">Nunca</span>
            ),
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

const UsuariosPage = () => {
    const navigate = useNavigate()
    const { message } = App.useApp()

    const [filtros, setFiltros] = useState(FILTROS_VACIOS)
    const [modalAbierto, setModalAbierto] = useState(false)

    const busquedaDiferida = useDebounce(filtros.search, 300)
    const { data: usuarios, isPending, isError, error, refetch } =
        useUsuarios({ ...filtros, search: busquedaDiferida })

    if (isError) {
        return (
            <Alert
                type="error"
                showIcon
                message="No se pudo cargar la lista de usuarios"
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
                        Usuarios
                        <Tooltip title="Administración de usuarios del panel. Solo accesible para superadministradores.">
                            <IconInfo className="pagina-head__info" />
                        </Tooltip>
                    </h1>
                </div>

                <Button type="primary" icon={<IconMas />} onClick={() => setModalAbierto(true)}>
                    Crear usuario
                </Button>
            </div>

            <Space className="usuarios-filtros" wrap size={8}>
                <Input
                    className="usuarios-filtros__buscador"
                    placeholder="Buscar por nombre o email..."
                    value={filtros.search}
                    onChange={(e) => setFiltros({ ...filtros, search: e.target.value })}
                    allowClear
                />
                <Select
                    className="usuarios-filtros__select"
                    placeholder="Rol: todos"
                    value={filtros.role}
                    onChange={(valor) => setFiltros({ ...filtros, role: valor ?? null })}
                    options={[
                        { value: 'superadmin', label: 'Superadmin' },
                        { value: 'admin', label: 'Admin' },
                        { value: 'viewer', label: 'Viewer' },
                    ]}
                    allowClear
                />
                <Select
                    className="usuarios-filtros__select"
                    placeholder="Estado: todos"
                    value={filtros.isActive}
                    onChange={(valor) => setFiltros({ ...filtros, isActive: valor ?? null })}
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
                    dataSource={usuarios}
                    rowKey="id"
                    loading={isPending}
                    scroll={{ x: 860 }}
                    onRow={(usuario) => ({
                        onClick: () => navigate(`/admin/usuarios/${usuario.id}`),
                    })}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: false,
                        // La API no pagina /users/: devuelve todo y paginamos aquí.
                        showTotal: (total, [desde, hasta]) =>
                            `Mostrando ${desde}-${hasta} de ${total} usuarios`,
                    }}
                    locale={{ emptyText: 'Ningún usuario coincide con el filtro' }}
                />
            </div>

            <ModalCrearUsuario
                abierto={modalAbierto}
                onCerrar={() => setModalAbierto(false)}
                onCreado={(usuario) => {
                    message.success(`Usuario "${usuario.name}" creado`)
                    navigate(`/admin/usuarios/${usuario.id}`)
                }}
            />
        </>
    )
}

export default UsuariosPage

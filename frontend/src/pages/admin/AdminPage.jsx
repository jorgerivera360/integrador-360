import { useNavigate } from 'react-router-dom'
import { IconClientes, IconUsuarios, IconConfigSQL, IconCamposWms } from '@/layouts/icons'
import useAuthStore from '@/store/authStore'
import { ROLES } from '@/config/roles'
import './admin.css'

const SECCIONES = [
    {
        key: 'clientes',
        titulo: 'Clientes',
        descripcion: 'Gestionar clientes, credenciales y contenedores',
        path: '/admin/clientes',
        icono: IconClientes,
        color: '#1677ff',
        roles: [ROLES.SUPERADMIN, ROLES.ADMIN, ROLES.VIEWER],
    },
    {
        key: 'usuarios',
        titulo: 'Usuarios',
        descripcion: 'Administrar usuarios y roles del sistema',
        path: '/admin/usuarios',
        icono: IconUsuarios,
        color: '#52c41a',
        roles: [ROLES.SUPERADMIN],
    },
    {
        key: 'config-sql',
        titulo: 'Config SQL',
        descripcion: 'Bloques SQL reutilizables para flujos SIESA',
        path: '/admin/config-sql',
        icono: IconConfigSQL,
        color: '#fa8c16',
        roles: [ROLES.SUPERADMIN, ROLES.ADMIN],
    },
    {
        key: 'campos-wms',
        titulo: 'Campos WMS',
        descripcion: 'Mapeo de campos del ERP hacia modelos de Odoo WMS',
        path: '/admin/campos-wms',
        icono: IconCamposWms,
        color: '#722ed1',
        roles: [ROLES.SUPERADMIN, ROLES.ADMIN],
    },
]

const AdminPage = () => {
    const navigate = useNavigate()
    const role = useAuthStore((state) => state.role)

    const visibles = SECCIONES.filter((s) => s.roles.includes(role))

    return (
        <div className="admin-page">
            <div className="pagina-head">
                <h1>Administraci&oacute;n</h1>
                <p className="pagina-head__sub">
                    Configuraci&oacute;n general del sistema
                </p>
            </div>

            <div className="admin-tarjetas">
                {visibles.map((sec) => {
                    const Icono = sec.icono
                    return (
                        <button
                            key={sec.key}
                            className="flujo-tarjeta"
                            style={{ borderLeftColor: sec.color }}
                            onClick={() => navigate(sec.path)}
                        >
                            <div
                                className="flujo-tarjeta__icono"
                                style={{ color: sec.color }}
                            >
                                <Icono />
                            </div>
                            <div className="flujo-tarjeta__texto">
                                <span className="flujo-tarjeta__titulo">
                                    {sec.titulo}
                                </span>
                                <span className="flujo-tarjeta__conteo">
                                    {sec.descripcion}
                                </span>
                            </div>
                        </button>
                    )
                })}
            </div>
        </div>
    )
}

export default AdminPage

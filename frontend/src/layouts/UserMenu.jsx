import { useNavigate } from 'react-router-dom'
import { Dropdown } from 'antd'
import { IconRueda, IconSalir } from '@/layouts/icons'
import RolBadge from '@/components/RolBadge'
import useAuthStore from '@/store/authStore'

const UserMenu = () => {
    const navigate = useNavigate()
    const user = useAuthStore((state) => state.user)
    const role = useAuthStore((state) => state.role)
    const clearAuth = useAuthStore((state) => state.clearAuth)

    const cerrarSesion = () => {
        clearAuth()
        navigate('/login', { replace: true })
    }

    const items = [
        {
            key: 'correo',
            type: 'group',
            label: <div className="dropdown__correo">{user?.email}</div>,
        },
        {
            key: 'salir',
            icon: <IconSalir />,
            label: 'Cerrar sesión',
            onClick: cerrarSesion,
        },
    ]

    return (
        <div className="usuario">
            <span className="usuario__nombre">{user?.name}</span>

            <RolBadge rol={role} />

            <Dropdown menu={{ items }} trigger={['click']} placement="bottomRight">
                <button type="button" className="usuario__rueda" title="Opciones" aria-label="Opciones de usuario">
                    <IconRueda />
                </button>
            </Dropdown>
        </div>
    )
}

export default UserMenu

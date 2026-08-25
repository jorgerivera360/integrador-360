import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import { NAV_ITEMS, filterNavByRole, resolveNav } from '@/config/navigation'
import useAuthStore from '@/store/authStore'
import useUiStore from '@/store/uiStore'
import logoCompleto from '@/assets/logo-360-claro.png'
import logoMarca from '@/assets/logo-360-marca.png'

const { Sider } = Layout

/** Convierte el árbol de navegación al formato que espera Menu de antd. */
function aItemsAntd(items) {
    return items.map((item) => {
        const Icono = item.icon
        return {
            key: item.key,
            icon: Icono ? <Icono /> : undefined,
            label: item.label,
            children: item.children ? aItemsAntd(item.children) : undefined,
        }
    })
}

/** Mapa key → path, para resolver la navegación al hacer clic. */
function aMapaDeRutas(items, mapa = new Map()) {
    items.forEach((item) => {
        if (item.path) mapa.set(item.key, item.path)
        if (item.children) aMapaDeRutas(item.children, mapa)
    })
    return mapa
}

const Sidebar = () => {
    const navigate = useNavigate()
    const { pathname } = useLocation()
    const role = useAuthStore((state) => state.role)
    const colapsado = useUiStore((state) => state.sidebarColapsado)
    const toggleSidebar = useUiStore((state) => state.toggleSidebar)

    const visibles = useMemo(() => filterNavByRole(NAV_ITEMS, role), [role])
    const items = useMemo(() => aItemsAntd(visibles), [visibles])
    const rutas = useMemo(() => aMapaDeRutas(visibles), [visibles])

    const nav = resolveNav(pathname)
    const seleccionado = nav ? [nav.item.key] : []

    // El submenú del padre se abre solo al entrar por una ruta suya
    // (link directo o recarga), y luego el usuario puede abrir/cerrar libre.
    const [openKeys, setOpenKeys] = useState(nav?.padre ? [nav.padre.key] : [])
    const padreKey = nav?.padre?.key

    useEffect(() => {
        if (!padreKey) return
        setOpenKeys((previas) =>
            previas.includes(padreKey) ? previas : [...previas, padreKey]
        )
    }, [padreKey])

    const alHacerClic = ({ key }) => {
        const path = rutas.get(key)
        if (path && path !== pathname) {
            navigate(path)
        }
    }

    return (
        <Sider
            className="app-sider"
            width={240}
            collapsedWidth={80}
            collapsible
            collapsed={colapsado}
            trigger={null}
            breakpoint="lg"
            onBreakpoint={(esAngosto) => esAngosto && useUiStore.getState().setSidebarColapsado(true)}
        >
            <div className="sidebar__marca">
                <img
                    src={colapsado ? logoMarca : logoCompleto}
                    alt="360 Software"
                />
            </div>

            <Menu
                className="sidebar__menu"
                theme="dark"
                mode="inline"
                items={items}
                selectedKeys={seleccionado}
                openKeys={colapsado ? [] : openKeys}
                onOpenChange={setOpenKeys}
                onClick={alHacerClic}
            />

            <button
                type="button"
                className="sidebar__colapsar"
                onClick={toggleSidebar}
                title={colapsado ? 'Expandir' : 'Colapsar'}
                aria-label={colapsado ? 'Expandir menú' : 'Colapsar menú'}
            >
                {colapsado ? '→' : '←'}
            </button>
        </Sider>
    )
}

export default Sidebar

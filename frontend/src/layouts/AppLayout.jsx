import { Layout } from 'antd'
import { Outlet } from 'react-router-dom'
import Sidebar from '@/layouts/Sidebar'
import HeaderBar from '@/layouts/HeaderBar'
import { BreadcrumbProvider } from '@/layouts/BreadcrumbContext'
import './layout.css'

/**
 * Shell de la aplicación: sidebar + header + contenido.
 * Se monta una sola vez; al navegar solo cambia lo que renderiza <Outlet />.
 */
const AppLayout = () => (
    <BreadcrumbProvider>
        <Layout className="app-layout">
            <Sidebar />
            <Layout>
                <HeaderBar />
                <Layout.Content className="app-contenido">
                    <Outlet />
                </Layout.Content>
            </Layout>
        </Layout>
    </BreadcrumbProvider>
)

export default AppLayout

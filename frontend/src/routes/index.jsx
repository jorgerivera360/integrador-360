import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import AppLayout from '@/layouts/AppLayout'
import { ROLES, RUTA_INICIAL } from '@/config/navigation'

import LoginPage from '@/pages/LoginPage'
import TableroPage from '@/pages/tablero/TableroPage'
import FlujosPage from '@/pages/flujos/FlujosPage'
import EjecucionesPage from '@/pages/ejecuciones/EjecucionesPage'
import AuditoriaPage from '@/pages/auditoria/AuditoriaPage'
import ClientesListPage from '@/pages/admin/clientes/ClientesListPage'
import ClienteDetallePage from '@/pages/admin/clientes/ClienteDetallePage'
import UsuariosPage from '@/pages/admin/usuarios/UsuariosPage'
import UsuarioDetallePage from '@/pages/admin/usuarios/UsuarioDetallePage'
import NotFoundPage from '@/pages/NotFoundPage'

/**
 * Árbol de rutas.
 *
 * Todo lo autenticado cuelga de una ruta de layout: el shell se monta una
 * vez y solo cambia el <Outlet />. Las restricciones por rol repiten aquí
 * lo que declara navigation.jsx, porque ocultar el ítem del menú no impide
 * entrar por URL directa.
 */
const AppRoutes = () => (
    <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
            element={
                <ProtectedRoute>
                    <AppLayout />
                </ProtectedRoute>
            }
        >
            <Route path="/tablero" element={<TableroPage />} />
            <Route path="/flujos" element={<FlujosPage />} />
            <Route path="/ejecuciones" element={<EjecucionesPage />} />
            <Route path="/auditoria" element={<AuditoriaPage />} />

            <Route path="/admin/clientes" element={<ClientesListPage />} />
            <Route path="/admin/clientes/:id" element={<ClienteDetallePage />} />
            <Route
                path="/admin/usuarios"
                element={
                    <ProtectedRoute roles={[ROLES.SUPERADMIN]}>
                        <UsuariosPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/usuarios/:id"
                element={
                    <ProtectedRoute roles={[ROLES.SUPERADMIN]}>
                        <UsuarioDetallePage />
                    </ProtectedRoute>
                }
            />

            <Route path="*" element={<NotFoundPage />} />
        </Route>

        <Route path="/" element={<Navigate to={RUTA_INICIAL} replace />} />
    </Routes>
)

export default AppRoutes

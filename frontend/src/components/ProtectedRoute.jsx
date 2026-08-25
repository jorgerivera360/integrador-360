import { Navigate, useLocation } from 'react-router-dom'
import useAuthStore from '@/store/authStore'
import { RUTA_INICIAL } from '@/config/navigation'

/**
 * Guarda de ruta.
 * - Sin token → al login, recordando a dónde iba para volver después.
 * - Con token pero sin el rol requerido → a la ruta inicial.
 */
const ProtectedRoute = ({ children, roles }) => {
    const location = useLocation()
    const token = useAuthStore((state) => state.token)
    const role = useAuthStore((state) => state.role)

    if (!token) {
        return <Navigate to="/login" replace state={{ desde: location.pathname }} />
    }

    if (roles && !roles.includes(role)) {
        return <Navigate to={RUTA_INICIAL} replace />
    }

    return children
}

export default ProtectedRoute

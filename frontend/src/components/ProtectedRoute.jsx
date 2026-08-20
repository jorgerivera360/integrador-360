import { Navigate } from 'react-router-dom'
import useAuthStore from '@/store/authStore'

const ProtectedRoute = ({ children, roles }) => {
    const token = useAuthStore((state) => state.token)
    const role = useAuthStore((state) => state.role)

    if (!token) {
        return <Navigate to="/login" replace />
    }

    if (roles && !roles.includes(role)) {
        return <Navigate to="/tablero" replace />
    }

    return children
}

export default ProtectedRoute
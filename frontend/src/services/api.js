import axios from 'axios'
import useAuthStore from '@/store/authStore'

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Antes de cada request: agrega el token desde el store
api.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Después de cada response: si es 401, limpia la sesión y manda al login
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            useAuthStore.getState().clearAuth()

            // Si ya estamos en /login no redirigimos: recargar borraría el
            // mensaje de error del propio intento de inicio de sesión.
            if (window.location.pathname !== '/login') {
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

export default api

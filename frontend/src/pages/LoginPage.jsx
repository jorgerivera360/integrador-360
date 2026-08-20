import { useNavigate } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { message } from 'antd'
import { loginWithGoogle } from '@/services/auth'
import useAuthStore from '@/store/authStore'

const LoginPage = () => {
    const navigate = useNavigate()
    const setAuth = useAuthStore((state) => state.setAuth)
    const token = useAuthStore((state) => state.token)

    if (token) {
        navigate('/tablero', { replace: true })
        return null
    }

    const handleSuccess = async (credentialResponse) => {
        try {
            const response = await loginWithGoogle(credentialResponse.credential)
            const { access_token, user } = response.data
            setAuth(user, access_token)
            message.success(`Bienvenido, ${user.name}`)
            navigate('/tablero')
        } catch (error) {
            const msg = error.response?.data?.detail || 'Error al iniciar sesión'
            message.error(msg)
        }
    }

    const handleError = () => {
        message.error('Error con Google. Intenta de nuevo.')
    }

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            backgroundColor: '#f0f2f5',
        }}>
            <div style={{
                textAlign: 'center',
                padding: '48px',
                backgroundColor: '#fff',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
            }}>
                <h1 style={{ marginBottom: '8px', color: '#1890ff' }}>
                    Integrador 360
                </h1>
                <p style={{ marginBottom: '32px', color: '#666' }}>
                    Inicia sesión con tu cuenta de 360 Software
                </p>
                <GoogleLogin
                    onSuccess={handleSuccess}
                    onError={handleError}
                    theme="outline"
                    size="large"
                    text="signin_with"
                    locale="es"
                />
            </div>
        </div>
    )
}

export default LoginPage
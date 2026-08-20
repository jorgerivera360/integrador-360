import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import { message } from 'antd'
import { loginWithGoogle } from '@/services/auth'
import useAuthStore from '@/store/authStore'
import logo from '@/assets/logo-360.png'
import './login.css'

const LoginPage = () => {
    const navigate = useNavigate()
    const setAuth = useAuthStore((state) => state.setAuth)
    const token = useAuthStore((state) => state.token)

    const [docs, setDocs] = useState('1.284')
    const [integraciones, setIntegraciones] = useState(6)
    const [segundos, setSegundos] = useState(8)

    useEffect(() => {
        if (token) {
            navigate('/tablero', { replace: true })
        }
    }, [token, navigate])

    useEffect(() => {
        const interval = setInterval(() => {
            setDocs((900 + Math.floor(Math.random() * 3200)).toLocaleString('es-CO'))
            setIntegraciones(3 + Math.floor(Math.random() * 12))
            setSegundos(1 + Math.floor(Math.random() * 59))
        }, 2000)
        return () => clearInterval(interval)
    }, [])

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

    if (token) return null

    return (
        <main className="login">
            <section className="panel-visual">
                <div className="halo halo-1" />
                <div className="halo halo-2" />

                <div className="panel-visual__contenido">
                    <div className="esquema">
                        <svg viewBox="0 0 620 300" aria-label="ERP conectado con WMS a través del Integrador 360">
                            <defs>
                                <linearGradient id="plate" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="rgba(255,255,255,.10)" />
                                    <stop offset="100%" stopColor="rgba(255,255,255,.03)" />
                                </linearGradient>
                            </defs>

                            <rect x="14" y="86" width="96" height="128" rx="16" fill="url(#plate)" stroke="rgba(160,200,255,.30)" />
                            <g fill="rgba(180,215,255,.5)">
                                <rect x="38" y="112" width="48" height="7" rx="3.5" />
                                <rect x="38" y="127" width="48" height="7" rx="3.5" opacity=".6" />
                                <rect x="38" y="142" width="30" height="7" rx="3.5" opacity=".35" />
                            </g>
                            <text x="62" y="184" textAnchor="middle" fill="rgba(255,255,255,.78)" fontFamily="Inter, sans-serif" fontSize="15" fontWeight="600" letterSpacing="1.6">ERP</text>

                            <rect x="510" y="86" width="96" height="128" rx="16" fill="url(#plate)" stroke="rgba(160,200,255,.30)" />
                            <g fill="rgba(180,215,255,.5)">
                                <rect x="534" y="112" width="48" height="7" rx="3.5" opacity=".35" />
                                <rect x="534" y="127" width="48" height="7" rx="3.5" opacity=".6" />
                                <rect x="534" y="142" width="30" height="7" rx="3.5" />
                            </g>
                            <text x="558" y="184" textAnchor="middle" fill="rgba(255,255,255,.78)" fontFamily="Inter, sans-serif" fontSize="15" fontWeight="600" letterSpacing="1.6">WMS</text>

                            <g stroke="rgba(150,195,255,.22)" strokeWidth="1.4" fill="none">
                                <path d="M110 112 C 195 112, 205 150, 262 150" />
                                <path d="M110 150 L262 150" />
                                <path d="M110 188 C 195 188, 205 150, 262 150" />
                                <path d="M358 150 C 415 150, 425 112, 510 112" />
                                <path d="M358 150 L510 150" />
                                <path d="M358 150 C 415 150, 425 188, 510 188" />
                            </g>

                            <g className="flujo" stroke="#4cc9f0" strokeWidth="2.2" fill="none" strokeLinecap="round" strokeDasharray="26 400" strokeDashoffset="426">
                                <path d="M110 112 C 195 112, 205 150, 262 150" />
                                <path d="M110 150 L262 150" />
                                <path d="M110 188 C 195 188, 205 150, 262 150" />
                            </g>

                            <g className="flujo flujo--salida" stroke="#7bdff2" strokeWidth="2.2" fill="none" strokeLinecap="round" strokeDasharray="26 400" strokeDashoffset="426">
                                <path d="M358 150 C 415 150, 425 112, 510 112" />
                                <path d="M358 150 L510 150" />
                                <path d="M358 150 C 415 150, 425 188, 510 188" />
                            </g>

                            <g className="orbita">
                                <circle cx="310" cy="150" r="74" fill="none" stroke="rgba(160,200,255,.16)" strokeWidth="1.2" strokeDasharray="4 12" />
                            </g>
                            <rect className="hub" x="262" y="102" width="96" height="96" rx="28" fill="rgba(76,201,240,.10)" stroke="rgba(76,201,240,.55)" strokeWidth="1.6" />
                            <text x="310" y="140" textAnchor="middle" fill="rgba(234,246,255,.62)" fontFamily="Inter, sans-serif" fontSize="9" fontWeight="600" letterSpacing="1.6">INTEGRADOR</text>
                            <text x="310" y="172" textAnchor="middle" fill="#eaf6ff" fontFamily="Inter, sans-serif" fontSize="28" fontWeight="700">360</text>
                        </svg>

                        <div className="metricas">
                            <div className="metricas__item">
                                <span className="metricas__valor">{docs}</span>
                                <span className="metricas__etiqueta">documentos sincronizados hoy</span>
                            </div>
                            <div className="metricas__sep" />
                            <div className="metricas__item">
                                <span className="metricas__valor">{integraciones}</span>
                                <span className="metricas__etiqueta">integraciones activas</span>
                            </div>
                            <div className="metricas__sep" />
                            <div className="metricas__item">
                                <span className="metricas__valor">
                                    <span className="punto-estado" />
                                    En línea
                                </span>
                                <span className="metricas__etiqueta">última corrida hace {segundos}&nbsp;s</span>
                            </div>
                        </div>
                    </div>

                </div>

                <div className="titular">
                    <h1>Integrador 360</h1>
                    <p>Plataforma interna de integración entre sistemas</p>
                </div>
            </section>

            <section className="panel-acceso">
                <div />

                <div className="panel-acceso__centro">
                    <img className="logo" src={logo} alt="360 Software" />
                    <h2>Bienvenido</h2>
                    <p className="panel-acceso__sub">Inicia sesión con tu cuenta corporativa</p>

                    <div className="google-login-wrapper">
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

                <p className="pie">© 360 Software — v1.0.0</p>
            </section>
        </main>
    )
}

export default LoginPage
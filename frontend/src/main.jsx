import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { App as AntdApp, ConfigProvider } from 'antd'
import esES from 'antd/locale/es_ES'
import dayjs from 'dayjs'
import 'dayjs/locale/es'
import App from './App'

// Los selectores de fecha de antd usan dayjs por dentro: sin esto los
// nombres de meses y días salen en inglés aunque el locale de antd sea es.
dayjs.locale('es')

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
})

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

// Paleta tomada del mockup panel.html. Coincide con la de Ant Design v4,
// por eso se fija colorPrimary en #1890ff y no en el #1677ff de la v5.
const tema = {
    token: {
        colorPrimary: '#1890ff',
        fontFamily: 'Inter, "Segoe UI", system-ui, sans-serif',
    },
    components: {
        Layout: {
            siderBg: '#001529',
            headerBg: '#ffffff',
            bodyBg: '#f0f2f5',
        },
        Menu: {
            darkItemBg: '#001529',
            darkSubMenuItemBg: '#000c17',
            darkItemColor: 'rgba(255,255,255,.72)',
            darkItemHoverBg: 'rgba(255,255,255,.10)',
            darkItemHoverColor: '#ffffff',
            darkItemSelectedBg: 'rgba(24,144,255,.20)',
            darkItemSelectedColor: '#ffffff',
            itemHeight: 44,
            itemMarginInline: 0,
        },
    },
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <GoogleOAuthProvider clientId={googleClientId}>
            <QueryClientProvider client={queryClient}>
                <ConfigProvider locale={esES} theme={tema}>
                    {/* component={false} evita un div extra: el layout depende
                        de que el árbol conserve su altura completa. */}
                    <AntdApp component={false}>
                        <BrowserRouter>
                            <App />
                        </BrowserRouter>
                    </AntdApp>
                </ConfigProvider>
            </QueryClientProvider>
        </GoogleOAuthProvider>
    </React.StrictMode>
)

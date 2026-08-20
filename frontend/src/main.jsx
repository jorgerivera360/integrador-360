import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { ConfigProvider } from 'antd'
import esES from 'antd/locale/es_ES'
import App from './App'

const queryClient = new QueryClient({
defaultOptions: {
    queries: {
    retry: 1,
    refetchOnWindowFocus: false,
    },
},
})

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

ReactDOM.createRoot(document.getElementById('root')).render(
<React.StrictMode>
    <GoogleOAuthProvider clientId={googleClientId}>
    <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={esES}>
        <BrowserRouter>
            <App />
        </BrowserRouter>
        </ConfigProvider>
    </QueryClientProvider>
    </GoogleOAuthProvider>
</React.StrictMode>
)
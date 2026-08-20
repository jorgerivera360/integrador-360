import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'

function App() {
    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
                path="/tablero"
                element={
                    <ProtectedRoute>
                        <div>Tablero — próximamente</div>
                    </ProtectedRoute>
                }
            />
            <Route path="/" element={<Navigate to="/tablero" replace />} />
            <Route path="*" element={<div>Página no encontrada</div>} />
        </Routes>
    )
}

export default App
import { useNavigate } from 'react-router-dom'
import { Button, Result } from 'antd'
import { RUTA_INICIAL } from '@/config/navigation'

const NotFoundPage = () => {
    const navigate = useNavigate()

    return (
        <Result
            status="404"
            title="404"
            subTitle="La página que buscas no existe."
            extra={
                <Button type="primary" onClick={() => navigate(RUTA_INICIAL)}>
                    Ir al tablero
                </Button>
            }
            style={{ background: '#fff', borderRadius: 8, padding: '48px 24px' }}
        />
    )
}

export default NotFoundPage

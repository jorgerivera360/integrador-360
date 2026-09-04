import { useNavigate } from 'react-router-dom'

const Flecha = () => (
    <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M15 6l-6 6 6 6" />
    </svg>
)

const BotonVolver = ({ to, onClick }) => {
    const navigate = useNavigate()

    const handleClick = () => {
        if (onClick) onClick()
        else if (to) navigate(to)
        else navigate(-1)
    }

    return (
        <button className="btn-volver" onClick={handleClick}>
            <Flecha /> Volver
        </button>
    )
}

export default BotonVolver

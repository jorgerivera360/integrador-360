import { useEffect, useState } from 'react'

/**
 * Difiere un valor hasta que deja de cambiar durante `ms`.
 * Para búsquedas contra el servidor: evita una petición por tecla.
 */
export default function useDebounce(valor, ms = 300) {
    const [diferido, setDiferido] = useState(valor)

    useEffect(() => {
        const temporizador = setTimeout(() => setDiferido(valor), ms)
        return () => clearTimeout(temporizador)
    }, [valor, ms])

    return diferido
}

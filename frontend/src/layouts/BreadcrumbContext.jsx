import { createContext, useContext, useEffect, useMemo, useState } from 'react'

/**
 * Migas de pan de nivel profundo.
 *
 * Los dos primeros niveles se derivan de la URL en navigation.jsx. Este
 * contexto solo aporta el último tramo cuando depende de un dato que hay
 * que cargar —el nombre de un cliente, de un flujo— y que la ruta no sabe.
 *
 * Es contexto y no store global a propósito: es estado de presentación del
 * layout, muere con él y no debería sobrevivir a una recarga.
 */
const BreadcrumbContext = createContext({ extra: null, setExtra: () => {} })

export const BreadcrumbProvider = ({ children }) => {
    const [extra, setExtra] = useState(null)
    const valor = useMemo(() => ({ extra, setExtra }), [extra])

    return <BreadcrumbContext.Provider value={valor}>{children}</BreadcrumbContext.Provider>
}

/** Lo consume el header. */
export function useBreadcrumbExtra() {
    return useContext(BreadcrumbContext).extra
}

/**
 * Lo usa una página de detalle: añade un tramo final y lo retira al salir.
 * Pasar null mientras el dato carga deja el breadcrumb en su nivel base.
 */
export function useSetBreadcrumb(label) {
    const { setExtra } = useContext(BreadcrumbContext)

    useEffect(() => {
        setExtra(label || null)
        return () => setExtra(null)
    }, [label, setExtra])
}

export default BreadcrumbContext

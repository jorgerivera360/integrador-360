import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

/**
 * Migas de pan de nivel profundo.
 *
 * Los dos primeros niveles se derivan de la URL en navigation.jsx. Este
 * contexto aporta tramos extra cuando dependen de un dato que hay que
 * cargar —el nombre de un cliente, de un flujo— y que la ruta no sabe.
 *
 * Además guarda un callback `onNavigate(indice)` para que el header pueda
 * disparar la navegación interna de páginas como Flujos/Ejecuciones que
 * no usan rutas sino estado interno.
 */
const BreadcrumbContext = createContext({
    extra: null,
    onNavigate: null,
    setExtra: () => {},
    setOnNavigate: () => {},
})

export const BreadcrumbProvider = ({ children }) => {
    const [extra, setExtra] = useState(null)
    const [onNavigate, setOnNavigate] = useState(null)
    const valor = useMemo(
        () => ({ extra, onNavigate, setExtra, setOnNavigate }),
        [extra, onNavigate]
    )

    return <BreadcrumbContext.Provider value={valor}>{children}</BreadcrumbContext.Provider>
}

/** Lo consume el header: labels + callback de navegación. */
export function useBreadcrumbExtra() {
    const { extra, onNavigate } = useContext(BreadcrumbContext)
    return { extra, onNavigate }
}

/**
 * Lo usa una página: añade tramos finales y opcionalmente un callback
 * para navegación por click en los tramos intermedios.
 *
 * @param {string|string[]|null} label  - tramo(s) extra
 * @param {function|null} onNav         - callback(indiceExtra) al clickear un tramo extra
 */
export function useSetBreadcrumb(label, onNav) {
    const { setExtra, setOnNavigate } = useContext(BreadcrumbContext)
    const key = label == null ? '' : Array.isArray(label) ? label.join('\0') : label
    const onNavRef = useRef(onNav)
    onNavRef.current = onNav

    const stableNav = useCallback((...args) => onNavRef.current?.(...args), [])

    useEffect(() => {
        if (!label) {
            setExtra(null)
            setOnNavigate(null)
        } else {
            setExtra(Array.isArray(label) ? label : [label])
            setOnNavigate(onNav ? () => stableNav : null)
        }
        return () => { setExtra(null); setOnNavigate(null) }
    }, [key, setExtra, setOnNavigate, !!onNav])
}

export default BreadcrumbContext

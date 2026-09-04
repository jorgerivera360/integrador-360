import { Fragment } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { resolveBreadcrumb, resolveNav } from '@/config/navigation'
import { useBreadcrumbExtra } from '@/layouts/BreadcrumbContext'
import UserMenu from '@/layouts/UserMenu'

/**
 * Header del shell.
 * Las migas se derivan de la URL, no de un click: así un link directo o
 * una recarga muestran la ruta correcta. El último tramo puede venir de
 * una página de detalle a través de BreadcrumbContext.
 */
const HeaderBar = () => {
    const { pathname } = useLocation()
    const base = resolveBreadcrumb(pathname)
    const { extra, onNavigate } = useBreadcrumbExtra()
    const nav = resolveNav(pathname)

    const extras = extra ? (Array.isArray(extra) ? extra : [extra]) : []
    const migas = [...base, ...extras]

    const tieneExtras = extras.length > 0
    const rutaSeccion = tieneExtras ? nav?.item?.path : null

    return (
        <header className="app-header">
            <div className="breadcrumb">
                <span>Integrador 360</span>
                {migas.map((miga, indice) => {
                    const esUltima = indice === migas.length - 1
                    if (esUltima) {
                        return (
                            <Fragment key={`${miga}-${indice}`}>
                                <span className="breadcrumb__sep">/</span>
                                <span className="breadcrumb__actual">{miga}</span>
                            </Fragment>
                        )
                    }

                    // Todos los tramos no-últimos son clickeables.
                    // Si la página registró onNavigate → callback con índice.
                    // Si no (admin con rutas reales) → Link a la ruta base.
                    const esBase = indice < base.length
                    const handleClick = onNavigate
                        ? () => onNavigate(esBase ? -1 : indice - base.length)
                        : null

                    return (
                        <Fragment key={`${miga}-${indice}`}>
                            <span className="breadcrumb__sep">/</span>
                            {handleClick ? (
                                <a className="breadcrumb__link" onClick={handleClick}>
                                    {miga}
                                </a>
                            ) : rutaSeccion && esBase ? (
                                <Link to={rutaSeccion}>{miga}</Link>
                            ) : (
                                <span>{miga}</span>
                            )}
                        </Fragment>
                    )
                })}
            </div>

            <UserMenu />
        </header>
    )
}

export default HeaderBar

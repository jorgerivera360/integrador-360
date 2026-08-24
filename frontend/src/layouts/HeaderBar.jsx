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
    const extra = useBreadcrumbExtra()
    const nav = resolveNav(pathname)

    const migas = extra ? [...base, extra] : base

    // Con un tramo extra, la sección deja de ser el final y pasa a ser un
    // enlace de vuelta a su listado.
    const rutaSeccion = extra ? nav?.item?.path : null

    return (
        <header className="app-header">
            <div className="breadcrumb">
                <span>Integrador 360</span>
                {migas.map((miga, indice) => {
                    const esUltima = indice === migas.length - 1
                    const esSeccion = Boolean(rutaSeccion) && indice === migas.length - 2

                    return (
                        <Fragment key={`${miga}-${indice}`}>
                            <span className="breadcrumb__sep">/</span>
                            {esSeccion ? (
                                <Link to={rutaSeccion}>{miga}</Link>
                            ) : (
                                <span className={esUltima ? 'breadcrumb__actual' : undefined}>
                                    {miga}
                                </span>
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

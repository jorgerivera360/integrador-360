import { useCallback, useState } from 'react'
import { useSetBreadcrumb } from '@/layouts/BreadcrumbContext'
import NivelClientes from './components/NivelClientes'
import NivelCategorias from './components/NivelCategorias'
import NivelFlows from './components/NivelFlows'
import NivelHistorial from './components/NivelHistorial'
import '@/styles/pagina.css'
import './ejecuciones.css'

const TITULOS_TIPO = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Entrada',
    sales: 'Salida',
}

const EjecucionesPage = () => {
    const [nivel, setNivel] = useState(1)
    const [cliente, setCliente] = useState(null)
    const [flowType, setFlowType] = useState(null)
    const [flow, setFlow] = useState(null)

    const breadcrumb = nivel === 1 ? null
        : nivel === 2 ? [cliente?.name]
        : nivel === 3 ? [cliente?.name, TITULOS_TIPO[flowType] || flowType]
        : [cliente?.name, TITULOS_TIPO[flowType] || flowType, flow?.flow_name]

    const navegarBreadcrumb = useCallback((indiceExtra) => {
        if (indiceExtra === -1) {
            setCliente(null); setFlowType(null); setFlow(null)
            setNivel(1)
            return
        }
        const nivelDestino = indiceExtra + 2
        if (nivelDestino <= nivel) {
            if (nivelDestino <= 2) { setFlowType(null) }
            if (nivelDestino <= 3) { setFlow(null) }
            setNivel(nivelDestino)
        }
    }, [nivel])

    useSetBreadcrumb(breadcrumb, breadcrumb ? navegarBreadcrumb : null)

    const irACliente = (c) => {
        setCliente(c)
        setNivel(2)
    }

    const irAFlowType = (tipo) => {
        setFlowType(tipo)
        setNivel(3)
    }

    const irAFlow = (f) => {
        setFlow(f)
        setNivel(4)
    }

    const volver = () => {
        if (nivel === 4) { setFlow(null); setNivel(3) }
        else if (nivel === 3) { setFlowType(null); setNivel(2) }
        else if (nivel === 2) { setCliente(null); setNivel(1) }
    }

    if (nivel === 4 && flow && cliente) {
        return (
            <NivelHistorial
                cliente={cliente}
                flow={flow}
                onVolver={volver}
            />
        )
    }

    if (nivel === 3 && flowType && cliente) {
        return (
            <NivelFlows
                cliente={cliente}
                flowType={flowType}
                onSeleccionar={irAFlow}
                onVolver={volver}
            />
        )
    }

    if (nivel === 2 && cliente) {
        return (
            <NivelCategorias
                cliente={cliente}
                onSeleccionar={irAFlowType}
                onVolver={volver}
            />
        )
    }

    return <NivelClientes onSeleccionar={irACliente} />
}

export default EjecucionesPage

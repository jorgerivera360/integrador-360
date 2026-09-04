import { useCallback, useState } from 'react'
import { useSetBreadcrumb } from '@/layouts/BreadcrumbContext'
import NivelClientes from './components/NivelClientes'
import NivelCategorias from './components/NivelCategorias'
import NivelFlows from './components/NivelFlows'
import EditorFlow from './components/EditorFlow'
import '@/styles/pagina.css'
import './flujos.css'

const TITULOS_TIPO = {
    items: 'Productos',
    customer: 'Clientes',
    supplier: 'Proveedores',
    purchases: 'Entrada',
    sales: 'Salida',
}

const FlujosPage = () => {
    const [nivel, setNivel] = useState(1)
    const [cliente, setCliente] = useState(null)
    const [flowType, setFlowType] = useState(null)
    const [flowId, setFlowId] = useState(null)
    const [flowName, setFlowName] = useState(null)
    const [flowTypeCrear, setFlowTypeCrear] = useState(null)

    const breadcrumb = nivel === 1 ? null
        : nivel === 2 ? [cliente?.name]
        : nivel === 3 ? [cliente?.name, TITULOS_TIPO[flowType] || flowType]
        : [cliente?.name, TITULOS_TIPO[flowTypeCrear || flowType] || flowType, flowName || 'Nuevo flujo']

    const navegarBreadcrumb = useCallback((indiceExtra) => {
        // -1 = segmento base ("Flujos") → reset a nivel 1
        // 0  = cliente → nivel 2
        // 1  = categoría → nivel 3
        if (indiceExtra === -1) {
            setCliente(null); setFlowType(null)
            setFlowId(null); setFlowName(null); setFlowTypeCrear(null)
            setNivel(1)
            return
        }
        const nivelDestino = indiceExtra + 2
        if (nivelDestino <= nivel) {
            if (nivelDestino <= 2) { setFlowType(null) }
            if (nivelDestino <= 3) { setFlowId(null); setFlowName(null); setFlowTypeCrear(null) }
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

    const irAEditar = (flow) => {
        setFlowId(flow.id)
        setFlowName(flow.flow_name)
        setFlowTypeCrear(null)
        setNivel(4)
    }

    const irACrear = (tipo) => {
        setFlowId(null)
        setFlowName(null)
        setFlowTypeCrear(tipo)
        setNivel(4)
    }

    const volver = () => {
        if (nivel === 4) { setFlowId(null); setFlowName(null); setFlowTypeCrear(null); setNivel(3) }
        else if (nivel === 3) { setFlowType(null); setNivel(2) }
        else if (nivel === 2) { setCliente(null); setNivel(1) }
    }

    if (nivel === 4 && cliente) {
        return (
            <EditorFlow
                cliente={cliente}
                flowId={flowId}
                flowType={flowTypeCrear || flowType}
                onVolver={volver}
            />
        )
    }

    if (nivel === 3 && flowType && cliente) {
        return (
            <NivelFlows
                cliente={cliente}
                flowType={flowType}
                onEditar={irAEditar}
                onCrear={irACrear}
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

export default FlujosPage

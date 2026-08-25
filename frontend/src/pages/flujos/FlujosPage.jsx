import { useState } from 'react'
import NivelClientes from './components/NivelClientes'
import NivelCategorias from './components/NivelCategorias'
import NivelFlows from './components/NivelFlows'
import EditorFlow from './components/EditorFlow'
import '@/styles/pagina.css'
import './flujos.css'

const FlujosPage = () => {
    const [nivel, setNivel] = useState(1)
    const [cliente, setCliente] = useState(null)
    const [flowType, setFlowType] = useState(null)
    const [flowId, setFlowId] = useState(null)
    const [flowTypeCrear, setFlowTypeCrear] = useState(null)

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
        setFlowTypeCrear(null)
        setNivel(4)
    }

    const irACrear = (tipo) => {
        setFlowId(null)
        setFlowTypeCrear(tipo)
        setNivel(4)
    }

    const volver = () => {
        if (nivel === 4) { setFlowId(null); setFlowTypeCrear(null); setNivel(3) }
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

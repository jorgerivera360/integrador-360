import { useState } from 'react'
import NivelClientes from './components/NivelClientes'
import NivelCategorias from './components/NivelCategorias'
import NivelFlows from './components/NivelFlows'
import NivelHistorial from './components/NivelHistorial'
import '@/styles/pagina.css'
import './ejecuciones.css'

const EjecucionesPage = () => {
    const [nivel, setNivel] = useState(1)
    const [cliente, setCliente] = useState(null)
    const [flowType, setFlowType] = useState(null)
    const [flow, setFlow] = useState(null)

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

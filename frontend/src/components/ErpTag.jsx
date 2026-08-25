import { erpPorValor } from '@/config/erp'
import './tags.css'

const DESCONOCIDO = {
    color: 'rgba(0,0,0,.45)',
    fondo: '#fafafa',
    borde: '#d9d9d9',
}

/** Etiqueta del tipo de ERP de un cliente. */
const ErpTag = ({ erpType }) => {
    const erp = erpPorValor(erpType)
    const estilo = erp || DESCONOCIDO

    return (
        <span
            className="tag-base"
            style={{
                color: estilo.color,
                background: estilo.fondo,
                borderColor: estilo.borde,
            }}
        >
            {erp ? erp.label : erpType || 'Sin ERP'}
        </span>
    )
}

export default ErpTag

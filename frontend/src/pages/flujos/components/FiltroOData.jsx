import { Button, Input, Select } from 'antd'
import { IconEliminar } from '../icons'

const OPERADORES = [
    { value: 'eq', label: 'eq (igual)' },
    { value: 'ne', label: 'ne (diferente)' },
    { value: 'gt', label: 'gt (mayor)' },
    { value: 'ge', label: 'ge (mayor o igual)' },
    { value: 'lt', label: 'lt (menor)' },
    { value: 'le', label: 'le (menor o igual)' },
]

const FiltroOData = ({ condiciones = [], onChange }) => {
    const agregar = () => {
        onChange([...condiciones, { campo: '', operador: 'eq', valor: '' }])
    }

    const cambiar = (indice, prop, nuevoValor) => {
        const copia = condiciones.map((c, i) =>
            i === indice ? { ...c, [prop]: nuevoValor } : c
        )
        onChange(copia)
    }

    const eliminar = (indice) => {
        onChange(condiciones.filter((_, i) => i !== indice))
    }

    const preview = condiciones
        .filter((c) => c.campo && c.valor)
        .map((c) => `${c.campo} ${c.operador} '${c.valor}'`)
        .join(' and ')

    return (
        <div className="flujo-filtro-odata">
            <div className="flujo-filtro-odata__cabecera">
                <span className="flujo-filtro-odata__col">Campo SAP</span>
                <span className="flujo-filtro-odata__col flujo-filtro-odata__col--op">Operador</span>
                <span className="flujo-filtro-odata__col">Valor</span>
                <span className="flujo-filtro-odata__col flujo-filtro-odata__col--accion" />
            </div>

            {condiciones.map((cond, i) => (
                <div key={i} className="flujo-filtro-odata__fila">
                    <Input
                        size="small"
                        value={cond.campo}
                        onChange={(e) => cambiar(i, 'campo', e.target.value)}
                        placeholder="ItemCode"
                    />
                    <Select
                        size="small"
                        value={cond.operador}
                        onChange={(val) => cambiar(i, 'operador', val)}
                        options={OPERADORES}
                        style={{ width: 160 }}
                    />
                    <Input
                        size="small"
                        value={cond.valor}
                        onChange={(e) => cambiar(i, 'valor', e.target.value)}
                        placeholder="valor"
                    />
                    <button
                        className="flujo-tcv__eliminar"
                        onClick={() => eliminar(i)}
                        type="button"
                    >
                        <IconEliminar />
                    </button>
                </div>
            ))}

            {condiciones.length === 0 && (
                <div className="flujo-tcv__vacio">Sin condiciones de filtro</div>
            )}

            <Button
                className="flujo-tcv__agregar"
                type="dashed"
                size="small"
                onClick={agregar}
            >
                + Agregar condicion
            </Button>

            {preview && (
                <div className="flujo-filtro-odata__preview">
                    <span className="flujo-filtro-odata__preview-label">$filter =</span>
                    <code className="flujo-filtro-odata__preview-valor">{preview}</code>
                </div>
            )}
        </div>
    )
}

export default FiltroOData

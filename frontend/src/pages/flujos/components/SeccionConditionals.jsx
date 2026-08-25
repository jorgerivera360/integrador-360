import { Button, Input, Select } from 'antd'
import TablaClaveValor from './TablaClaveValor'
import { IconEliminar } from '../icons'

const FUNCIONES_CATALOGO = [
    { value: 'route_compra_manufactura_prefijo', label: 'route_compra_manufactura_prefijo', params: ['campo_compra', 'campo_manufactura', 'campo_referencia', 'prefijo_manufactura'] },
    { value: 'extraer_prefijo', label: 'extraer_prefijo', params: ['campo_origen'] },
    { value: 'concatenar_campos', label: 'concatenar_campos', params: ['campos', 'separador'] },
    { value: 'valor_por_campo', label: 'valor_por_campo', params: ['campo_origen', 'valor', 'si', 'no'] },
    { value: 'valor_por_lista', label: 'valor_por_lista', params: ['campo_origen', 'lista', 'si', 'no'] },
    { value: 'doc_name_por_rango', label: 'doc_name_por_rango', params: ['campo_origen', 'rangos', 'separador'] },
    { value: 'sap_field_combined', label: 'sap_field_combined', params: ['campo1', 'campo2', 'valor_esperado', 'texto_ambos', 'texto_solo_uno'] },
]

const OPCIONES_FUNCIONES = FUNCIONES_CATALOGO.map((f) => ({
    value: f.value,
    label: f.label,
}))

const BloqueRegla = ({ regla, indice, onChange, onEliminar }) => {
    const cambiar = (campo, valor) => {
        onChange(indice, { ...regla, [campo]: valor })
    }

    return (
        <div className="flujo-condicional flujo-condicional--regla">
            <div className="flujo-condicional__cabecera">
                <span className="flujo-condicional__tipo">Regla condicional</span>
                <button
                    className="flujo-tcv__eliminar"
                    onClick={() => onEliminar(indice)}
                    type="button"
                >
                    <IconEliminar />
                </button>
            </div>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Campo destino</label>
                    <Input
                        size="small"
                        value={regla.campo_destino || ''}
                        onChange={(e) => cambiar('campo_destino', e.target.value)}
                        placeholder="ej: ruta"
                    />
                </div>
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Campo origen</label>
                    <Input
                        size="small"
                        value={regla.campo_origen || ''}
                        onChange={(e) => cambiar('campo_origen', e.target.value)}
                        placeholder="ej: tipo_producto"
                    />
                </div>
            </div>

            <div className="flujo-campo flujo-campo--ancho">
                <label className="flujo-campo__label">Reglas (si el valor es / entonces asignar)</label>
                <TablaClaveValor
                    columnas={['Si el valor es', 'Entonces asignar']}
                    datos={regla.reglas || []}
                    onChange={(nuevas) => cambiar('reglas', nuevas)}
                    placeholders={['MP', 'Materia Prima']}
                />
            </div>

            <div className="flujo-campo">
                <label className="flujo-campo__label">Valor por defecto</label>
                <Input
                    size="small"
                    value={regla.valor_por_defecto || ''}
                    onChange={(e) => cambiar('valor_por_defecto', e.target.value)}
                    placeholder="valor si no coincide ninguna regla"
                />
            </div>
        </div>
    )
}

const BloqueFuncion = ({ funcion, indice, onChange, onEliminar }) => {
    const cambiar = (campo, valor) => {
        onChange(indice, { ...funcion, [campo]: valor })
    }

    const funcCatalogo = FUNCIONES_CATALOGO.find((f) => f.value === funcion.nombre)
    const parametrosEsperados = funcCatalogo?.params || []

    return (
        <div className="flujo-condicional flujo-condicional--funcion">
            <div className="flujo-condicional__cabecera">
                <span className="flujo-condicional__tipo">Funcion del catalogo</span>
                <button
                    className="flujo-tcv__eliminar"
                    onClick={() => onEliminar(indice)}
                    type="button"
                >
                    <IconEliminar />
                </button>
            </div>

            <div className="flujo-campos">
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Campo destino</label>
                    <Input
                        size="small"
                        value={funcion.campo_destino || ''}
                        onChange={(e) => cambiar('campo_destino', e.target.value)}
                        placeholder="ej: ruta"
                    />
                </div>
                <div className="flujo-campo">
                    <label className="flujo-campo__label">Funcion</label>
                    <Select
                        size="small"
                        value={funcion.nombre || undefined}
                        onChange={(val) => cambiar('nombre', val)}
                        options={OPCIONES_FUNCIONES}
                        placeholder="Seleccionar funcion"
                        style={{ width: '100%' }}
                    />
                </div>
            </div>

            {parametrosEsperados.length > 0 && (
                <div className="flujo-campos flujo-campos--params">
                    {parametrosEsperados.map((param) => (
                        <div key={param} className="flujo-campo">
                            <label className="flujo-campo__label">{param}</label>
                            <Input
                                size="small"
                                value={funcion.params?.[param] || ''}
                                onChange={(e) => {
                                    const nuevosParams = { ...(funcion.params || {}), [param]: e.target.value }
                                    cambiar('params', nuevosParams)
                                }}
                                placeholder={param}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

const SeccionConditionals = ({ conditionals = [], onChange }) => {
    const cambiar = (indice, nuevo) => {
        const copia = conditionals.map((c, i) => (i === indice ? nuevo : c))
        onChange(copia)
    }

    const eliminar = (indice) => {
        onChange(conditionals.filter((_, i) => i !== indice))
    }

    const agregarRegla = () => {
        onChange([...conditionals, {
            tipo: 'regla',
            campo_destino: '',
            campo_origen: '',
            reglas: [],
            valor_por_defecto: '',
        }])
    }

    const agregarFuncion = () => {
        onChange([...conditionals, {
            tipo: 'funcion',
            campo_destino: '',
            nombre: '',
            params: {},
        }])
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Logica de variables y funciones</h3>
            <p className="flujo-seccion__ayuda">
                Los conditionals se ejecutan despues del mapping y los hardcodes.
                Las reglas evaluan campo_origen contra valores fijos.
                Las funciones del catalogo ejecutan logica especifica.
            </p>

            {conditionals.map((cond, i) =>
                cond.tipo === 'funcion' ? (
                    <BloqueFuncion
                        key={i}
                        funcion={cond}
                        indice={i}
                        onChange={cambiar}
                        onEliminar={eliminar}
                    />
                ) : (
                    <BloqueRegla
                        key={i}
                        regla={cond}
                        indice={i}
                        onChange={cambiar}
                        onEliminar={eliminar}
                    />
                )
            )}

            {conditionals.length === 0 && (
                <div className="flujo-tcv__vacio">Sin reglas ni funciones configuradas</div>
            )}

            <div className="flujo-condicional__acciones">
                <Button type="dashed" size="small" onClick={agregarRegla}>
                    + Agregar regla
                </Button>
                <Button type="dashed" size="small" onClick={agregarFuncion}>
                    + Agregar funcion
                </Button>
            </div>
        </div>
    )
}

export default SeccionConditionals

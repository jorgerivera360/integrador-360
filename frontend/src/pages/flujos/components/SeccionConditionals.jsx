import { useState, useEffect } from 'react'
import { Button, Input, Select, Spin, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'
import { IconEliminar } from '../icons'
import { getDeterminationFunctions } from '@/services/catalog'

const CatalogoFunciones = ({ funciones }) => {
    const [abierto, setAbierto] = useState(false)

    return (
        <div className="flujo-variables">
            <button
                type="button"
                className="flujo-variables__toggle"
                onClick={() => setAbierto(!abierto)}
            >
                {abierto ? '▾' : '▸'} Ver funciones disponibles
            </button>
            {abierto && (
                <div className="flujo-variables__lista">
                    {funciones.map((fn) => (
                        <div key={fn.name} className="flujo-catalogo-fn">
                            <div className="flujo-catalogo-fn__cabecera">
                                <code className="flujo-variables__codigo">{fn.label}</code>
                                <Tooltip title={fn.descripcion}>
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </div>
                            <div className="flujo-catalogo-fn__params">
                                {fn.params.map((p) => (
                                    <div key={p.name} className="flujo-catalogo-fn__param">
                                        <code className="flujo-catalogo-fn__param-nombre">{p.name}</code>
                                        <Tooltip title={p.descripcion}>
                                            <InfoCircleOutlined className="flujo-seccion__info" />
                                        </Tooltip>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

const BloqueRegla = ({ regla, indice, onChange, onEliminar }) => {
    const cambiar = (campo, valor) => {
        onChange(indice, { ...regla, [campo]: valor })
    }

    return (
        <div className="flujo-condicional flujo-condicional--regla">
            <div className="flujo-condicional__cabecera">
                <span className="flujo-condicional__tipo">
                    Regla condicional{' '}
                    <Tooltip title="Evalúa el valor de un campo y según lo que contenga, asigna un resultado a otro campo. Funciona como un 'si esto entonces aquello'. Puede usarse para transformar valores que vienen del ERP (ej: estado 3 → 'draft') o para crear campos nuevos que no existen en el ERP. Si el campo destino ya tiene un valor, la regla lo sobreescribe. Las condiciones se evalúan de arriba a abajo y se aplica la primera que coincida.">
                        <InfoCircleOutlined className="flujo-seccion__info" />
                    </Tooltip>
                </span>
                <button
                    className="flujo-tcv__eliminar"
                    onClick={() => onEliminar(indice)}
                    type="button"
                >
                    <IconEliminar />
                </button>
            </div>

            <div className="flujo-regla-config">
                <div className="flujo-regla-linea">
                    <span className="flujo-regla-etiqueta">Evaluar el campo</span>
                    <Input
                        size="small"
                        className="flujo-regla-input"
                        value={regla.campo_origen || ''}
                        onChange={(e) => cambiar('campo_origen', e.target.value)}
                        placeholder="ej: Maneja_lote"
                    />
                    <Tooltip title="Campo cuyo valor se evalúa en las condiciones de abajo. Si el campo fue renombrado en el mapeo, usar el nombre ya mapeado. Si no fue mapeado, usar el nombre original del ERP.">
                        <InfoCircleOutlined className="flujo-seccion__info" />
                    </Tooltip>
                </div>
                <div className="flujo-regla-linea">
                    <span className="flujo-regla-etiqueta">Asignar resultado a</span>
                    <Input
                        size="small"
                        className="flujo-regla-input"
                        value={regla.campo_destino || ''}
                        onChange={(e) => cambiar('campo_destino', e.target.value)}
                        placeholder="ej: tracking"
                    />
                    <Tooltip title="Campo que recibirá el valor resultante. Puede ser un campo que ya existe (vino del ERP o de un valor fijo) y la regla lo sobreescribe, o un campo completamente nuevo que se crea en ese momento. El resultado viaja junto con los demás campos hacia WMS.">
                        <InfoCircleOutlined className="flujo-seccion__info" />
                    </Tooltip>
                </div>
            </div>

            <div className="flujo-campo flujo-campo--ancho" style={{ marginTop: 12 }}>
                <TablaClaveValor
                    columnas={['Si es', 'Asignar']}
                    datos={regla.reglas || []}
                    onChange={(nuevas) => cambiar('reglas', nuevas)}
                    placeholders={['SI', 'lot']}
                />
            </div>

            <div className="flujo-regla-linea flujo-regla-linea--default">
                <span className="flujo-regla-etiqueta">Si no coincide ninguna</span>
                <Input
                    size="small"
                    className="flujo-regla-input"
                    value={regla.valor_por_defecto || ''}
                    onChange={(e) => cambiar('valor_por_defecto', e.target.value)}
                    placeholder=""
                />
                <Tooltip title="Valor que se asigna cuando ninguna de las condiciones anteriores coincide. Si se deja vacío, el campo no se modifica; es decir, si ya existía conserva su valor original y si no existía, no se crea.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </div>
        </div>
    )
}

const BloqueFuncion = ({ funcion, indice, funciones, onChange, onEliminar }) => {
    const cambiar = (campo, valor) => {
        onChange(indice, { ...funcion, [campo]: valor })
    }

    const funcCatalogo = funciones.find((f) => f.name === funcion.nombre)
    const parametrosEsperados = funcCatalogo ? funcCatalogo.params : []

    const opciones = funciones.map((f) => ({
        value: f.name,
        label: f.label,
    }))

    return (
        <div className="flujo-condicional flujo-condicional--funcion">
            <div className="flujo-condicional__cabecera">
                <span className="flujo-condicional__tipo">
                    Función del catálogo{' '}
                    <Tooltip title="Ejecuta una lógica predefinida que evalúa uno o varios campos del ERP para calcular el valor del campo destino. Cada función tiene sus propios parámetros de configuración. Consulte 'Ver funciones disponibles' para conocer el detalle de cada función y sus parámetros.">
                        <InfoCircleOutlined className="flujo-seccion__info" />
                    </Tooltip>
                </span>
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
                    <label className="flujo-campo__label">
                        Campo destino{' '}
                        <Tooltip title="Campo que recibirá el valor calculado por la función. Puede ser un campo que ya existe (vino del ERP o de un valor fijo) y la función lo sobreescribe, o un campo completamente nuevo que se crea en ese momento.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Input
                        size="small"
                        value={funcion.campo_destino || ''}
                        onChange={(e) => cambiar('campo_destino', e.target.value)}
                        placeholder="ej: ruta"
                    />
                </div>
                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Función{' '}
                        {funcCatalogo && (
                            <Tooltip title={funcCatalogo.descripcion}>
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        )}
                    </label>
                    <Select
                        size="small"
                        value={funcion.nombre || undefined}
                        onChange={(val) => cambiar('nombre', val)}
                        options={opciones}
                        placeholder="Seleccionar función"
                        style={{ width: '100%' }}
                    />
                </div>
            </div>

            {parametrosEsperados.length > 0 && (
                <div className="flujo-campos flujo-campos--params">
                    {parametrosEsperados.map((p) => (
                        <div key={p.name} className="flujo-campo">
                            <label className="flujo-campo__label">
                                {p.name}{' '}
                                <Tooltip title={p.descripcion}>
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </label>
                            <Input
                                size="small"
                                value={funcion.params?.[p.name] || ''}
                                onChange={(e) => {
                                    const nuevosParams = { ...(funcion.params || {}), [p.name]: e.target.value }
                                    cambiar('params', nuevosParams)
                                }}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

const SeccionConditionals = ({ conditionals = [], onChange }) => {
    const [funciones, setFunciones] = useState([])
    const [cargando, setCargando] = useState(true)

    useEffect(() => {
        getDeterminationFunctions()
            .then(setFunciones)
            .catch(() => setFunciones([]))
            .finally(() => setCargando(false))
    }, [])

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
            <h3 className="flujo-seccion__titulo">
                Campos calculados{' '}
                <Tooltip title="Campos cuyo valor no viene directamente del ERP sino que se calcula a partir de otros campos. Hay dos formas de calcularlos: con reglas condicionales (si un campo vale X, asignar Y) o con funciones predefinidas (lógica más compleja que evalúa varios campos). Se ejecutan después del mapeo de campos y los valores fijos.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            {cargando ? (
                <div className="flujo-cargando"><Spin size="small" /></div>
            ) : (
                <>
                    {conditionals.map((cond, i) =>
                        cond.tipo === 'funcion' ? (
                            <BloqueFuncion
                                key={i}
                                funcion={cond}
                                indice={i}
                                funciones={funciones}
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
                        <div className="flujo-tcv__vacio">Sin campos calculados configurados</div>
                    )}

                    <div className="flujo-condicional__acciones">
                        <Button type="dashed" size="small" onClick={agregarRegla}>
                            + Agregar regla condicional
                        </Button>
                        <Button type="dashed" size="small" onClick={agregarFuncion}>
                            + Agregar función
                        </Button>
                    </div>

                    <CatalogoFunciones funciones={funciones} />
                </>
            )}
        </div>
    )
}

export default SeccionConditionals

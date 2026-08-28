import { useState } from 'react'
import { Button, Input, Select, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'
import { IconEliminar } from '../icons'

const FUNCIONES_CATALOGO = [
    {
        value: 'route_compra_manufactura_prefijo',
        label: 'Ruta compra/manufactura por prefijo',
        descripcion: 'Determina la ruta logística del producto en Odoo (Buy, Fabricación o ambas). Evalúa los indicadores de compra y manufactura que vienen del ERP y, adicionalmente, verifica si la referencia del producto comienza con un prefijo específico para forzar la ruta de manufactura. Si ambos indicadores están activos, asigna ambas rutas separadas por coma.',
        params: {
            campo_compra: 'Nombre del campo del ERP que indica si el producto se compra. Acepta valores como "True", "SI" o "1". Ejemplo en Connekta: "Compra".',
            campo_manufactura: 'Nombre del campo del ERP que indica si el producto se manufactura. Acepta los mismos valores que campo_compra. Ejemplo en Connekta: "Manufactura".',
            campo_referencia: 'Nombre del campo que contiene la referencia del producto. Se usa para verificar si empieza con el prefijo de manufactura. Ejemplo: "Referencia_Item".',
            prefijo_manufactura: 'Prefijo alfabético que, si aparece al inicio de la referencia, fuerza la ruta de manufactura. Ejemplo: "PT" hace que "PT001" se considere producto de manufactura aunque el indicador no esté activo.',
        },
    },
    {
        value: 'extraer_prefijo',
        label: 'Extraer prefijo alfabético',
        descripcion: 'Extrae las letras iniciales consecutivas de un campo, ignorando números y caracteres especiales. Útil para clasificar productos por el prefijo de su referencia. Ejemplo: "PT001" → "PT", "MP1234" → "MP", "12345" → "" (sin letras iniciales).',
        params: {
            campo_origen: 'Nombre del campo del cual se extraen las letras iniciales. Normalmente es la referencia del producto. Ejemplo: "Referencia_Item" o "referencia" si ya fue mapeado.',
        },
    },
    {
        value: 'concatenar_campos',
        label: 'Concatenar campos',
        descripcion: 'Une el valor de varios campos en un solo texto, separados por un carácter definido. Los campos vacíos se omiten automáticamente para evitar separadores dobles. Se usa típicamente para armar el nombre de un documento a partir de sus componentes. Ejemplo: campos CO, TipoDocto y ConsecDocto con separador "-" → "001-TEM-123".',
        params: {
            campos: 'Lista de nombres de campos a unir, separados por coma. Se procesan en el orden indicado. Ejemplo: "CO,TipoDocto,ConsecDocto". Usar los nombres del ERP si no fueron mapeados.',
            separador: 'Carácter o texto que se coloca entre cada valor. Ejemplo: "-" produce "001-TEM-123", " " produce "001 TEM 123".',
        },
    },
    {
        value: 'valor_por_campo',
        label: 'Valor según campo',
        descripcion: 'Compara el valor de un campo con un valor específico. Si coincide, asigna un resultado; si no coincide, asigna otro. Es como una regla condicional pero dentro de una función, útil cuando se necesita junto con otras funciones. Ejemplo: si el campo "PurchaseItem" tiene el valor "tYES", asignar "Buy"; si no, asignar "Fabricar".',
        params: {
            campo_origen: 'Nombre del campo cuyo valor se compara. Ejemplo: "PurchaseItem".',
            valor: 'Valor exacto contra el que se compara. La comparación es textual y sensible a mayúsculas. Ejemplo: "tYES".',
            si: 'Texto que se asigna al campo destino cuando el valor del campo origen coincide. Ejemplo: "Buy".',
            no: 'Texto que se asigna al campo destino cuando el valor del campo origen NO coincide. Ejemplo: "Fabricar".',
        },
    },
    {
        value: 'valor_por_lista',
        label: 'Valor según lista',
        descripcion: 'Verifica si el valor de un campo está dentro de una lista de valores permitidos. Si está en la lista asigna un resultado, si no está asigna otro. La comparación funciona tanto con números como con texto. Ejemplo: si "ItemsGroupCode" está en la lista [307, 313, 315, 316], asignar "lot"; si no está, asignar "none".',
        params: {
            campo_origen: 'Nombre del campo cuyo valor se busca en la lista. Ejemplo: "ItemsGroupCode".',
            lista: 'Lista de valores permitidos, separados por coma. Pueden ser números o texto. Ejemplo: "307,313,315,316" o "A,B,C".',
            si: 'Texto que se asigna cuando el valor SÍ está en la lista. Ejemplo: "lot".',
            no: 'Texto que se asigna cuando el valor NO está en la lista. Ejemplo: "none".',
        },
    },
    {
        value: 'doc_name_por_rango',
        label: 'Nombre de documento por rango',
        descripcion: 'Arma el nombre del documento combinando un prefijo con el número del documento. El prefijo se elige según en qué rango numérico cae el consecutivo. Útil en SAP donde distintas series de documentos tienen prefijos diferentes. Ejemplo: DocNum 3565 cae en el rango 1-10000000 que tiene prefijo "OCNAL", resultado: "OCNAL-3565".',
        params: {
            campo_origen: 'Nombre del campo que contiene el número del documento. Debe ser numérico. Ejemplo: "DocNum".',
            rangos: 'Rangos numéricos con sus prefijos en formato "inicio-fin:prefijo", separados por coma. Ejemplo: "1-10000000:OCNAL,10000001-20000000:OCIMP". El documento se asigna al primer rango que coincida.',
            separador: 'Carácter que se coloca entre el prefijo y el número del documento. Por defecto es "-". Ejemplo: con separador "-" el resultado es "OCNAL-3565".',
        },
    },
    {
        value: 'sap_field_combined',
        label: 'Combinación de campos SAP',
        descripcion: 'Evalúa dos campos de SAP contra un valor esperado. Si ambos campos tienen ese valor, asigna un texto; si solo uno o ninguno lo tiene, asigna otro texto diferente. Se usa en SAP para determinar clasificaciones que dependen de dos indicadores simultáneos. Ejemplo: si U_FB_EnviarWMS y U_FB_EnviarProdWMS son ambos "Y", asignar "Producto Terminado, Producción"; si solo uno es "Y", asignar "Producto Terminado".',
        params: {
            campo1: 'Nombre del primer campo a evaluar. Ejemplo: "U_FB_EnviarWMS".',
            campo2: 'Nombre del segundo campo a evaluar. Ejemplo: "U_FB_EnviarProdWMS".',
            valor_esperado: 'Valor que ambos campos deben tener para que se considere una coincidencia completa. Ejemplo: "Y".',
            texto_ambos: 'Texto que se asigna cuando ambos campos coinciden con el valor esperado. Ejemplo: "Producto Terminado, Producción".',
            texto_solo_uno: 'Texto que se asigna cuando solo uno de los campos coincide o ninguno coincide. Ejemplo: "Producto Terminado".',
        },
    },
]

const OPCIONES_FUNCIONES = FUNCIONES_CATALOGO.map((f) => ({
    value: f.value,
    label: f.label,
}))

const CatalogoFunciones = () => {
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
                    {FUNCIONES_CATALOGO.map((fn) => (
                        <div key={fn.value} className="flujo-catalogo-fn">
                            <div className="flujo-catalogo-fn__cabecera">
                                <code className="flujo-variables__codigo">{fn.label}</code>
                                <Tooltip title={fn.descripcion}>
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </div>
                            <div className="flujo-catalogo-fn__params">
                                {Object.entries(fn.params).map(([nombre, desc]) => (
                                    <div key={nombre} className="flujo-catalogo-fn__param">
                                        <code className="flujo-catalogo-fn__param-nombre">{nombre}</code>
                                        <Tooltip title={desc}>
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
                    <Tooltip title="Campo que recibirá el valor resultante. Puede ser un campo que ya existe (vino del ERP o de un valor fijo) y la regla lo sobreescribe, o un campo completamente nuevo que se crea en ese momento. El resultado viaja junto con los demás campos hacia Odoo.">
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

const BloqueFuncion = ({ funcion, indice, onChange, onEliminar }) => {
    const cambiar = (campo, valor) => {
        onChange(indice, { ...funcion, [campo]: valor })
    }

    const funcCatalogo = FUNCIONES_CATALOGO.find((f) => f.value === funcion.nombre)
    const parametrosEsperados = funcCatalogo ? Object.keys(funcCatalogo.params) : []

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
                        options={OPCIONES_FUNCIONES}
                        placeholder="Seleccionar función"
                        style={{ width: '100%' }}
                    />
                </div>
            </div>

            {parametrosEsperados.length > 0 && (
                <div className="flujo-campos flujo-campos--params">
                    {parametrosEsperados.map((param) => (
                        <div key={param} className="flujo-campo">
                            <label className="flujo-campo__label">
                                {param}{' '}
                                <Tooltip title={funcCatalogo.params[param]}>
                                    <InfoCircleOutlined className="flujo-seccion__info" />
                                </Tooltip>
                            </label>
                            <Input
                                size="small"
                                value={funcion.params?.[param] || ''}
                                onChange={(e) => {
                                    const nuevosParams = { ...(funcion.params || {}), [param]: e.target.value }
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

            <CatalogoFunciones />
        </div>
    )
}

export default SeccionConditionals

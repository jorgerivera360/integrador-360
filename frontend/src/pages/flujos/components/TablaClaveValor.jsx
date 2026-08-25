import { Button, Input } from 'antd'
import { IconEliminar } from '../icons'

const TablaClaveValor = ({
    columnas = ['Clave', 'Valor'],
    datos = [],
    onChange,
    placeholders = ['', ''],
    soloLectura = false,
}) => {
    const agregar = () => {
        onChange([...datos, { clave: '', valor: '' }])
    }

    const cambiar = (indice, campo, nuevoValor) => {
        const copia = datos.map((fila, i) =>
            i === indice ? { ...fila, [campo]: nuevoValor } : fila
        )
        onChange(copia)
    }

    const eliminar = (indice) => {
        onChange(datos.filter((_, i) => i !== indice))
    }

    return (
        <div className="flujo-tcv">
            <div className="flujo-tcv__cabecera">
                <span className="flujo-tcv__col">{columnas[0]}</span>
                <span className="flujo-tcv__col">{columnas[1]}</span>
                {!soloLectura && <span className="flujo-tcv__col flujo-tcv__col--accion" />}
            </div>

            {datos.map((fila, i) => (
                <div key={i} className="flujo-tcv__fila">
                    <Input
                        className="flujo-tcv__input"
                        value={fila.clave}
                        onChange={(e) => cambiar(i, 'clave', e.target.value)}
                        placeholder={placeholders[0]}
                        disabled={soloLectura}
                        size="small"
                    />
                    <Input
                        className="flujo-tcv__input"
                        value={fila.valor}
                        onChange={(e) => cambiar(i, 'valor', e.target.value)}
                        placeholder={placeholders[1]}
                        disabled={soloLectura}
                        size="small"
                    />
                    {!soloLectura && (
                        <button
                            className="flujo-tcv__eliminar"
                            onClick={() => eliminar(i)}
                            title="Eliminar fila"
                            type="button"
                        >
                            <IconEliminar />
                        </button>
                    )}
                </div>
            ))}

            {datos.length === 0 && (
                <div className="flujo-tcv__vacio">Sin datos configurados</div>
            )}

            {!soloLectura && (
                <Button
                    className="flujo-tcv__agregar"
                    type="dashed"
                    size="small"
                    onClick={agregar}
                >
                    + Agregar
                </Button>
            )}
        </div>
    )
}

export default TablaClaveValor

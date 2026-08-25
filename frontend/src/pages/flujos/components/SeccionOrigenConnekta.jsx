import { Input, Switch } from 'antd'
import TablaClaveValor from './TablaClaveValor'

const SeccionOrigenConnekta = ({ config, onChange }) => {
    const cambiar = (campo, valor) => {
        onChange({ ...config, [campo]: valor })
    }

    const parametros = config.parametros_tabla || []

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Origen de datos</h3>

            <div className="flujo-campos">
                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">Query descriptor (query_desc)</label>
                    <Input
                        className="flujo-input-mono"
                        value={config.query_desc || ''}
                        onChange={(e) => cambiar('query_desc', e.target.value)}
                        placeholder="ej: pinturastitopabon_articulos"
                    />
                </div>

                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Parametros
                        <span className="flujo-campo__hint">
                            Placeholders: {'{hoy}'}, {'{hoy-N}'}, {'{inicio_mes}'}, {'{fin_mes}'}
                        </span>
                    </label>
                    <TablaClaveValor
                        columnas={['Clave', 'Valor']}
                        datos={parametros}
                        onChange={(nuevos) => cambiar('parametros_tabla', nuevos)}
                        placeholders={['FechaInicio', '{hoy-1}']}
                    />
                </div>

                <div className="flujo-campo flujo-campo--switch">
                    <label className="flujo-campo__label">Paginacion</label>
                    <Switch
                        checked={config.paginacion !== false}
                        onChange={(checked) => cambiar('paginacion', checked)}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionOrigenConnekta

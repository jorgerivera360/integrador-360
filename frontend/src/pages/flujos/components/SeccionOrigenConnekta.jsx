import { Input, Switch, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'
import VariablesDinamicas from './VariablesDinamicas'

const SeccionOrigenConnekta = ({ config, onChange }) => {
    const cambiar = (campo, valor) => {
        onChange({ ...config, [campo]: valor })
    }

    const parametros = config.parametros_tabla || []

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Origen de datos{' '}
                <Tooltip title="Configuración de la consulta a la API REST de SIESA Connekta. Define qué reporte consultar, con qué filtros de fecha y si debe paginar los resultados automáticamente">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="flujo-campos">
                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Consulta Connekta{' '}
                        <Tooltip title="Nombre de la consulta configurada en la plataforma SIESA Connekta. Dentro de Connekta esta consulta contiene el SQL que extrae la información directamente de SIESA y la expone como servicio REST. El nombre lo define la persona encargada de registrar la consulta en la plataforma.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Input
                        className="flujo-input-mono"
                        value={config.query_desc || ''}
                        onChange={(e) => cambiar('query_desc', e.target.value)}
                        placeholder="ej: pinturastitopabon_articulos"
                    />
                </div>

                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Parámetros{' '}
                        <Tooltip title="Filtros que se envían junto con la consulta a Connekta para limitar los resultados. Se pueden usar placeholders dinámicos que el sistema resuelve automáticamente antes de cada ejecución.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <TablaClaveValor
                        columnas={['Clave', 'Valor']}
                        datos={parametros}
                        onChange={(nuevos) => cambiar('parametros_tabla', nuevos)}
                        placeholders={['FechaInicio', '{hoy-1}']}
                    />
                    <VariablesDinamicas />
                </div>

                <div className="flujo-campo flujo-campo--switch">
                    <label className="flujo-campo__label">
                        Paginación{' '}
                        <Tooltip title="Si está activo, el sistema consulta la API de Connekta en múltiples llamadas (páginas de 100 registros), acumula todos los resultados y los procesa juntos. Activar cuando el reporte devuelve muchos registros. Si está desactivado, trae todo en una sola llamada.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
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

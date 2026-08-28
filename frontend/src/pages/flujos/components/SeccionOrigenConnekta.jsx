import { useState } from 'react'
import { Input, Switch, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const VARIABLES = [
    {
        codigo: '{hoy}',
        nombre: 'Fecha actual',
        tooltip: 'Se reemplaza por la fecha del día en que se ejecuta el flujo, en formato YYYYMMDD. Ejemplo: si hoy es 28 de agosto de 2026, el valor será 20260828.',
    },
    {
        codigo: '{hoy-N}',
        nombre: 'Hace N días',
        tooltip: 'Resta N días a la fecha actual. Útil para traer documentos recientes. Ejemplo: {hoy-1} = ayer, {hoy-7} = hace una semana, {hoy-30} = hace un mes.',
    },
    {
        codigo: '{hoy+N}',
        nombre: 'En N días',
        tooltip: 'Suma N días a la fecha actual. Ejemplo: {hoy+1} = mañana, {hoy+7} = en una semana.',
    },
    {
        codigo: '{inicio_mes}',
        nombre: 'Primer día del mes',
        tooltip: 'Se reemplaza por el primer día del mes actual. Ejemplo: si estamos en agosto 2026, el valor será 20260801.',
    },
    {
        codigo: '{fin_mes}',
        nombre: 'Último día del mes',
        tooltip: 'Se reemplaza por el último día del mes actual. Tiene en cuenta meses de 28, 29, 30 y 31 días. Ejemplo: en agosto 2026 será 20260831, en febrero 2026 será 20260228.',
    },
    {
        codigo: '{inicio_mes-N}',
        nombre: 'Inicio de hace N meses',
        tooltip: 'Primer día del mes que fue hace N meses. Ejemplo: {inicio_mes-1} en agosto 2026 será 20260701 (primer día de julio). Útil para traer datos del mes anterior.',
    },
    {
        codigo: '{fin_mes-N}',
        nombre: 'Fin de hace N meses',
        tooltip: 'Último día del mes que fue hace N meses. Ejemplo: {fin_mes-1} en agosto 2026 será 20260731 (último día de julio).',
    },
]

const VariablesDinamicas = () => {
    const [abierto, setAbierto] = useState(false)

    return (
        <div className="flujo-variables">
            <button
                type="button"
                className="flujo-variables__toggle"
                onClick={() => setAbierto(!abierto)}
            >
                {abierto ? '▾' : '▸'} Ver variables dinámicas disponibles
            </button>
            {abierto && (
                <div className="flujo-variables__lista">
                    {VARIABLES.map((v) => (
                        <div key={v.codigo} className="flujo-variables__item">
                            <code className="flujo-variables__codigo">{v.codigo}</code>
                            <span className="flujo-variables__nombre">{v.nombre}</span>
                            <Tooltip title={v.tooltip}>
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

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

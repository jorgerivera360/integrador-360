import { useState } from 'react'
import { Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'

const VARIABLES_CONNEKTA = [
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

const VARIABLES_SAP = [
    {
        codigo: '{hoy}',
        nombre: 'Fecha actual',
        tooltip: 'Se reemplaza por la fecha del día en que se ejecuta el flujo, en formato YYYY-MM-DD. Ejemplo: si hoy es 28 de agosto de 2026, el valor será 2026-08-28.',
    },
    {
        codigo: '{hoy-N}',
        nombre: 'Hace N días',
        tooltip: 'Resta N días a la fecha actual. Útil para traer documentos recientes. Ejemplo: {hoy-1} = ayer (2026-08-27), {hoy-7} = hace una semana (2026-08-21), {hoy-30} = hace un mes.',
    },
    {
        codigo: '{hoy+N}',
        nombre: 'En N días',
        tooltip: 'Suma N días a la fecha actual. Ejemplo: {hoy+1} = mañana (2026-08-29), {hoy+7} = en una semana (2026-09-04).',
    },
    {
        codigo: '{inicio_mes}',
        nombre: 'Primer día del mes',
        tooltip: 'Se reemplaza por el primer día del mes actual. Ejemplo: si estamos en agosto 2026, el valor será 2026-08-01.',
    },
    {
        codigo: '{fin_mes}',
        nombre: 'Último día del mes',
        tooltip: 'Se reemplaza por el último día del mes actual. Tiene en cuenta meses de 28, 29, 30 y 31 días. Ejemplo: en agosto 2026 será 2026-08-31, en febrero 2026 será 2026-02-28.',
    },
    {
        codigo: '{inicio_mes-N}',
        nombre: 'Inicio de hace N meses',
        tooltip: 'Primer día del mes que fue hace N meses. Ejemplo: {inicio_mes-1} en agosto 2026 será 2026-07-01 (primer día de julio). Útil para traer datos del mes anterior.',
    },
    {
        codigo: '{fin_mes-N}',
        nombre: 'Fin de hace N meses',
        tooltip: 'Último día del mes que fue hace N meses. Ejemplo: {fin_mes-1} en agosto 2026 será 2026-07-31 (último día de julio).',
    },
]

const VariablesDinamicas = ({ erp = 'connekta' }) => {
    const [abierto, setAbierto] = useState(false)
    const variables = erp === 'sap' ? VARIABLES_SAP : VARIABLES_CONNEKTA

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
                    {variables.map((v) => (
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

export default VariablesDinamicas

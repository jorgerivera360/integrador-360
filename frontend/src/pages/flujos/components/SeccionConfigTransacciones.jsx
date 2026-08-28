import { Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import TablaClaveValor from './TablaClaveValor'

const SeccionConfigTransacciones = ({ flowType, config, onChange }) => {
    const esEntrada = flowType === 'purchases'

    const titulo = esEntrada
        ? 'Configuración del flujo — Documentos de entrada'
        : 'Configuración del flujo — Documentos de salida'

    const tooltipSeccion = esEntrada
        ? 'Opciones que definen cómo se procesan los documentos de entrada (órdenes de compra, transferencias, devoluciones de cliente, etc.) al crearlos en Odoo. Cada opción controla un aspecto del procesamiento'
        : 'Opciones que definen cómo se procesan los documentos de salida (pedidos de venta, facturas, transferencias de salida, devoluciones a proveedor, etc.) al crearlos en Odoo. Cada opción controla un aspecto del procesamiento'

    const subtitulo = esEntrada
        ? 'Mapeo de almacenes — Operación de recepción'
        : 'Mapeo de almacenes'

    const tooltipMapping = esEntrada
        ? 'Relaciona cada bodega del ERP con la operación de recepción correspondiente en Odoo. El ERP maneja sus propios códigos de bodega (ej: 00550, 00006, PPAL) y Odoo tiene sus operaciones de recepción con IDs propios. El admin debe conocer ambos sistemas para hacer la equivalencia. Ejemplo: bodega "00550" del ERP → operación de recepción ID 1 en Odoo. Las operaciones de recepción se consultan en Odoo en Inventario > Configuración > Tipos de operación. Si una bodega no está en la tabla, se usa la operación de recepción por defecto del almacén principal.'
        : 'Relaciona cada bodega del ERP con el almacén correspondiente en Odoo. El ERP maneja sus propios códigos de bodega (ej: 00550, 00006, PPAL) y Odoo tiene sus almacenes con IDs propios. El admin debe conocer ambos sistemas para hacer la equivalencia. Ejemplo: bodega "00550" del ERP → almacén ID 1 en Odoo. Los almacenes se consultan en Odoo en Inventario > Configuración > Almacenes. Si una bodega no está en la tabla, se usa el almacén principal por defecto.'

    const columnaOdoo = esEntrada ? 'ID Operación de recepción' : 'ID Almacén Odoo'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                {titulo}{' '}
                <Tooltip title={tooltipSeccion}>
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <h4 className="flujo-seccion__subtitulo">
                {subtitulo}{' '}
                <Tooltip title={tooltipMapping}>
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h4>

            <div className="flujo-campo flujo-campo--ancho">
                <TablaClaveValor
                    columnas={['Bodega ERP', columnaOdoo]}
                    datos={config.warehouse_mapping_tabla || []}
                    onChange={(nuevos) => onChange({ ...config, warehouse_mapping_tabla: nuevos })}
                    placeholders={['00550', '1']}
                />
            </div>
        </div>
    )
}

export default SeccionConfigTransacciones

import { Input, InputNumber, Switch, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'

const SeccionConfigPartners = ({ flowType, config, onChange }) => {
    const cambiar = (campo, valor) => {
        onChange({ ...config, [campo]: valor })
    }

    const esCliente = flowType === 'customer'
    const titulo = esCliente
        ? 'Configuración del flujo — Clientes'
        : 'Configuración del flujo — Proveedores'

    const tipoPar = esCliente ? 'clientes' : 'proveedores'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                {titulo}{' '}
                <Tooltip title={`Opciones que definen cómo se crean los ${tipoPar} en Odoo: si las sucursales se organizan bajo una sede principal, qué país se les asigna y con qué tipo de documento se registran`}>
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="flujo-campos">
                <div className="flujo-campo flujo-campo--switch">
                    <label className="flujo-campo__label">
                        Jerarquía de sucursales{' '}
                        <Tooltip title={`Activar cuando un mismo tercero (mismo NIT) tiene varias sucursales en el ERP. El sistema crea la sucursal configurada como padre (ej: "001") como empresa principal, y las demás sucursales como direcciones de entrega vinculadas a esa empresa. Ejemplo: NIT 900123 con 001, 002 y 003 → "001" se crea como empresa, "002" y "003" como direcciones hijas. Si un tercero viene con una sola sucursal y coincide con la padre, se crea como empresa. Si viene con una sola sucursal distinta a la padre, se crea como contacto normal sin jerarquía. Si se desactiva, todas las sucursales se crean como contactos independientes sin relación entre ellos.`}>
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Switch
                        checked={config.sucursal_hierarchy || false}
                        onChange={(checked) => cambiar('sucursal_hierarchy', checked)}
                    />
                </div>

                {config.sucursal_hierarchy && (
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">
                            Código de la sucursal padre{' '}
                            <Tooltip title="Código de la sucursal que el ERP usa como sede principal. En SIESA siempre es '001'. Esta sucursal se crea primero como empresa y las demás quedan como direcciones hijas. Si el ERP del cliente usa otro código para la sede principal, cambiarlo aquí.">
                                <InfoCircleOutlined className="flujo-seccion__info" />
                            </Tooltip>
                        </label>
                        <Input
                            value={config.sucursal_padre || '001'}
                            onChange={(e) => cambiar('sucursal_padre', e.target.value)}
                            placeholder="001"
                        />
                    </div>
                )}

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        País en Odoo{' '}
                        <Tooltip title="ID del país que se asigna a todos los contactos creados. También se usa para asociar correctamente los departamentos (ej: Antioquia, Valle del Cauca). El valor por defecto 49 es Colombia. Solo cambiar si el cliente opera en otro país.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <InputNumber
                        value={config.country_id ?? 49}
                        onChange={(val) => cambiar('country_id', val)}
                        min={1}
                        style={{ width: '100%' }}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Tipo de identificación{' '}
                        <Tooltip title="Tipo de documento con el que se registra el contacto en Odoo (NIT, cédula, pasaporte, etc.). El valor por defecto 5 es NIT, que aplica para la mayoría de empresas colombianas. Solo se asigna al crear el contacto por primera vez, no se modifica en actualizaciones posteriores.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <InputNumber
                        value={config.identification_type_id ?? 5}
                        onChange={(val) => cambiar('identification_type_id', val)}
                        min={1}
                        style={{ width: '100%' }}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionConfigPartners

import { Input, InputNumber, Switch } from 'antd'

const SeccionConfigPartners = ({ flowType, config, onChange }) => {
    const cambiar = (campo, valor) => {
        onChange({ ...config, [campo]: valor })
    }

    const titulo = flowType === 'customer'
        ? 'Configuracion del flujo — Clientes'
        : 'Configuracion del flujo — Proveedores'

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">{titulo}</h3>

            <div className="flujo-campos">
                <div className="flujo-campo flujo-campo--switch">
                    <label className="flujo-campo__label">Jerarquia de sucursales (sucursal_hierarchy)</label>
                    <Switch
                        checked={config.sucursal_hierarchy || false}
                        onChange={(checked) => cambiar('sucursal_hierarchy', checked)}
                    />
                </div>

                {config.sucursal_hierarchy && (
                    <div className="flujo-campo">
                        <label className="flujo-campo__label">Sucursal padre</label>
                        <Input
                            value={config.sucursal_padre || '001'}
                            onChange={(e) => cambiar('sucursal_padre', e.target.value)}
                            placeholder="001"
                        />
                    </div>
                )}

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        ID de pais (country_id)
                        <span className="flujo-campo__hint">49 = Colombia</span>
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
                        Tipo de identificacion (identification_type_id)
                        <span className="flujo-campo__hint">5 = NIT</span>
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

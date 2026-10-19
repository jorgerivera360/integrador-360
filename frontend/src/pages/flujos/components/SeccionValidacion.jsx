import { Select, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'

const SeccionValidacion = ({ config, onChange }) => {
    const cambiar = (campo, valor) => onChange({ ...config, [campo]: valor })

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Validaci&oacute;n y tipado de campos{' '}
                <Tooltip title="Define qu&eacute; campos del flujo se convierten a n&uacute;mero, entero o fecha, y cu&aacute;les son obligatorios para que un registro sea v&aacute;lido. Si no se configura, el sistema usa valores por defecto seg&uacute;n el tipo de flujo.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            <div className="flujo-campos">
                <div className="flujo-campo flujo-campo--ancho">
                    <label className="flujo-campo__label">
                        Campos obligatorios{' '}
                        <Tooltip title="Campos que deben tener valor para que el registro sea v&aacute;lido. Si alguno est&aacute; vac&iacute;o, el registro se descarta.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        value={config.campos_obligatorios || []}
                        onChange={(v) => cambiar('campos_obligatorios', v)}
                        placeholder="Escribe un nombre de campo y presiona Enter"
                        tokenSeparators={[',']}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Campos num&eacute;ricos (float){' '}
                        <Tooltip title="Campos que se convierten a n&uacute;mero decimal. Ejemplo: cantidad, precio_unitario, impuesto. Si el valor no es num&eacute;rico, se reemplaza por 0.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        value={config.campos_float || []}
                        onChange={(v) => cambiar('campos_float', v)}
                        placeholder="cantidad, precio_unitario, impuesto"
                        tokenSeparators={[',']}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Campos enteros (int){' '}
                        <Tooltip title="Campos que se convierten a n&uacute;mero entero. Ejemplo: use_expiration_date, ind_compra, ind_venta. Si el valor no es num&eacute;rico, se reemplaza por 0.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        value={config.campos_int || []}
                        onChange={(v) => cambiar('campos_int', v)}
                        placeholder="use_expiration_date, ind_compra"
                        tokenSeparators={[',']}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Campos fecha{' '}
                        <Tooltip title="Campos que se parsean como fecha y se convierten al formato YYYY-MM-DD. Soporta m&uacute;ltiples formatos de entrada (YYYYMMDD, ISO 8601, MM/DD/YYYY, etc).">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        value={config.campos_fecha || []}
                        onChange={(v) => cambiar('campos_fecha', v)}
                        placeholder="fecha_entrega, fecha_pedido"
                        tokenSeparators={[',']}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Campos con default 0{' '}
                        <Tooltip title="Campos que se reemplazan por 0 si vienen vac&iacute;os o nulos. &Uacute;til para precio_unitario en transacciones donde el precio puede no venir.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        value={config.campos_default_cero || []}
                        onChange={(v) => cambiar('campos_default_cero', v)}
                        placeholder="precio_unitario"
                        tokenSeparators={[',']}
                    />
                </div>

                <div className="flujo-campo">
                    <label className="flujo-campo__label">
                        Campos mayor a 0{' '}
                        <Tooltip title="Campos que deben ser num&eacute;ricos y mayores a cero. Si el valor es 0, negativo o no num&eacute;rico, el registro se descarta.">
                            <InfoCircleOutlined className="flujo-seccion__info" />
                        </Tooltip>
                    </label>
                    <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        value={config.campos_mayor_cero || []}
                        onChange={(v) => cambiar('campos_mayor_cero', v)}
                        placeholder="cantidad, cantidad_pedida"
                        tokenSeparators={[',']}
                    />
                </div>
            </div>
        </div>
    )
}

export default SeccionValidacion

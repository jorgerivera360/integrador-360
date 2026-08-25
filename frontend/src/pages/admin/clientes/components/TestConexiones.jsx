import { Alert, Button } from 'antd'
import { etiquetaErp } from '@/config/erp'
import { useProbarConexion, mensajeDeError } from '@/hooks/useClientes'
import { IconCheck, IconEquis, IconNube, IconRayo, IconServidor } from '../icons'

/**
 * Una tarjeta de prueba. `tipo`: 'erp' | 'odoo'.
 * El endpoint responde 200 aunque la conexión falle, así que el veredicto
 * sale de `success` en el cuerpo, no del estado HTTP.
 */
const TarjetaTest = ({ clienteId, tipo, titulo, subtitulo, icono, tonoIcono, textoBoton, botonVerde }) => {
    const probar = useProbarConexion(clienteId, tipo)
    const resultado = probar.data

    const fallo = probar.isError
    const exito = !fallo && resultado?.success === true
    const hayResultado = fallo || Boolean(resultado)

    const detalle = fallo ? mensajeDeError(probar.error) : resultado?.msg
    const referencia = tipo === 'odoo' ? resultado?.odoo_url : resultado?.erp_type

    return (
        <div className="test">
            <div className={`test__icono test__icono--${tonoIcono}`}>{icono}</div>
            <div className="test__titulo">{titulo}</div>
            <p className="test__sub">{subtitulo}</p>

            <Button
                type="primary"
                icon={<IconRayo />}
                loading={probar.isPending}
                onClick={() => probar.mutate()}
                style={botonVerde ? { background: '#52c41a', boxShadow: '0 2px 6px rgba(82,196,26,.24)' } : undefined}
            >
                {textoBoton}
            </Button>

            {hayResultado && (
                <div className={`resultado resultado--${exito ? 'ok' : 'error'}`}>
                    <div className="resultado__head">
                        {exito ? <IconCheck /> : <IconEquis />}
                        {exito ? 'Conexión exitosa' : 'Conexión fallida'}
                    </div>
                    <div className="resultado__cuerpo">
                        <div className="resultado__detalle">{detalle}</div>
                        {referencia && <span className="resultado__tag">{referencia}</span>}
                    </div>
                </div>
            )}
        </div>
    )
}

const TestConexiones = ({ cliente }) => (
    <div className="seccion" style={{ marginBottom: 0 }}>
        <div className="seccion__titulo">Verificar conectividad</div>
        <p className="seccion__sub">
            Prueba la conexión con el ERP del cliente y con su instancia de Odoo. Las
            credenciales se obtienen de GCP Secret Manager.
        </p>
        <div className="seccion__linea" />

        <div className="grid-2">
            <TarjetaTest
                clienteId={cliente.id}
                tipo="erp"
                titulo={`ERP — ${etiquetaErp(cliente.erp_type)}`}
                subtitulo="Prueba que el integrador puede conectarse al ERP del cliente"
                icono={<IconServidor />}
                tonoIcono="azul"
                textoBoton="Probar conexión ERP"
            />

            <TarjetaTest
                clienteId={cliente.id}
                tipo="odoo"
                titulo="Odoo WMS"
                subtitulo="Prueba que el integrador puede autenticarse en la instancia de Odoo"
                icono={<IconNube />}
                tonoIcono="verde"
                textoBoton="Probar conexión Odoo"
                botonVerde
            />
        </div>

        <Alert
            type="info"
            showIcon
            style={{ marginTop: 24 }}
            message="Las credenciales se cargan desde GCP Secret Manager. Si la prueba falla, verificar que el secret del cliente existe y que la service account tiene acceso."
        />

        {!cliente.is_active && (
            <Alert
                type="warning"
                showIcon
                style={{ marginTop: 12 }}
                message="El cliente está inactivo. La API rechaza las pruebas de conexión de clientes desactivados."
            />
        )}
    </div>
)

export default TestConexiones

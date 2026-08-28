import { Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'

const SeccionSQL = ({ sql, onChange }) => {
    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Consulta SQL{' '}
                <Tooltip title="Query SQL que se ejecuta contra SIESA WS via SOAP. Debe usar alias canónicos (AS referencia, AS descripcion, etc.) y comillas dobles para strings literales con SET QUOTED_IDENTIFIER OFF">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>
            <textarea
                className="flujo-sql"
                value={sql || ''}
                onChange={(e) => onChange(e.target.value)}
                placeholder="SELECT ... FROM ... WHERE ..."
                spellCheck={false}
            />
        </div>
    )
}

export default SeccionSQL

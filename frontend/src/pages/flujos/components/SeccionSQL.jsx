const SeccionSQL = ({ sql, onChange }) => {
    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">Consulta SQL</h3>
            <p className="flujo-seccion__ayuda">
                Query SQL que se ejecuta contra SIESA WS. Usa SET QUOTED_IDENTIFIER OFF
                y alias canonicos (AS referencia, AS descripcion, etc.)
            </p>
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

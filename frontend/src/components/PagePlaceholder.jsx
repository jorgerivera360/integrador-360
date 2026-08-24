/**
 * Marcador temporal de página, con el mismo aspecto que el placeholder
 * del mockup panel.html. Se va reemplazando pantalla por pantalla.
 */
const PagePlaceholder = ({ titulo }) => (
    <div
        style={{
            minHeight: 320,
            height: '100%',
            background: '#fff',
            borderRadius: 8,
            border: '1px dashed #d9d9d9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'rgba(0,0,0,.35)',
            fontSize: 15,
        }}
    >
        {titulo}
    </div>
)

export default PagePlaceholder

import { useState, useEffect } from 'react'
import { Button, Tooltip, Upload, message } from 'antd'
import { InfoCircleOutlined, UploadOutlined, FileExcelOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { uploadExcel, getExcelFiles } from '@/services/excel'

const TIPO_POR_FLOW = {
    items: 'productos',
    customer: 'clientes',
    supplier: 'proveedores',
    purchases: 'entradas',
    sales: 'salidas',
}

const formatTamano = (bytes) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const formatFecha = (timestamp) => {
    if (!timestamp) return ''
    const fecha = new Date(timestamp * 1000)
    return fecha.toLocaleString('es-CO', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })
}

const SeccionOrigenExcel = ({ clienteId, flowType }) => {
    const [archivoInfo, setArchivoInfo] = useState(null)
    const [subiendo, setSubiendo] = useState(false)
    const [cargando, setCargando] = useState(true)

    const tipo = TIPO_POR_FLOW[flowType] || ''

    useEffect(() => {
        if (!clienteId || !tipo) return
        setCargando(true)
        getExcelFiles(clienteId)
            .then((res) => {
                const archivos = res.data || []
                const encontrado = archivos.find((a) => a.tipo === tipo)
                setArchivoInfo(encontrado || null)
            })
            .catch(() => setArchivoInfo(null))
            .finally(() => setCargando(false))
    }, [clienteId, tipo])

    const subirArchivo = (file) => {
        setSubiendo(true)
        uploadExcel(clienteId, tipo, file)
            .then((res) => {
                const data = res.data
                setArchivoInfo({
                    tipo,
                    archivo: data.archivo,
                    tamano: data.tamano,
                    fecha: Date.now() / 1000,
                })
                message.success('Archivo cargado correctamente')
            })
            .catch((err) => {
                const detalle = err.response?.data?.detail || err.message
                message.error(`Error al cargar: ${detalle}`)
            })
            .finally(() => setSubiendo(false))
        return false
    }

    return (
        <div className="flujo-seccion">
            <h3 className="flujo-seccion__titulo">
                Archivo Excel{' '}
                <Tooltip title="Sube el archivo Excel que contiene los datos a cargar en el WMS. El archivo se guarda en el servidor y se lee cada vez que se ejecuta el flujo. Al subir un archivo nuevo se reemplaza el anterior.">
                    <InfoCircleOutlined className="flujo-seccion__info" />
                </Tooltip>
            </h3>

            {cargando ? (
                <div className="flujo-excel__cargando">Verificando archivo...</div>
            ) : (
                <div className="flujo-excel">
                    {archivoInfo ? (
                        <div className="flujo-excel__archivo">
                            <div className="flujo-excel__icono">
                                <FileExcelOutlined />
                            </div>
                            <div className="flujo-excel__info">
                                <span className="flujo-excel__nombre">{archivoInfo.archivo}</span>
                                <span className="flujo-excel__meta">
                                    {formatTamano(archivoInfo.tamano)}
                                    {archivoInfo.fecha && ` — ${formatFecha(archivoInfo.fecha)}`}
                                </span>
                            </div>
                            <CheckCircleOutlined className="flujo-excel__ok" />
                        </div>
                    ) : (
                        <div className="flujo-excel__vacio">
                            No hay archivo cargado para {tipo}
                        </div>
                    )}

                    <Upload
                        accept=".xlsx,.xls"
                        showUploadList={false}
                        beforeUpload={subirArchivo}
                    >
                        <Button
                            icon={<UploadOutlined />}
                            loading={subiendo}
                        >
                            {archivoInfo ? 'Reemplazar archivo' : 'Subir archivo'}
                        </Button>
                    </Upload>
                </div>
            )}
        </div>
    )
}

export default SeccionOrigenExcel

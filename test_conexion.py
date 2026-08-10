import os
os.environ["ENV"] = "staging"

from config.loader import ConfigLoader
from connection.siesa_enterprise import SiesaEnterprise

config = ConfigLoader("pruebaws").load_config()
config["client_id"] = "pruebaws"
connector = SiesaEnterprise(config)

sql = (
    'SET QUOTED_IDENTIFIER OFF;'
    ' SELECT TOP 1'
    ' CONCAT(TRIM(t430.f430_id_co), TRIM(t430.f430_id_tipo_docto), t430.f430_consec_docto) AS pedido,'
    ' TRIM(t200.f200_nit) AS cliente,'
    ' TRIM(t201.f201_id_sucursal) AS sucursal_cliente,'
    ' ISNULL(CONVERT(VARCHAR, t430.f430_id_fecha, 23), "") AS fecha_pedido,'
    ' "draft" AS estado,'
    ' 1 AS almacen,'
    ' TRIM(RTRIM(v121.v121_id_item)) AS producto,'
    ' t431.f431_cant1_pedida AS cantidad_pedida,'
    ' t431.f431_precio_unitario_base AS precio_unitario,'
    ' "" AS impuesto,'
    ' "" AS zona,'
    ' "" AS vendedor,'
    ' "" AS condicion_pago,'
    ' TRIM(t430.f430_notas) AS observacion,'
    ' TRIM(t431.f431_id_unidad_medida) AS unidad_medida,'
    ' TRIM(t150.f150_id) AS bodega_siesa'
    ' FROM t201_mm_clientes t201'
    ' INNER JOIN t200_mm_terceros t200'
    '     ON t201.f201_rowid_tercero = t200.f200_rowid AND t201.f201_id_cia = t200.f200_id_cia'
    ' INNER JOIN t430_cm_pv_docto t430'
    '     ON t200.f200_id_cia = t430.f430_id_cia AND t200.f200_rowid = t430.f430_rowid_tercero_fact'
    '        AND t201.f201_id_sucursal = t430.f430_id_sucursal_fact'
    ' INNER JOIN t431_cm_pv_movto t431'
    '     ON t431.f431_rowid_pv_docto = t430.f430_rowid AND t430.f430_id_cia = t431.f431_id_cia'
    ' INNER JOIN t150_mc_bodegas t150'
    '     ON t150.f150_rowid = t431.f431_rowid_bodega'
    ' INNER JOIN v121'
    '     ON v121.v121_id_cia = t431.f431_id_cia AND t431.f431_rowid_item_ext = v121.v121_rowid_item_ext'
    ' WHERE t430.f430_id_cia = 1;'
    ' SET QUOTED_IDENTIFIER ON;'
)

status, data = connector.get(endpoint="EjecutarConsultaXML", params={"sql": sql})
print("Status:", status)
if status and data:
    print("Data:", data[0])
else:
    print("Error:", data)
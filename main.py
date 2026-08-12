"""
main.py — Orquestador del sistema
Responsabilidades:
  - build_connector()  → Factory — instancia el conector correcto por erp_type
  - build_transform()  → Factory — instancia el transform correcto por erp_type
  - connection_data()  → autentica en Odoo y retorna JsonRPC listo
  - _dispatch_flow()   → despacha al procesador del core por flow_type
  - run()              → orquesta un flow completo: connector → transform → resolve → core → BD
Patrones: Factory · Strategy
Fase: 6 — Conexión BD + Main
"""
import traceback
from config.logger import IntegradorLogger
from connection.sap import SAP
from connection.siesa_enterprise import SiesaEnterprise
from connection.siesa_connekta import SiesaConnekta
from connection.excel_connector import ExcelConnector
from connection.jsonrpc import JsonRPC
from transform.transform_ws import TransformWS
from transform.transform_connekta import TransformConnekta
from transform.transform_sap import TransformSAP
from core.process_items import ProcessItems
from core.process_partners import ProcessPartners
from core.process_purchases import ProcessPurchases
from core.process_sales import ProcessSales
from core.resolve_missing_masters import resolve_missing_masters


def build_connector(erp_type, config):
    connectors = {
        "ws":      SiesaEnterprise,
        "connekta": SiesaConnekta,
        "sap":     SAP,
        "excel":   ExcelConnector,
    }
    cls = connectors.get(erp_type)
    if not cls:
        raise ValueError(f"Tipo de ERP no soportado: {erp_type}")
    return cls(config)


def build_transform(erp_type, config):
    transforms = {
        "ws":      TransformWS,
        "connekta": TransformConnekta,
        "sap":     TransformSAP,
        "excel":   TransformWS,
    }
    cls = transforms.get(erp_type)
    if not cls:
        raise ValueError(f"Tipo de ERP no soportado para transform: {erp_type}")
    return cls(config)


def connection_data(config):
    odoo = JsonRPC(config)
    ok, msg = odoo.authenticate()
    if not ok:
        raise RuntimeError(f"No se pudo autenticar en Odoo: {msg}")
    return odoo


def _dispatch_flow(data, flow_type, odoo, config, flow_config):
    processors = {
        "items":     ProcessItems,
        "customer":  ProcessPartners,
        "supplier":  ProcessPartners,
        "purchases": ProcessPurchases,
        "sales":     ProcessSales,
    }
    cls = processors.get(flow_type)
    if not cls:
        raise ValueError(f"flow_type no soportado: {flow_type}")
    processor = cls(odoo, config, flow_config)
    return processor.process(data)


def run(flow, config, erp_type, flow_configs=None, db_writer=None,
        triggered_by="scheduler", triggered_user=None):
    flow_id     = flow["flow_id"]
    flow_name   = flow["flow_name"]
    flow_type   = flow["flow_type"]
    flow_config = flow["flow_config"]
    logger      = IntegradorLogger(client_id=config["client_id"])

    # Registrar inicio en BD
    execution_id = None
    if db_writer:
        execution_id = db_writer.start_execution(flow_id, triggered_by, triggered_user)

    try:
        logger.info(f"Main | Iniciando flow '{flow_name}' (tipo: {flow_type})")

        # 1. Connector + Transform
        connector = build_connector(erp_type, config)
        transform = build_transform(erp_type, config)

        # 2. Obtener datos del ERP
        data = transform.get_flow(connector, flow_name, flow_config)

        if not data:
            logger.info(f"Main | Flow '{flow_name}' no retornó datos")
            result = {"creados": 0, "actualizados": 0, "fallidos": [], "total": 0}
            if db_writer:
                db_writer.finish_execution(execution_id, "success", result)
            return result

        # 3. Autenticar en Odoo
        odoo = connection_data(config)

        # 4. Resolve missing masters (solo para transacciones)
        if flow_type in ("purchases", "sales") and flow_configs:
            data_purchases = data if flow_type == "purchases" else None
            data_sales     = data if flow_type == "sales" else None
            resolve_missing_masters(
                odoo, connector, transform,
                data_purchases, data_sales,
                flow_configs, config, logger
            )

        # 5. Ejecutar core
        result = _dispatch_flow(data, flow_type, odoo, config, flow_config)

        # 6. Determinar status
        fallidos = result.get("fallidos", [])
        status = "success" if not fallidos else "partial"
        logger.info(f"Main | Flow '{flow_name}' finalizado: status={status}")

        if db_writer:
            db_writer.finish_execution(execution_id, status, result)

        return result

    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"Main | Error en flow '{flow_name}': {e}")
        if db_writer:
            db_writer.finish_execution(execution_id, "error", None, error_msg)
        raise
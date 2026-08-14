"""
resolve_missing_masters — Resuelve maestros faltantes antes de procesar transacciones
Responsabilidades:
- Identifica productos, proveedores y clientes que están en las transacciones
    pero no existen en Odoo
- Consulta al ERP via connector + transform para obtener los datos completos
- Crea los faltantes en Odoo via ProcessItems / ProcessPartners
- Solo se ejecuta si hay faltantes — si todo existe, termina en milisegundos
No hereda CoreProcessor — es un paso de orquestación
Fase: 4 — Core Layer
"""
from core.process_items import ProcessItems
from core.process_partners import ProcessPartners


BATCH_SIZE = 30


def resolve_missing_masters(odoo, connector, transform, data_purchases, data_sales, flow_configs, config, logger):

    resumen = {
        "productos_faltantes": 0,
        "productos_resueltos": 0,
        "proveedores_faltantes": 0,
        "proveedores_resueltos": 0,
        "clientes_faltantes": 0,
        "clientes_resueltos": 0,
        "no_resueltos": [],
    }

    try:
        # Fase 1: Extraer dependencias únicas de las transacciones
        productos_refs = set()
        proveedores_keys = set()
        clientes_keys = set()

        for row in (data_purchases or []):
            if row.get("producto"):
                productos_refs.add(str(row["producto"]))
            if row.get("proveedor"):
                proveedores_keys.add((row["proveedor"], row.get("sucursal_proveedor", "")))

        for row in (data_sales or []):
            if row.get("producto"):
                productos_refs.add(str(row["producto"]))
            if row.get("cliente"):
                clientes_keys.add((row["cliente"], row.get("sucursal_cliente", "")))

        if not productos_refs and not proveedores_keys and not clientes_keys:
            logger.info("Resolve Masters | Sin dependencias que verificar")
            return resumen

        logger.info(
            f"Resolve Masters | Dependencias: {len(productos_refs)} productos, "
            f"{len(proveedores_keys)} proveedores, {len(clientes_keys)} clientes"
        )

        # Fase 2: Verificar cuáles existen en Odoo
        productos_faltantes = set()
        if productos_refs:
            ok, result = odoo.search_read(
                "product.product",
                [["default_code", "in", list(productos_refs)]],
                ["default_code"]
            )
            if ok:
                existentes = {p["default_code"] for p in (result or [])}
                productos_faltantes = productos_refs - existentes
            else:
                logger.error(f"Resolve Masters | Error verificando productos: {result}")

        proveedores_faltantes = set()
        if proveedores_keys:
            vats_prov = list({k[0] for k in proveedores_keys})
            ok, result = odoo.search_read(
                "res.partner",
                [["vat", "in", vats_prov]],
                ["vat", "sucursal"]
            )
            if ok:
                existentes = {(p["vat"], p.get("sucursal", "")) for p in (result or [])}
                proveedores_faltantes = proveedores_keys - existentes
            else:
                logger.error(f"Resolve Masters | Error verificando proveedores: {result}")

        clientes_faltantes = set()
        if clientes_keys:
            vats_cli = list({k[0] for k in clientes_keys})
            ok, result = odoo.search_read(
                "res.partner",
                [["vat", "in", vats_cli]],
                ["vat", "sucursal"]
            )
            if ok:
                existentes = {(p["vat"], p.get("sucursal", "")) for p in (result or [])}
                clientes_faltantes = clientes_keys - existentes
            else:
                logger.error(f"Resolve Masters | Error verificando clientes: {result}")

        resumen["productos_faltantes"] = len(productos_faltantes)
        resumen["proveedores_faltantes"] = len(proveedores_faltantes)
        resumen["clientes_faltantes"] = len(clientes_faltantes)

        if not productos_faltantes and not proveedores_faltantes and not clientes_faltantes:
            logger.info("Resolve Masters | Todos los maestros existen en Odoo — sin acción")
            return resumen

        logger.info(
            f"Resolve Masters | Faltantes: {len(productos_faltantes)} productos, "
            f"{len(proveedores_faltantes)} proveedores, {len(clientes_faltantes)} clientes"
        )

        # Fase 3: Consultar al ERP y crear faltantes

        # Productos faltantes
        if productos_faltantes and flow_configs.get("items"):
            try:
                logger.info(f"Resolve Masters | Consultando ERP por {len(productos_faltantes)} productos faltantes")
                all_items = _query_erp_batched(
                    transform, connector, "items",
                    flow_configs["items"], productos_faltantes, logger
                )

                if all_items:
                    missing_data = [
                        row for row in all_items if str(row.get("referencia", "")) in productos_faltantes
                    ]
                    if missing_data:
                        logger.info(
                            f"Resolve Masters | {len(missing_data)} productos encontrados en ERP, creando en Odoo"
                        )
                        processor = ProcessItems(odoo, config, flow_configs["items"])
                        result = processor.process(missing_data)
                        resumen["productos_resueltos"] = result.get("creados", 0)

                        no_encontrados = productos_faltantes - {
                            str(row["referencia"]) for row in missing_data
                        }
                        for ref in no_encontrados:
                            resumen["no_resueltos"].append({
                                "tipo": "producto", "referencia": ref,
                                "razon": "No existe en el ERP"
                            })
                    else:
                        for ref in productos_faltantes:
                            resumen["no_resueltos"].append({
                                "tipo": "producto", "referencia": ref,
                                "razon": "No existe en el ERP"
                            })
                else:
                    logger.warning("Resolve Masters | ERP no retornó datos de productos")
                    for ref in productos_faltantes:
                        resumen["no_resueltos"].append({
                            "tipo": "producto", "referencia": ref,
                            "razon": "ERP no retornó datos"
                        })
            except Exception as e:
                logger.error(f"Resolve Masters | Error resolviendo productos: {e}")

        # Proveedores faltantes
        if proveedores_faltantes and flow_configs.get("supplier"):
            try:
                logger.info(
                    f"Resolve Masters | Consultando ERP por {len(proveedores_faltantes)} proveedores faltantes"
                )
                all_suppliers = _query_erp_batched(
                    transform, connector, "partners",
                    flow_configs["supplier"], {vat for vat, suc in proveedores_faltantes}, logger
                )

                if all_suppliers:
                    vats_faltantes = {vat for vat, suc in proveedores_faltantes}
                    missing_data = [
                        row for row in all_suppliers
                        if row.get("identificacion") in vats_faltantes
                    ]
                    if missing_data:
                        logger.info(
                            f"Resolve Masters | {len(missing_data)} proveedores encontrados en ERP, creando en Odoo"
                        )
                        processor = ProcessPartners(odoo, config, flow_configs["supplier"])
                        result = processor.process(missing_data)
                        resumen["proveedores_resueltos"] = result.get("creados", 0)

                        no_encontrados = proveedores_faltantes - {
                            (row["identificacion"], row.get("sucursal", ""))
                            for row in missing_data
                        }
                        for vat, suc in no_encontrados:
                            resumen["no_resueltos"].append({
                                "tipo": "proveedor", "identificacion": vat,
                                "sucursal": suc, "razon": "No existe en el ERP"
                            })
                    else:
                        for vat, suc in proveedores_faltantes:
                            resumen["no_resueltos"].append({
                                "tipo": "proveedor", "identificacion": vat,
                                "sucursal": suc, "razon": "No existe en el ERP"
                            })
                else:
                    logger.warning("Resolve Masters | ERP no retornó datos de proveedores")
                    for vat, suc in proveedores_faltantes:
                        resumen["no_resueltos"].append({
                            "tipo": "proveedor", "identificacion": vat, "sucursal": suc,
                            "razon": "ERP no retornó datos"
                        })
            except Exception as e:
                logger.error(f"Resolve Masters | Error resolviendo proveedores: {e}")

        # Clientes faltantes
        if clientes_faltantes and flow_configs.get("customer"):
            try:
                logger.info(
                    f"Resolve Masters | Consultando ERP por {len(clientes_faltantes)} clientes faltantes"
                )
                all_customers = _query_erp_batched(
                    transform, connector, "partners",
                    flow_configs["customer"], {vat for vat, suc in clientes_faltantes}, logger
                )

                if all_customers:
                    vats_faltantes = {vat for vat, suc in clientes_faltantes}
                    missing_data = [
                        row for row in all_customers
                        if row.get("identificacion") in vats_faltantes
                    ]
                    if missing_data:
                        logger.info(
                            f"Resolve Masters | {len(missing_data)} clientes encontrados en ERP, creando en Odoo"
                        )
                        processor = ProcessPartners(odoo, config, flow_configs["customer"])
                        result = processor.process(missing_data)
                        resumen["clientes_resueltos"] = result.get("creados", 0)

                        no_encontrados = clientes_faltantes - {
                            (row["identificacion"], row.get("sucursal", ""))
                            for row in missing_data
                        }
                        for vat, suc in no_encontrados:
                            resumen["no_resueltos"].append({
                                "tipo": "cliente", "identificacion": vat,
                                "sucursal": suc, "razon": "No existe en el ERP"
                            })
                    else:
                        for vat, suc in clientes_faltantes:
                            resumen["no_resueltos"].append({
                                "tipo": "cliente", "identificacion": vat,
                                "sucursal": suc, "razon": "No existe en el ERP"
                            })
                else:
                    logger.warning("Resolve Masters | ERP no retornó datos de clientes")
                    for vat, suc in clientes_faltantes:
                        resumen["no_resueltos"].append({
                            "tipo": "cliente", "identificacion": vat, "sucursal": suc,
                            "razon": "ERP no retornó datos"
                        })
            except Exception as e:
                logger.error(f"Resolve Masters | Error resolviendo clientes: {e}")

        # Fase 4: Resumen
        logger.info(
            f"Resolve Masters | Resultado: "
            f"{resumen['productos_resueltos']}/{resumen['productos_faltantes']} productos, "
            f"{resumen['proveedores_resueltos']}/{resumen['proveedores_faltantes']} proveedores, "
            f"{resumen['clientes_resueltos']}/{resumen['clientes_faltantes']} clientes resueltos"
        )
        if resumen["no_resueltos"]:
            logger.warning(
                f"Resolve Masters | {len(resumen['no_resueltos'])} maestros no resueltos:"
            )
            for nr in resumen["no_resueltos"]:
                if nr["tipo"] == "producto":
                    logger.warning(f"  - Producto '{nr['referencia']}': {nr['razon']}")
                else:
                    logger.warning(
                        f"  - {nr['tipo'].capitalize()} {nr['identificacion']} "
                        f"(suc={nr.get('sucursal', '')}): {nr['razon']}"
                    )

        return resumen

    except Exception as e:
        logger.error(f"Resolve Masters | Error fatal: {e}")
        resumen["error"] = str(e)
        return resumen


def _query_erp_batched(transform, connector, flow_name, flow_config, faltantes, logger):

    needs_batching = (
        flow_config.get("resolve_filter_field")
        and len(faltantes) > BATCH_SIZE
    )

    if not needs_batching:
        resolved_config = _build_resolve_filter(flow_config, faltantes, logger=logger)
        return transform.get_flow(connector, flow_name, resolved_config)

    faltantes_list = list(faltantes)
    all_results = []
    total_batches = (len(faltantes_list) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(faltantes_list), BATCH_SIZE):
        batch = set(faltantes_list[i:i + BATCH_SIZE])
        batch_num = (i // BATCH_SIZE) + 1
        logger.info(
            f"Resolve Masters | Batch {batch_num}/{total_batches}: {len(batch)} valores"
        )

        resolved_config = _build_resolve_filter(flow_config, batch, logger=logger)
        batch_results = transform.get_flow(connector, flow_name, resolved_config)

        if batch_results:
            all_results.extend(batch_results)

    return all_results if all_results else []


def _build_resolve_filter(flow_config, faltantes, logger=None):

    if not faltantes:
        return flow_config

    # Caso SAP: filtro OData dinámico
    resolve_field = flow_config.get("resolve_filter_field")
    resolve_template = flow_config.get("resolve_filter_template")
    if resolve_field and resolve_template:
        parts = [resolve_template.replace("{ref}", str(ref)) for ref in faltantes]
        dynamic_filter = "(" + " or ".join(parts) + ")"

        new_config = {**flow_config}
        new_config["filter"] = dynamic_filter

        if logger:
            logger.info(f"Resolve Masters | Filtro OData dinámico: {len(faltantes)} valores")
        return new_config

    # Caso WS: inyección SQL dinámica
    resolve_sql = flow_config.get("resolve_sql_inject")
    if resolve_sql and flow_config.get("sql"):
        refs_quoted = ",".join(f'"{str(ref)}"' for ref in faltantes)
        inject_clause = resolve_sql.replace("{refs}", refs_quoted)

        sql = flow_config["sql"]
        order_idx = sql.upper().rfind("ORDER BY")
        if order_idx != -1:
            new_sql = sql[:order_idx] + inject_clause + " " + sql[order_idx:]
        else:
            last_semi = sql.rfind(";")
            if last_semi != -1:
                new_sql = sql[:last_semi] + " " + inject_clause + sql[last_semi:]
            else:
                new_sql = sql + " " + inject_clause

        new_config = {**flow_config}
        new_config["sql"] = new_sql

        if logger:
            logger.info(f"Resolve Masters | Filtro SQL dinámico: {len(faltantes)} valores")
        return new_config

    # Sin resolve: retorna sin cambios
    return flow_config
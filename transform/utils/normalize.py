"""
normalize — Pipeline genérico de normalización.
Funciones standalone que reciben todo por parámetro.
Fase: 3 — Transform Layer
"""
from transform.utils.helpers import (
    clean_row, validate_record, to_float, to_int, parse_fecha,
)
from transform.utils.defaults import get_normalize_config
from transform.utils.documentos import preparar_documentos, procesar_fila
from transform.utils.determination_functions import get_determination_function


def apply_mapping(row: dict, mapping: dict) -> dict:
    if not mapping:
        return row
    mapped = {}
    mapped_keys = set()
    for key_origen, key_canon in mapping.items():
        if key_origen in row:
            mapped[key_canon] = row[key_origen]
            mapped_keys.add(key_origen)
    for key, value in row.items():
        if key not in mapped_keys:
            mapped[key] = value
    return mapped


def apply_hardcodes(row: dict, hardcodes: dict) -> dict:
    if not hardcodes:
        return row
    for campo, valor in hardcodes.items():
        row[campo] = valor
    return row


def apply_conditionals(row: dict, conditionals: list, logger=None) -> dict:
    if not conditionals:
        return row

    for cond in conditionals:
        tipo = cond.get("tipo", "")
        campo_destino = cond.get("campo_destino", "")

        if tipo == "reglas":
            campo_origen = cond.get("campo_origen", "")
            reglas = cond.get("reglas", [])
            default = cond.get("default")
            valor_origen = str(row.get(campo_origen, "")).strip()

            resultado = default
            for regla in reglas:
                if str(regla.get("si", "")).strip() == valor_origen:
                    if "entonces" not in regla:
                        if logger:
                            logger.error(
                                f"apply_conditionals: regla sin 'entonces' para "
                                f"campo_destino '{campo_destino}' — regla: {regla}"
                            )
                        break
                    resultado = regla["entonces"]
                    break

            if resultado is not None:
                row[campo_destino] = resultado
            else:
                if logger:
                    logger.warning(
                        f"apply_conditionals: ninguna regla matcheó para "
                        f"campo_destino '{campo_destino}' y no hay default configurado"
                    )

        elif tipo == "funcion":
            nombre_fn = cond.get("funcion", "")
            params = cond.get("params", {})
            fn = get_determination_function(nombre_fn, logger=logger)
            if fn:
                row[campo_destino] = fn(row, params, logger=logger)

    return row


def normalize(raw, flow_config, flow_type, logger, descartados,
              use_conditionals=False):
    """Pipeline genérico: mapping → hardcodes → conditionals → documentos
    → clean → validate → tipado.

    Parámetros:
        raw: lista de dicts crudos del conector
        flow_config: dict con toda la configuración del flow
        flow_type: str (items, customer, supplier, purchases, sales)
        logger: IntegradorLogger
        descartados: lista mutable donde se agregan los rechazados
        use_conditionals: si True, aplica conditionals del flow_config

    Retorna: lista de dicts normalizados listos para el core.
    """
    cfg = get_normalize_config(flow_config, flow_type)

    mapping = flow_config.get("mapping", {})
    hardcodes = flow_config.get("hardcodes", {})
    conditionals = flow_config.get("conditionals", [])

    docs_activos, stats_docs = preparar_documentos(
        flow_config.get("documentos"), logger=logger
    )

    results = []
    fallidos = []

    campo_id = cfg["campos_obligatorios"][0] if cfg["campos_obligatorios"] else "referencia"

    for row in raw:
        try:
            row = apply_mapping(row, mapping)
            row = apply_hardcodes(row, hardcodes)

            if use_conditionals and conditionals:
                row = apply_conditionals(row, conditionals, logger=logger)

            row = procesar_fila(row, docs_activos, stats_docs, logger=logger)
            if row is None:
                continue

            row = clean_row(row)

            valid, detalle = validate_record(
                row,
                cfg["campos_obligatorios"],
                campos_mayor_cero=cfg["campos_mayor_cero"],
                campos_default_cero=cfg["campos_default_cero"],
                logger=logger,
            )
            if not valid:
                fallidos.append({
                    campo_id: row.get(campo_id, "?"),
                    "etapa": "validacion",
                    **detalle,
                })
                continue

            for campo in cfg["campos_float"] & row.keys():
                row[campo] = to_float(row[campo], logger=logger, field_name=campo)

            for campo in cfg["campos_int"] & row.keys():
                row[campo] = to_int(row[campo], logger=logger, field_name=campo)

            for campo in cfg["campos_fecha"] & row.keys():
                row[campo] = parse_fecha(row[campo], logger=logger)

            results.append(row)

        except Exception as e:
            fallidos.append({
                campo_id: row.get(campo_id, "?"),
                "etapa": "validacion",
                "campo": "excepcion",
                "razon": str(e),
                "valor_recibido": "",
            })
            continue

    logger.info(f"normalize: {len(results)}/{len(raw)} registros validos")
    if fallidos:
        logger.warning(f"normalize: {len(fallidos)} registros descartados:")
        for f in fallidos:
            logger.warning(f"  - {f.get(campo_id, '?')}: {f.get('razon', '?')}")
        descartados.extend(fallidos)
    if docs_activos:
        detalle = ", ".join(
            f"{cod}: {d['aceptados']} ok / {d['descartados']} descartados"
            for cod, d in stats_docs.items() if not cod.startswith("_")
        )
        logger.info(
            f"normalize: documentos — {detalle}, "
            f"sin documento: {stats_docs['_sin_documento']}"
        )
    return results

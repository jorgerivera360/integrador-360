OPERADORES = ("=", "!=", "in", "contiene", "empieza_con")


def evaluar_condicion(row: dict, condicion: dict, logger=None) -> bool:
    campo = condicion.get("campo", "")
    operador = condicion.get("operador", "=")
    esperado = condicion.get("valor")

    if not campo:
        if logger:
            logger.warning("evaluar_condicion: condicion sin 'campo' — se evalua como falsa")
        return False

    actual = str(row.get(campo, "") or "").strip()

    if operador == "=":
        return actual == str(esperado or "").strip()

    if operador == "!=":
        return actual != str(esperado or "").strip()

    if operador == "in":
        if not isinstance(esperado, (list, tuple)):
            if logger:
                logger.warning(
                    f"evaluar_condicion: el operador 'in' requiere una lista en 'valor' "
                    f"para el campo '{campo}' — se evalua como falsa"
                )
            return False
        return actual in [str(v or "").strip() for v in esperado]

    if operador == "contiene":
        return str(esperado or "").strip() in actual

    if operador == "empieza_con":
        return actual.startswith(str(esperado or "").strip())

    if logger:
        logger.warning(
            f"evaluar_condicion: operador desconocido '{operador}' "
            f"para el campo '{campo}' — se evalua como falsa"
        )
    return False


def _documentos_activos(documentos: list, logger=None) -> list:
    activos = []
    for indice, doc in enumerate(documentos or []):
        if not isinstance(doc, dict):
            if logger:
                logger.warning(f"documentos: el elemento #{indice} no es un dict, se omite")
            continue
        if doc.get("activo", True) is False:
            continue
        activos.append(doc)
    return activos


def clasificar_documento(row: dict, documentos: list, logger=None) -> dict:
    for doc in documentos:
        identificar_por = doc.get("identificar_por")
        if not identificar_por:
            if logger:
                logger.warning(
                    f"clasificar_documento: el documento "
                    f"'{doc.get('codigo', '?')}' no tiene 'identificar_por' — se omite"
                )
            continue
        if evaluar_condicion(row, identificar_por, logger=logger):
            return doc
    return None


def _validar_campos(row: dict, documentos: list, logger=None) -> None:
    if not logger:
        return
    disponibles = set(row.keys())
    referenciados = set()
    for doc in documentos:
        ident = doc.get("identificar_por") or {}
        if ident.get("campo"):
            referenciados.add(ident["campo"])
        for filtro in doc.get("filtros") or []:
            if isinstance(filtro, dict) and filtro.get("campo"):
                referenciados.add(filtro["campo"])
        for regla in doc.get("reglas") or []:
            if isinstance(regla, dict):
                for filtro in regla.get("filtros") or []:
                    if isinstance(filtro, dict) and filtro.get("campo"):
                        referenciados.add(filtro["campo"])
    faltantes = referenciados - disponibles
    if faltantes:
        logger.warning(
            f"aplicar_documentos: estos campos estan configurados en los documentos "
            f"pero no llegan en el dato: {sorted(faltantes)} — "
            f"campos disponibles: {sorted(disponibles)}"
        )


def _inyectar_meta(row: dict, fuente: dict) -> None:
    for clave in ("method", "operacion_id", "estado", "crear_como", "warehouse_mapping"):
        valor = fuente.get(clave)
        if valor is not None:
            row[f"_{clave}"] = valor


def preparar_documentos(documentos: list, logger=None) -> tuple:
    activos = _documentos_activos(documentos, logger=logger)
    if documentos and not activos and logger:
        logger.warning(
            "preparar_documentos: el flujo declara documentos pero ninguno "
            "quedo activo — las filas pasan sin cambios"
        )
    stats = {}
    for i, doc in enumerate(activos):
        codigo = doc.get("codigo", f"#{i}")
        entry = {"aceptados": 0, "descartados": 0}
        if doc.get("reglas"):
            entry["reglas_sin_match"] = 0
        stats[codigo] = entry
    stats["_sin_documento"] = 0
    stats["_validado"] = False
    return activos, stats


def procesar_fila(row: dict, activos: list, stats: dict, logger=None):
    if not activos:
        return row

    if not stats.get("_validado"):
        _validar_campos(row, activos, logger=logger)
        stats["_validado"] = True

    doc = clasificar_documento(row, activos, logger=logger)

    if doc is None:
        stats["_sin_documento"] += 1
        return row

    codigo = doc.get("codigo", "?")

    reglas = doc.get("reglas")
    if reglas:
        # --- Modo reglas: evaluar if/elif ---
        regla_ganadora = None
        for regla in reglas:
            if not isinstance(regla, dict):
                continue
            filtros_regla = regla.get("filtros") or []
            if all(evaluar_condicion(row, f, logger=logger) for f in filtros_regla):
                regla_ganadora = regla
                break

        if regla_ganadora is None:
            stats[codigo]["descartados"] += 1
            stats[codigo]["reglas_sin_match"] += 1
            return None

        for campo, valor in (regla_ganadora.get("hardcodes") or {}).items():
            row[campo] = valor

        _inyectar_meta(row, regla_ganadora)
        stats[codigo]["aceptados"] += 1
        return row

    # --- Modo simple (sin reglas): comportamiento original ---
    if not all(evaluar_condicion(row, f, logger=logger) for f in doc.get("filtros") or []):
        stats[codigo]["descartados"] += 1
        return None

    for campo, valor in (doc.get("hardcodes") or {}).items():
        row[campo] = valor

    _inyectar_meta(row, doc)
    stats[codigo]["aceptados"] += 1
    return row

"""
Ensamblador de SQL desde bloques.

Recibe un bloque base + bloques de campo + bloques de filtro con sus variables
resueltas y genera el SQL completo que transform_ws.py consume.
"""

import re


def _resolve_variables(fragment, variables_def, variables_values):
    """Reemplaza {nombre} en el fragmento con los valores provistos."""
    result = fragment
    for var in variables_def:
        name = var.get("name", "")
        value = str(variables_values.get(name, var.get("default", "")))

        if var.get("type") == "list":
            items = [v.strip() for v in value.split(",") if v.strip()]
            value = ", ".join(f'"{item}"' for item in items)

        result = result.replace(f"{{{name}}}", value)
    return result


def _extract_base_parts(select_fragment):
    """
    Separa el select_fragment de un bloque base en sus partes.

    El bloque base contiene todo: SET, SELECT, FROM, JOINs, GROUP BY.
    Retorna un dict con las partes separadas para poder inyectar campos,
    JOINs y WHERE adicionales.
    """
    text = select_fragment.strip()

    prefix = ""
    body = text
    set_match = re.match(r"(SET\s+QUOTED_IDENTIFIER\s+\w+\s*;?\s*)", body, re.IGNORECASE)
    if set_match:
        prefix = set_match.group(1).strip() + "\n"
        body = body[set_match.end():]

    group_by = ""
    group_match = re.search(r"\bGROUP\s+BY\b(.+)$", body, re.IGNORECASE | re.DOTALL)
    if group_match:
        group_by = group_match.group(1).strip().rstrip(";").strip()
        body = body[:group_match.start()].strip()

    where_part = ""
    where_match = re.search(r"\bWHERE\b(.+)$", body, re.IGNORECASE | re.DOTALL)
    if where_match:
        where_part = where_match.group(1).strip()
        body = body[:where_match.start()].strip()

    select_part = ""
    from_part = ""
    from_match = re.search(r"\bFROM\b", body, re.IGNORECASE)
    if from_match:
        select_part = body[:from_match.start()].strip()
        from_part = body[from_match.start():].strip()
    else:
        select_part = body

    return {
        "prefix": prefix,
        "select": select_part,
        "from": from_part,
        "where": where_part,
        "group_by": group_by,
    }


def assemble_sql(base_block, campo_blocks, filtro_blocks):
    """
    Ensambla un SQL completo desde bloques.

    Args:
        base_block: dict con el bloque base (block_type='base').
            Debe incluir 'select_fragment', 'variables', y opcionalmente
            'variables_values' con los valores del flow.
        campo_blocks: lista de dicts, cada uno con:
            - select_fragment, join_fragment, group_by_fragment, variables
            - variables_values: dict con valores del flow
        filtro_blocks: lista de dicts, cada uno con:
            - where_fragment, variables
            - variables_values: dict con valores del flow

    Returns:
        str: SQL completo ensamblado.
    """
    if not base_block or not base_block.get("select_fragment"):
        return ""

    base_vars = base_block.get("variables", [])
    base_values = base_block.get("variables_values", {})
    base_fragment = _resolve_variables(
        base_block["select_fragment"], base_vars, base_values
    )

    parts = _extract_base_parts(base_fragment)

    extra_selects = []
    extra_joins = []
    extra_group_bys = []

    for campo in campo_blocks:
        if not campo.get("select_fragment"):
            continue

        c_vars = campo.get("variables", [])
        c_values = campo.get("variables_values", {})

        select_frag = _resolve_variables(
            campo["select_fragment"], c_vars, c_values
        ).strip()
        if select_frag:
            extra_selects.append(select_frag)

        join_frag = _resolve_variables(
            campo.get("join_fragment", ""), c_vars, c_values
        ).strip()
        if join_frag:
            extra_joins.append(join_frag)

        gb_frag = _resolve_variables(
            campo.get("group_by_fragment", ""), c_vars, c_values
        ).strip()
        if gb_frag:
            extra_group_bys.append(gb_frag)

    where_conditions = []
    if parts["where"]:
        where_conditions.append(parts["where"])

    for filtro in filtro_blocks:
        if not filtro.get("where_fragment"):
            continue

        f_vars = filtro.get("variables", [])
        f_values = filtro.get("variables_values", {})

        where_frag = _resolve_variables(
            filtro["where_fragment"], f_vars, f_values
        ).strip()
        if where_frag:
            where_conditions.append(where_frag)

    sql = parts["prefix"]

    sql += parts["select"]
    for sel in extra_selects:
        sql += ",\n    " + sel

    sql += "\n" + parts["from"]
    for join in extra_joins:
        sql += "\n" + join

    if where_conditions:
        sql += "\nWHERE " + "\n    AND ".join(where_conditions)

    all_group_bys = []
    if parts["group_by"]:
        all_group_bys.append(parts["group_by"])
    all_group_bys.extend(extra_group_bys)

    if all_group_bys:
        sql += "\nGROUP BY " + ", ".join(all_group_bys)

    sql += ";\nSET QUOTED_IDENTIFIER ON;"

    return sql


def assemble_from_flow_config(flow_config, db_cursor):
    """
    Lee los bloques desde la BD y ensambla el SQL para un flow en modo visual.

    Args:
        flow_config: dict con sql_mode, sql_base_id, sql_campos, sql_filtros
        db_cursor: cursor de PostgreSQL con RealDictCursor

    Returns:
        str: SQL ensamblado, o "" si no se puede ensamblar.
    """
    if flow_config.get("sql_mode") != "visual":
        return flow_config.get("sql", "")

    base_id = flow_config.get("sql_base_id")
    if not base_id:
        return ""

    block_ids = [base_id]
    campos_config = flow_config.get("sql_campos", [])
    filtros_config = flow_config.get("sql_filtros", [])

    for c in campos_config:
        if c.get("block_id"):
            block_ids.append(c["block_id"])
    for f in filtros_config:
        if f.get("block_id"):
            block_ids.append(f["block_id"])

    if not block_ids:
        return ""

    db_cursor.execute(
        "SELECT * FROM sql_blocks WHERE id = ANY(%s) AND is_active = true",
        (block_ids,)
    )
    blocks_by_id = {row["id"]: row for row in db_cursor.fetchall()}

    base_block = blocks_by_id.get(base_id)
    if not base_block:
        return ""

    base_block["variables_values"] = flow_config.get("sql_base_variables", {})

    campo_blocks = []
    for c in campos_config:
        block = blocks_by_id.get(c.get("block_id"))
        if block:
            campo_blocks.append({
                **block,
                "variables_values": c.get("variables", {}),
            })

    filtro_blocks = []
    for f in filtros_config:
        block = blocks_by_id.get(f.get("block_id"))
        if block:
            filtro_blocks.append({
                **block,
                "variables_values": f.get("variables", {}),
            })

    return assemble_sql(base_block, campo_blocks, filtro_blocks)

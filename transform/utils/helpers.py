import re
from datetime import datetime
from typing import Optional, Tuple
import calendar


def parse_fecha(fecha_str: str, formato: str = "%Y%m%d", logger=None) -> str:
      if not fecha_str or not isinstance(fecha_str, str):
          return ""
      fecha_str = fecha_str.strip()
      if not fecha_str:
          return ""

      # Intento directo con el formato proporcionado
      try:
          return datetime.strptime(fecha_str, formato).strftime("%Y-%m-%d")
      except (ValueError, TypeError):
          pass

      # Auto-detección: 8 dígitos puros -> %Y%m%d
      if len(fecha_str) == 8 and fecha_str.isdigit():
          try:
              return datetime.strptime(fecha_str, "%Y%m%d").strftime("%Y-%m-%d")
          except ValueError:
              pass

      # ISO 8601 con T (con o sin microsegundos, con o sin Z/offset)
      if "T" in fecha_str:
          limpia = fecha_str.split(".")[0]
          limpia = limpia.replace("Z", "")
          try:
              return datetime.strptime(limpia, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
          except ValueError:
              pass

      # Fallback: formatos comunes restantes
      for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"):
          try:
              return datetime.strptime(fecha_str, fmt).strftime("%Y-%m-%d")
          except (ValueError, TypeError):
              continue

      if logger:
          logger.warning(
              f"parse_fecha: no se pudo parsear '{fecha_str}' con formato '{formato}'"
          )
      return ""

def clean_string(value) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    return "".join(c for c in s if c.isprintable())

def to_float(value, default: float = 0.0, logger=None, field_name: str = "") -> float:

    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        if logger:
            logger.warning(
                f"to_float: no se pudo convertir '{value}' en campo "
                f"'{field_name}', usando default {default}"
            )
        return default

def to_int(value, default: int = 0, logger=None, field_name: str = "") -> int:

      if value is None or value == "":
          return default
      try:
          return int(float(value))
      except (ValueError, TypeError):
          if logger:
              logger.warning(
                  f"to_int: no se pudo convertir '{value}' en campo "
                  f"'{field_name}', usando default {default}"
              )
          return default

def split_codes(value: str, separator: str = ",") -> list:

      if not value or not isinstance(value, str):
          return []
      return [code.strip() for code in value.split(separator) if code.strip()]

def clean_row(row: dict) -> dict:
      
      cleaned = {}
      for k, v in row.items():
          if isinstance(v, str):
              cleaned[k] = clean_string(v)
          else:
              cleaned[k] = v
      return cleaned

def validate_record(row: dict, entity_type: str, logger=None) -> Tuple[bool, str]:

    ENTIDADES_VALIDAS = ("items", "partners", "purchases", "sales")

    if entity_type not in ENTIDADES_VALIDAS:
        if logger:
            logger.error(
                f"validate_record: entity_type desconocido '{entity_type}' — "
                f"registro descartado. Validos: {', '.join(ENTIDADES_VALIDAS)}"
            )
        return False, f"entity_type desconocido: '{entity_type}'"

    if entity_type == "items":
        ref = row.get("referencia", "")
        if not ref or not str(ref).strip():
            if logger:
                logger.warning(
                    f"validate_record: item descartado — referencia vacía "
                    f"— datos recibidos: {row}"
                )
            return False, "referencia vacía"
        desc = row.get("descripcion", "")
        if not desc or not str(desc).strip():
            if logger:
                logger.warning(
                    f"validate_record: item descartado — descripcion vacía "
                    f"para referencia '{ref}' — datos recibidos: {row}"
                )
            return False, "descripcion vacía"

    elif entity_type == "partners":
        nombre = row.get("nombre", "")
        identificacion = row.get("identificacion", "")
        if not nombre or not str(nombre).strip():
            if logger:
                logger.warning(
                    f"validate_record: partner descartado — nombre vacío "
                    f"— datos recibidos: {row}"
                )
            return False, "nombre vacío"
        if not identificacion or not str(identificacion).strip():
            if logger:
                logger.warning(
                    f"validate_record: partner descartado — identificacion "
                    f"vacía para nombre '{nombre}' — datos recibidos: {row}"
                )
            return False, "identificacion vacía"

    elif entity_type == "purchases":
        compra = row.get("compra", "")
        if not compra or not str(compra).strip():
            if logger:
                logger.warning(
                    f"validate_record: purchase descartado — compra vacía "
                    f"— datos recibidos: {row}"
                )
            return False, "compra vacía"
        producto = row.get("producto", "")
        if not producto or not str(producto).strip():
            if logger:
                logger.warning(
                    f"validate_record: línea descartada — producto vacío "
                    f"en compra '{compra}' — datos recibidos: {row}"
                )
            return False, "producto vacío"
        proveedor = row.get("proveedor", "")
        if not proveedor or not str(proveedor).strip():
            if logger:
                logger.warning(
                    f"validate_record: purchase descartado — proveedor vacío "
                    f"en compra '{compra}' — datos recibidos: {row}"
                )
            return False, "proveedor vacío"
        sucursal_proveedor = row.get("sucursal_proveedor", "")
        if not sucursal_proveedor or not str(sucursal_proveedor).strip():
            if logger:
                logger.warning(
                    f"validate_record: purchase descartado — sucursal_proveedor vacía "
                    f"en compra '{compra}' — datos recibidos: {row}"
                )
            return False, "sucursal_proveedor vacía"
        fecha_entrega = row.get("fecha_entrega", "")
        if not fecha_entrega or not str(fecha_entrega).strip():
            if logger:
                logger.warning(
                    f"validate_record: purchase descartado — fecha_entrega vacía "
                    f"en compra '{compra}' — datos recibidos: {row}"
                )
            return False, "fecha_entrega vacía"
        estado = row.get("estado", "")
        if not estado or not str(estado).strip():
            if logger:
                logger.warning(
                    f"validate_record: purchase descartado — estado vacío "
                    f"en compra '{compra}' — datos recibidos: {row}"
                )
            return False, "estado vacío"
        almacen = row.get("almacen", "")
        if not almacen or not str(almacen).strip():
            if logger:
                logger.warning(
                    f"validate_record: purchase descartado — almacen vacío "
                    f"en compra '{compra}' — datos recibidos: {row}"
                )
            return False, "almacen vacío"
        if row.get("precio_unitario") is None or str(row.get("precio_unitario", "")).strip() == "":
            row["precio_unitario"] = 0
        cantidad = row.get("cantidad")
        if cantidad is None or str(cantidad).strip() == "":
            if logger:
                logger.warning(
                    f"validate_record: línea descartada - cantidad ausente "
                    f"en compra '{compra}' - datos recibidos: {row}"
                )
            return False, "cantidad ausente"
        try:
            if float(cantidad) <= 0:
                if logger:
                    logger.warning(
                        f"validate_record: línea descartada — "
                        f"cantidad <= 0 en compra '{compra}' "
                        f"— datos recibidos: {row}"
                    )
                return False, "cantidad <= 0"
        except (ValueError, TypeError):
            if logger:
                logger.error(
                    f"validate_record: línea descartada — cantidad no "
                    f"numérica '{cantidad}' en compra '{compra}' "
                    f"— datos recibidos: {row}"
                )
            return False, f"cantidad no numérica: {cantidad}"
    elif entity_type == "sales":
        pedido = row.get("pedido", "")
        if not pedido or not str(pedido).strip():
            if logger:
                logger.warning(
                    f"validate_record: sale descartado — pedido vacío "
                    f"— datos recibidos: {row}"
                )
            return False, "pedido vacío"
        producto = row.get("producto", "")
        if not producto or not str(producto).strip():
            if logger:
                logger.warning(
                    f"validate_record: línea descartada — producto vacío "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "producto vacío"
        cliente = row.get("cliente", "")
        if not cliente or not str(cliente).strip():
            if logger:
                logger.warning(
                    f"validate_record: sale descartado — cliente vacío "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "cliente vacío"
        sucursal_cliente = row.get("sucursal_cliente", "")
        if not sucursal_cliente or not str(sucursal_cliente).strip():
            if logger:
                logger.warning(
                    f"validate_record: sale descartado — sucursal_cliente vacía "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "sucursal_cliente vacía"
        fecha_pedido = row.get("fecha_pedido", "")
        if not fecha_pedido or not str(fecha_pedido).strip():
            if logger:
                logger.warning(
                    f"validate_record: sale descartado — fecha_pedido vacía "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "fecha_pedido vacía"
        estado = row.get("estado", "")
        if not estado or not str(estado).strip():
            if logger:
                logger.warning(
                    f"validate_record: sale descartado — estado vacío "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "estado vacío"
        almacen = row.get("almacen", "")
        if not almacen or not str(almacen).strip():
            if logger:
                logger.warning(
                    f"validate_record: sale descartado — almacen vacío "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "almacen vacío"
        if row.get("precio_unitario") is None or str(row.get("precio_unitario", "")).strip() == "":
            row["precio_unitario"] = 0
        cantidad = row.get("cantidad_pedida")
        if cantidad is None or str(cantidad).strip() == "":
            if logger:
                logger.warning(
                    f"validate_record: línea descartada — cantidad_pedida ausente "
                    f"en pedido '{pedido}' — datos recibidos: {row}"
                )
            return False, "cantidad_pedida ausente"
        try:
            if float(cantidad) <= 0:
                if logger:
                    logger.warning(
                        f"validate_record: línea descartada — "
                        f"cantidad_pedida <= 0 en pedido '{pedido}' "
                        f"— datos recibidos: {row}"
                    )
                return False, "cantidad_pedida <= 0"
        except (ValueError, TypeError):
            if logger:
                logger.error(
                    f"validate_record: línea descartada — cantidad_pedida no "
                    f"numérica '{cantidad}' en pedido '{pedido}' "
                    f"— datos recibidos: {row}"
                )
            return False, f"cantidad_pedida no numérica: {cantidad}"
    return True, ""

def resolve_parametros(parametros_str, formato="%Y%m%d", logger=None):
    if not parametros_str or "{" not in parametros_str:
        return parametros_str

    from datetime import timedelta

    hoy = datetime.now()

    def _resolver_placeholder(match):
        placeholder = match.group(1)

        if placeholder == "hoy":
            return hoy.strftime(formato)
        if placeholder.startswith("hoy-"):
            dias = int(placeholder.split("-")[1])
            return (hoy - timedelta(days=dias)).strftime(formato)
        if placeholder.startswith("hoy+"):
            dias = int(placeholder.split("+")[1])
            return (hoy + timedelta(days=dias)).strftime(formato)

        if placeholder == "inicio_mes":
            return hoy.replace(day=1).strftime(formato)
        if placeholder.startswith("inicio_mes-"):
            n = int(placeholder.split("-")[1])
            mes = hoy.month - n
            anio = hoy.year
            while mes <= 0:
                mes += 12
                anio -= 1
            return datetime(anio, mes, 1).strftime(formato)

        if placeholder == "fin_mes":
            ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
            return hoy.replace(day=ultimo_dia).strftime(formato)
        if placeholder.startswith("fin_mes-"):
            n = int(placeholder.split("-")[1])
            mes = hoy.month - n
            anio = hoy.year
            while mes <= 0:
                mes += 12
                anio -= 1
            ultimo_dia = calendar.monthrange(anio, mes)[1]
            return datetime(anio, mes, ultimo_dia).strftime(formato)

        if logger:
            logger.warning(f"Placeholder no reconocido: {{{placeholder}}}")
        return match.group(0)

    resultado = re.sub(r"\{([^}]+)\}", _resolver_placeholder, parametros_str)
    return resultado
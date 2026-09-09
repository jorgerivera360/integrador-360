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

def validate_record(row: dict, entity_type: str, logger=None) -> Tuple[bool, dict]:

    ENTIDADES_VALIDAS = ("items", "partners", "purchases", "sales")

    def _rechazo(campo, razon, valor_recibido=""):
        """Construye dict de rechazo estandarizado y loguea."""
        if logger:
            logger.warning(f"validate_record: {entity_type} descartado: {razon} (datos: {row})")
        return False, {"campo": campo, "razon": razon, "valor_recibido": str(valor_recibido)}

    def _campo_vacio(campo, contexto=""):
        valor = row.get(campo, "")
        if not valor or not str(valor).strip():
            prefijo = f"{contexto}: " if contexto else ""
            return True, _rechazo(campo, f"{prefijo}campo '{campo}' vacio", valor)
        return False, None

    if entity_type not in ENTIDADES_VALIDAS:
        if logger:
            logger.error(f"validate_record: entity_type desconocido '{entity_type}'")
        return False, {"campo": "entity_type", "razon": f"Tipo de entidad desconocido: '{entity_type}'", "valor_recibido": entity_type}

    if entity_type == "items":
        ref = str(row.get("referencia", "")).strip()
        desc = str(row.get("descripcion", "")).strip()
        contexto = f"Producto '{ref or '?'}'"

        vacio, resultado = _campo_vacio("referencia", "Producto")
        if vacio: return resultado
        vacio, resultado = _campo_vacio("descripcion", contexto)
        if vacio: return resultado

    elif entity_type == "partners":
        nombre = str(row.get("nombre", "")).strip()
        ident = str(row.get("identificacion", "")).strip()
        contexto = f"Tercero '{nombre or ident or '?'}'"

        vacio, resultado = _campo_vacio("nombre", "Tercero")
        if vacio: return resultado
        vacio, resultado = _campo_vacio("identificacion", contexto)
        if vacio: return resultado

    elif entity_type == "purchases":
        compra = str(row.get("compra", "")).strip()
        producto = str(row.get("producto", "")).strip()
        contexto = f"Compra '{compra or '?'}'"
        contexto_linea = f"Compra '{compra or '?'}', producto '{producto or '?'}'"

        vacio, resultado = _campo_vacio("compra", "Compra")
        if vacio: return resultado
        vacio, resultado = _campo_vacio("producto", contexto)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("proveedor", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("sucursal_proveedor", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("fecha_entrega", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("estado", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("almacen", contexto_linea)
        if vacio: return resultado

        if row.get("precio_unitario") is None or str(row.get("precio_unitario", "")).strip() == "":
            row["precio_unitario"] = 0

        cantidad = row.get("cantidad")
        if cantidad is None or str(cantidad).strip() == "":
            return _rechazo("cantidad", f"{contexto_linea}: campo 'cantidad' ausente", cantidad)
        try:
            if float(cantidad) <= 0:
                return _rechazo("cantidad", f"{contexto_linea}: cantidad es {cantidad} (debe ser > 0)", cantidad)
        except (ValueError, TypeError):
            return _rechazo("cantidad", f"{contexto_linea}: cantidad no numerica '{cantidad}'", cantidad)

    elif entity_type == "sales":
        pedido = str(row.get("pedido", "")).strip()
        producto = str(row.get("producto", "")).strip()
        contexto = f"Pedido '{pedido or '?'}'"
        contexto_linea = f"Pedido '{pedido or '?'}', producto '{producto or '?'}'"

        vacio, resultado = _campo_vacio("pedido", "Pedido")
        if vacio: return resultado
        vacio, resultado = _campo_vacio("producto", contexto)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("cliente", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("sucursal_cliente", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("fecha_pedido", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("estado", contexto_linea)
        if vacio: return resultado
        vacio, resultado = _campo_vacio("almacen", contexto_linea)
        if vacio: return resultado

        if row.get("precio_unitario") is None or str(row.get("precio_unitario", "")).strip() == "":
            row["precio_unitario"] = 0

        cantidad = row.get("cantidad_pedida")
        if cantidad is None or str(cantidad).strip() == "":
            return _rechazo("cantidad_pedida", f"{contexto_linea}: campo 'cantidad_pedida' ausente", cantidad)
        try:
            if float(cantidad) <= 0:
                return _rechazo("cantidad_pedida", f"{contexto_linea}: cantidad_pedida es {cantidad} (debe ser > 0)", cantidad)
        except (ValueError, TypeError):
            return _rechazo("cantidad_pedida", f"{contexto_linea}: cantidad_pedida no numerica '{cantidad}'", cantidad)

    return True, {}

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
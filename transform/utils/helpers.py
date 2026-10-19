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

def validate_record(row: dict, campos_obligatorios, campos_mayor_cero: set = None,
                    campos_default_cero: set = None, logger=None) -> Tuple[bool, dict]:

    # Caso None o tipo inválido
    if campos_obligatorios is None:
        if logger:
            logger.error("validate_record: campos_obligatorios es None")
        return False, {
            "campo": "entity_type",
            "razon": "Tipo de entidad desconocido: 'None'",
            "valor_recibido": "None",
        }

    # Retrocompatibilidad: si recibe un string (entity_type), resuelve desde defaults
    if isinstance(campos_obligatorios, str):
        from transform.utils.defaults import NORMALIZE_DEFAULTS
        entity_type = campos_obligatorios
        # partners es alias legacy para customer/supplier
        if entity_type == "partners":
            entity_type = "customer"
        defaults = NORMALIZE_DEFAULTS.get(entity_type)
        if defaults is None:
            if logger:
                logger.error(f"validate_record: entity_type desconocido '{campos_obligatorios}'")
            return False, {
                "campo": "entity_type",
                "razon": f"Tipo de entidad desconocido: '{campos_obligatorios}'",
                "valor_recibido": campos_obligatorios,
            }
        campos_obligatorios = defaults.get("campos_obligatorios", [])
        if campos_mayor_cero is None:
            campos_mayor_cero = set(defaults.get("campos_mayor_cero", []))
        if campos_default_cero is None:
            campos_default_cero = set(defaults.get("campos_default_cero", []))

    if campos_default_cero is None:
        campos_default_cero = set()
    if campos_mayor_cero is None:
        campos_mayor_cero = set()

    def _rechazo(campo, razon, valor_recibido=""):
        if logger:
            logger.warning(f"validate_record: descartado: {razon} (datos: {row})")
        return False, {"campo": campo, "razon": razon, "valor_recibido": str(valor_recibido)}

    # 1. Campos obligatorios no vacíos
    for campo in campos_obligatorios:
        valor = row.get(campo, "")
        if not valor or not str(valor).strip():
            return _rechazo(campo, f"campo '{campo}' vacio", valor)

    # 2. Campos que defaultean a 0 si no vienen
    for campo in campos_default_cero:
        if row.get(campo) is None or str(row.get(campo, "")).strip() == "":
            row[campo] = 0

    # 3. Campos que deben ser > 0
    for campo in campos_mayor_cero:
        valor = row.get(campo)
        if valor is None or str(valor).strip() == "":
            return _rechazo(campo, f"campo '{campo}' ausente", valor)
        try:
            if float(valor) <= 0:
                return _rechazo(campo, f"{campo} es {valor} (debe ser > 0)", valor)
        except (ValueError, TypeError):
            return _rechazo(campo, f"{campo} no numerico '{valor}'", valor)

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
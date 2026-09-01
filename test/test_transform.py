"""
test_transform.py — Pruebas de la capa Transform

Cubre:
  - transform/base.py                        contrato Transform(ABC)
  - transform/utils/helpers.py               8 funciones
  - transform/utils/determination_functions.py  catalogo de 7 funciones
  - transform/transform_ws.py                TransformWS
  - transform/transform_connekta.py          TransformConnekta
  - transform/transform_sap.py               TransformSAP

La personalizacion por documento se prueba aparte en test_documentos.py;
aqui solo se verifica que los normalizes la integren.

Fase: 3 — Transform Layer
"""
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

WS_CONFIG = {"client_id": "test_client", "erp": {"tipo": "ws"}}
CONNEKTA_CONFIG = {"client_id": "test_client", "erp": {"tipo": "connekta"}}
SAP_CONFIG = {"client_id": "test_client", "erp": {"tipo": "sap"}}


def conector(status=True, data=None):
    c = MagicMock()
    c.get.return_value = (status, data if data is not None else [])
    c.session_id = "sesion-fake"
    return c


# ==========================================================
# transform/base.py
# ==========================================================

class TestTransformBase:

    def test_no_se_puede_instanciar_la_abstracta(self):
        from transform.base import Transform
        with pytest.raises(TypeError):
            Transform()

    def test_subclase_sin_get_flow_no_se_puede_instanciar(self):
        from transform.base import Transform

        class SinGetFlow(Transform):
            pass

        with pytest.raises(TypeError):
            SinGetFlow()

    def test_subclase_con_get_flow_si_se_instancia(self):
        from transform.base import Transform

        class Completa(Transform):
            def get_flow(self, connector, flow_name, flow_type, flow_config):
                return []

        assert Completa() is not None

    def test_get_flow_recibe_cuatro_parametros(self):
        import inspect
        from transform.base import Transform
        firma = inspect.signature(Transform.get_flow)
        assert list(firma.parameters) == [
            "self", "connector", "flow_name", "flow_type", "flow_config"
        ]


# ==========================================================
# helpers.py — parse_fecha
# ==========================================================

class TestParseFecha:

    def test_formato_yyyymmdd(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("20260115") == "2026-01-15"

    def test_formato_explicito(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("15/01/2026", formato="%d/%m/%Y") == "2026-01-15"

    def test_iso_con_t(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("2026-01-15T14:30:00") == "2026-01-15"

    def test_iso_con_milisegundos(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("2026-01-15T14:30:00.123") == "2026-01-15"

    def test_iso_con_z(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("2026-01-15T14:30:00Z") == "2026-01-15"

    def test_solo_fecha_iso(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("2026-01-15") == "2026-01-15"

    def test_fecha_con_hora_sin_t(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("2026-01-15 14:30:00") == "2026-01-15"

    def test_formato_americano(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("01/15/2026") == "2026-01-15"

    def test_string_vacio(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("") == ""

    def test_none(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha(None) == ""

    def test_no_string(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha(12345) == ""

    def test_solo_espacios(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("   ") == ""

    def test_no_parseable_devuelve_vacio(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("no es fecha") == ""

    def test_no_parseable_sin_logger_no_revienta(self):
        from transform.utils.helpers import parse_fecha
        assert parse_fecha("basura") == ""

    def test_no_parseable_loguea_warning(self):
        from transform.utils.helpers import parse_fecha
        logger = MagicMock()
        parse_fecha("basura", logger=logger)
        assert logger.warning.called


# ==========================================================
# helpers.py — clean_string / clean_row
# ==========================================================

class TestCleanString:

    def test_quita_espacios(self):
        from transform.utils.helpers import clean_string
        assert clean_string("  hola  ") == "hola"

    def test_quita_caracteres_no_imprimibles(self):
        from transform.utils.helpers import clean_string
        assert "\x00" not in clean_string("ho\x00la")

    def test_none_devuelve_vacio(self):
        from transform.utils.helpers import clean_string
        assert clean_string(None) == ""

    def test_conserva_texto_normal(self):
        from transform.utils.helpers import clean_string
        assert clean_string("PRODUCTO 123") == "PRODUCTO 123"


class TestCleanRow:

    def test_limpia_los_strings(self):
        from transform.utils.helpers import clean_row
        assert clean_row({"a": "  x  "})["a"] == "x"

    def test_no_toca_los_no_strings(self):
        from transform.utils.helpers import clean_row
        r = clean_row({"n": 5, "f": 1.5, "b": True, "z": None})
        assert r["n"] == 5 and r["f"] == 1.5 and r["b"] is True and r["z"] is None

    def test_dict_vacio(self):
        from transform.utils.helpers import clean_row
        assert clean_row({}) == {}

    def test_conserva_todas_las_claves(self):
        from transform.utils.helpers import clean_row
        assert set(clean_row({"a": "1", "b": 2}).keys()) == {"a", "b"}


# ==========================================================
# helpers.py — to_float / to_int
# ==========================================================

class TestToFloat:

    def test_entero(self):
        from transform.utils.helpers import to_float
        assert to_float(5) == 5.0

    def test_decimal(self):
        from transform.utils.helpers import to_float
        assert to_float(5.5) == 5.5

    def test_string_numerico(self):
        from transform.utils.helpers import to_float
        assert to_float("5.5") == 5.5

    def test_none_devuelve_default(self):
        from transform.utils.helpers import to_float
        assert to_float(None) == 0.0

    def test_vacio_devuelve_default(self):
        from transform.utils.helpers import to_float
        assert to_float("") == 0.0

    def test_no_numerico_devuelve_default(self):
        from transform.utils.helpers import to_float
        assert to_float("abc") == 0.0

    def test_default_personalizado(self):
        from transform.utils.helpers import to_float
        assert to_float("abc", default=9.9) == 9.9

    def test_no_numerico_loguea_warning(self):
        from transform.utils.helpers import to_float
        logger = MagicMock()
        to_float("abc", logger=logger, field_name="precio")
        assert logger.warning.called


class TestToInt:

    def test_entero(self):
        from transform.utils.helpers import to_int
        assert to_int(5) == 5

    def test_string_numerico(self):
        from transform.utils.helpers import to_int
        assert to_int("5") == 5

    def test_float_like_se_trunca(self):
        from transform.utils.helpers import to_int
        assert to_int("5.0") == 5

    def test_float_se_trunca_hacia_abajo(self):
        from transform.utils.helpers import to_int
        assert to_int("5.9") == 5

    def test_none_devuelve_default(self):
        from transform.utils.helpers import to_int
        assert to_int(None) == 0

    def test_no_numerico_devuelve_default(self):
        from transform.utils.helpers import to_int
        assert to_int("abc") == 0

    def test_default_personalizado(self):
        from transform.utils.helpers import to_int
        assert to_int("abc", default=7) == 7

    def test_no_numerico_loguea_warning(self):
        from transform.utils.helpers import to_int
        logger = MagicMock()
        to_int("abc", logger=logger, field_name="vence")
        assert logger.warning.called


class TestSplitCodes:

    def test_separa_por_coma(self):
        from transform.utils.helpers import split_codes
        assert split_codes("a,b,c") == ["a", "b", "c"]

    def test_aplica_strip(self):
        from transform.utils.helpers import split_codes
        assert split_codes(" a , b ") == ["a", "b"]

    def test_filtra_vacios(self):
        from transform.utils.helpers import split_codes
        assert split_codes("a,,b,") == ["a", "b"]

    def test_separador_personalizado(self):
        from transform.utils.helpers import split_codes
        assert split_codes("a|b", separator="|") == ["a", "b"]

    def test_string_vacio(self):
        from transform.utils.helpers import split_codes
        assert split_codes("") == []

    def test_none(self):
        from transform.utils.helpers import split_codes
        assert split_codes(None) == []


# ==========================================================
# helpers.py — validate_record
# ==========================================================

def item_ok():
    return {"referencia": "A1", "descripcion": "Producto"}


def partner_ok():
    return {"nombre": "Cliente", "identificacion": "900"}


def purchase_ok():
    return {
        "compra": "OC-1", "producto": "A1", "proveedor": "900",
        "sucursal_proveedor": "001", "fecha_entrega": "2026-01-01",
        "estado": "draft", "almacen": "1",
        "precio_unitario": 100, "cantidad": 5,
    }


def sale_ok():
    return {
        "pedido": "PV-1", "producto": "A1", "cliente": "900",
        "sucursal_cliente": "001", "fecha_pedido": "2026-01-01",
        "estado": "draft", "almacen": "1",
        "precio_unitario": 100, "cantidad_pedida": 5,
    }


class TestValidateRecordItems:

    def test_valido(self):
        from transform.utils.helpers import validate_record
        assert validate_record(item_ok(), "items")[0] is True

    def test_sin_referencia(self):
        from transform.utils.helpers import validate_record
        r = dict(item_ok(), referencia="")
        assert validate_record(r, "items")[0] is False

    def test_sin_descripcion(self):
        from transform.utils.helpers import validate_record
        r = dict(item_ok(), descripcion="")
        assert validate_record(r, "items")[0] is False

    def test_referencia_solo_espacios(self):
        from transform.utils.helpers import validate_record
        r = dict(item_ok(), referencia="   ")
        assert validate_record(r, "items")[0] is False

    def test_descarte_loguea_warning(self):
        from transform.utils.helpers import validate_record
        logger = MagicMock()
        validate_record(dict(item_ok(), referencia=""), "items", logger=logger)
        assert logger.warning.called


class TestValidateRecordPartners:

    def test_valido(self):
        from transform.utils.helpers import validate_record
        assert validate_record(partner_ok(), "partners")[0] is True

    def test_sin_nombre(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(partner_ok(), nombre=""), "partners")[0] is False

    def test_sin_identificacion(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(partner_ok(), identificacion=""), "partners")[0] is False


class TestValidateRecordPurchases:

    def test_valido(self):
        from transform.utils.helpers import validate_record
        assert validate_record(purchase_ok(), "purchases")[0] is True

    @pytest.mark.parametrize("campo", [
        "compra", "producto", "proveedor", "sucursal_proveedor",
        "fecha_entrega", "estado", "almacen",
    ])
    def test_campo_obligatorio_vacio_descarta(self, campo):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(purchase_ok(), **{campo: ""}), "purchases")[0] is False

    def test_precio_unitario_none_se_convierte_en_cero(self):
        from transform.utils.helpers import validate_record
        r = dict(purchase_ok(), precio_unitario=None)
        valido, _ = validate_record(r, "purchases")
        assert valido is True
        assert r["precio_unitario"] == 0

    def test_precio_unitario_vacio_se_convierte_en_cero(self):
        from transform.utils.helpers import validate_record
        r = dict(purchase_ok(), precio_unitario="")
        validate_record(r, "purchases")
        assert r["precio_unitario"] == 0

    def test_precio_unitario_cero_es_valido(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(purchase_ok(), precio_unitario=0), "purchases")[0] is True

    def test_cantidad_ausente_descarta(self):
        from transform.utils.helpers import validate_record
        r = purchase_ok()
        del r["cantidad"]
        assert validate_record(r, "purchases")[0] is False

    def test_cantidad_cero_descarta(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(purchase_ok(), cantidad=0), "purchases")[0] is False

    def test_cantidad_negativa_descarta(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(purchase_ok(), cantidad=-1), "purchases")[0] is False

    def test_cantidad_no_numerica_descarta(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(purchase_ok(), cantidad="abc"), "purchases")[0] is False

    def test_cantidad_no_numerica_loguea_error(self):
        from transform.utils.helpers import validate_record
        logger = MagicMock()
        validate_record(dict(purchase_ok(), cantidad="abc"), "purchases", logger=logger)
        assert logger.error.called


class TestValidateRecordSales:

    def test_valido(self):
        from transform.utils.helpers import validate_record
        assert validate_record(sale_ok(), "sales")[0] is True

    @pytest.mark.parametrize("campo", [
        "pedido", "producto", "cliente", "sucursal_cliente",
        "fecha_pedido", "estado", "almacen",
    ])
    def test_campo_obligatorio_vacio_descarta(self, campo):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(sale_ok(), **{campo: ""}), "sales")[0] is False

    def test_precio_unitario_none_se_convierte_en_cero(self):
        from transform.utils.helpers import validate_record
        r = dict(sale_ok(), precio_unitario=None)
        validate_record(r, "sales")
        assert r["precio_unitario"] == 0

    def test_cantidad_pedida_cero_descarta(self):
        from transform.utils.helpers import validate_record
        assert validate_record(dict(sale_ok(), cantidad_pedida=0), "sales")[0] is False

    def test_campos_del_groupby_pueden_ir_vacios(self):
        # zona, vendedor, condicion_pago y observacion no son obligatorios
        from transform.utils.helpers import validate_record
        r = dict(sale_ok(), zona="", vendedor="", condicion_pago="", observacion="")
        assert validate_record(r, "sales")[0] is True


class TestValidateRecordEntidadDesconocida:

    def test_entity_type_desconocido_deja_pasar(self):
        # Comportamiento actual: fail-open. Documentado como defecto #5 del
        # informe de correcciones; el test fija la conducta real, no la deseada.
        from transform.utils.helpers import validate_record
        assert validate_record({"cualquier": "cosa"}, "no_existe")[0] is True

    def test_entity_type_vacio_deja_pasar(self):
        from transform.utils.helpers import validate_record
        assert validate_record({}, "")[0] is True


# ==========================================================
# helpers.py — resolve_parametros
# ==========================================================

class TestResolveParametros:

    def test_sin_placeholders_devuelve_igual(self):
        from transform.utils.helpers import resolve_parametros
        assert resolve_parametros("fecha = 20260101") == "fecha = 20260101"

    def test_string_vacio(self):
        from transform.utils.helpers import resolve_parametros
        assert resolve_parametros("") == ""

    def test_none(self):
        from transform.utils.helpers import resolve_parametros
        assert resolve_parametros(None) is None

    def test_hoy(self):
        from transform.utils.helpers import resolve_parametros
        esperado = datetime.now().strftime("%Y%m%d")
        assert resolve_parametros("{hoy}") == esperado

    def test_hoy_menos_dias(self):
        from transform.utils.helpers import resolve_parametros
        esperado = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        assert resolve_parametros("{hoy-7}") == esperado

    def test_hoy_mas_dias(self):
        from transform.utils.helpers import resolve_parametros
        esperado = (datetime.now() + timedelta(days=3)).strftime("%Y%m%d")
        assert resolve_parametros("{hoy+3}") == esperado

    def test_inicio_mes(self):
        from transform.utils.helpers import resolve_parametros
        esperado = datetime.now().replace(day=1).strftime("%Y%m%d")
        assert resolve_parametros("{inicio_mes}") == esperado

    def test_fin_mes_es_el_ultimo_dia(self):
        import calendar
        from transform.utils.helpers import resolve_parametros
        hoy = datetime.now()
        ultimo = calendar.monthrange(hoy.year, hoy.month)[1]
        assert resolve_parametros("{fin_mes}") == hoy.replace(day=ultimo).strftime("%Y%m%d")

    def test_inicio_mes_anterior(self):
        from transform.utils.helpers import resolve_parametros
        r = resolve_parametros("{inicio_mes-1}")
        assert len(r) == 8 and r.endswith("01")

    def test_fin_mes_anterior_tiene_ocho_digitos(self):
        from transform.utils.helpers import resolve_parametros
        assert len(resolve_parametros("{fin_mes-1}")) == 8

    def test_formato_iso_para_sap(self):
        from transform.utils.helpers import resolve_parametros
        esperado = datetime.now().strftime("%Y-%m-%d")
        assert resolve_parametros("{hoy}", formato="%Y-%m-%d") == esperado

    def test_varios_placeholders_en_el_mismo_string(self):
        from transform.utils.helpers import resolve_parametros
        r = resolve_parametros("ini = {inicio_mes}|fin = {hoy}")
        assert "{" not in r and "|" in r

    def test_placeholder_desconocido_queda_igual(self):
        from transform.utils.helpers import resolve_parametros
        assert resolve_parametros("{manana}") == "{manana}"

    def test_placeholder_desconocido_loguea_warning(self):
        from transform.utils.helpers import resolve_parametros
        logger = MagicMock()
        resolve_parametros("{manana}", logger=logger)
        assert logger.warning.called

    def test_conserva_el_texto_alrededor(self):
        from transform.utils.helpers import resolve_parametros
        r = resolve_parametros("FechaInicio = {hoy}")
        assert r.startswith("FechaInicio = ")


# ==========================================================
# determination_functions.py
# ==========================================================

class TestCatalogo:

    def test_tiene_siete_funciones(self):
        from transform.utils.determination_functions import CATALOG
        assert len(CATALOG) == 7

    def test_nombres_del_catalogo(self):
        from transform.utils.determination_functions import CATALOG
        assert set(CATALOG) == {
            "route_compra_manufactura_prefijo", "extraer_prefijo",
            "concatenar_campos", "valor_por_campo", "valor_por_lista",
            "doc_name_por_rango", "sap_field_combined",
        }

    def test_cada_entrada_tiene_metadata_completa(self):
        from transform.utils.determination_functions import CATALOG
        for nombre, entrada in CATALOG.items():
            assert callable(entrada["fn"]), nombre
            assert entrada["label"], nombre
            assert entrada["descripcion"], nombre
            assert isinstance(entrada["params"], list), nombre

    def test_cada_param_tiene_nombre_y_descripcion(self):
        from transform.utils.determination_functions import CATALOG
        for nombre, entrada in CATALOG.items():
            for p in entrada["params"]:
                assert p["name"], nombre
                assert p["descripcion"], nombre
                assert isinstance(p["required"], bool), nombre

    def test_resuelve_funcion_existente(self):
        from transform.utils.determination_functions import get_determination_function
        assert callable(get_determination_function("extraer_prefijo"))

    def test_funcion_inexistente_devuelve_none(self):
        from transform.utils.determination_functions import get_determination_function
        assert get_determination_function("no_existe") is None

    def test_funcion_inexistente_loguea_error(self):
        from transform.utils.determination_functions import get_determination_function
        logger = MagicMock()
        get_determination_function("no_existe", logger=logger)
        assert logger.error.called

    def test_nunca_usa_eval_ni_exec(self):
        import inspect
        from transform.utils import determination_functions
        fuente = inspect.getsource(determination_functions)
        assert "eval(" not in fuente
        assert "exec(" not in fuente


class TestRouteCompraManufacturaPrefijo:

    def _params(self):
        return {
            "campo_compra": "Compra", "campo_manufactura": "Manufactura",
            "campo_referencia": "referencia", "prefijo_manufactura": "PT",
        }

    def test_ambos_indicadores(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "True", "Manufactura": "True", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Buy,Fabricación"

    def test_solo_compra(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "True", "Manufactura": "False", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Buy"

    def test_solo_manufactura(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "False", "Manufactura": "True", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Fabricación"

    def test_ninguno_devuelve_vacio(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "False", "Manufactura": "False", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == ""

    def test_el_prefijo_fuerza_manufactura(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "False", "Manufactura": "False", "referencia": "PT001"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Fabricación"

    def test_acepta_si_ademas_de_true(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "SI", "Manufactura": "NO", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Buy"

    def test_acepta_uno_como_verdadero(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "1", "Manufactura": "0", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Buy"

    def test_no_distingue_mayusculas(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "true", "Manufactura": "false", "referencia": "X1"}
        assert route_compra_manufactura_prefijo(row, self._params()) == "Buy"

    def test_sin_ruta_loguea_info(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        logger = MagicMock()
        row = {"Compra": "No", "Manufactura": "No", "referencia": "X1"}
        route_compra_manufactura_prefijo(row, self._params(), logger=logger)
        assert logger.info.called


class TestExtraerPrefijo:

    def test_prefijo_simple(self):
        from transform.utils.determination_functions import extraer_prefijo
        assert extraer_prefijo({"ref": "PT001"}, {"campo_origen": "ref"}) == "PT"

    def test_prefijo_largo(self):
        from transform.utils.determination_functions import extraer_prefijo
        assert extraer_prefijo({"ref": "ABCD123"}, {"campo_origen": "ref"}) == "ABCD"

    def test_sin_letras_devuelve_vacio(self):
        from transform.utils.determination_functions import extraer_prefijo
        assert extraer_prefijo({"ref": "12345"}, {"campo_origen": "ref"}) == ""

    def test_campo_vacio_devuelve_vacio(self):
        from transform.utils.determination_functions import extraer_prefijo
        assert extraer_prefijo({"ref": ""}, {"campo_origen": "ref"}) == ""

    def test_campo_ausente_loguea_warning(self):
        from transform.utils.determination_functions import extraer_prefijo
        logger = MagicMock()
        extraer_prefijo({}, {"campo_origen": "ref"}, logger=logger)
        assert logger.warning.called

    def test_sin_prefijo_loguea_warning(self):
        from transform.utils.determination_functions import extraer_prefijo
        logger = MagicMock()
        extraer_prefijo({"ref": "123"}, {"campo_origen": "ref"}, logger=logger)
        assert logger.warning.called


class TestConcatenarCampos:

    def test_une_con_separador(self):
        from transform.utils.determination_functions import concatenar_campos
        row = {"co": "001", "tipo": "TEM", "consec": "123"}
        params = {"campos": ["co", "tipo", "consec"], "separador": "-"}
        assert concatenar_campos(row, params) == "001-TEM-123"

    def test_sin_separador(self):
        from transform.utils.determination_functions import concatenar_campos
        params = {"campos": ["a", "b"]}
        assert concatenar_campos({"a": "X", "b": "Y"}, params) == "XY"

    def test_omite_los_campos_vacios(self):
        from transform.utils.determination_functions import concatenar_campos
        row = {"a": "001", "b": "", "c": "123"}
        params = {"campos": ["a", "b", "c"], "separador": "-"}
        assert concatenar_campos(row, params) == "001-123"

    def test_campo_ausente_se_omite(self):
        from transform.utils.determination_functions import concatenar_campos
        params = {"campos": ["a", "no_existe"], "separador": "-"}
        assert concatenar_campos({"a": "001"}, params) == "001"

    def test_lista_vacia_devuelve_vacio(self):
        from transform.utils.determination_functions import concatenar_campos
        assert concatenar_campos({"a": "1"}, {"campos": []}) == ""

    def test_lista_vacia_loguea_warning(self):
        from transform.utils.determination_functions import concatenar_campos
        logger = MagicMock()
        concatenar_campos({}, {"campos": []}, logger=logger)
        assert logger.warning.called


class TestValorPorCampo:

    def _params(self):
        return {"campo_origen": "PurchaseItem", "valor": "tYES",
                "si": "Comprar", "no": "Fabricar"}

    def test_coincide(self):
        from transform.utils.determination_functions import valor_por_campo
        assert valor_por_campo({"PurchaseItem": "tYES"}, self._params()) == "Comprar"

    def test_no_coincide(self):
        from transform.utils.determination_functions import valor_por_campo
        assert valor_por_campo({"PurchaseItem": "tNO"}, self._params()) == "Fabricar"

    def test_campo_ausente_devuelve_el_no(self):
        from transform.utils.determination_functions import valor_por_campo
        assert valor_por_campo({}, self._params()) == "Fabricar"

    def test_aplica_strip(self):
        from transform.utils.determination_functions import valor_por_campo
        assert valor_por_campo({"PurchaseItem": " tYES "}, self._params()) == "Comprar"

    def test_es_sensible_a_mayusculas(self):
        from transform.utils.determination_functions import valor_por_campo
        assert valor_por_campo({"PurchaseItem": "tyes"}, self._params()) == "Fabricar"


class TestValorPorLista:

    def _params(self):
        return {"campo_origen": "ItemsGroupCode", "lista": [307, 313],
                "si": "lot", "no": "none"}

    def test_valor_en_la_lista(self):
        from transform.utils.determination_functions import valor_por_lista
        assert valor_por_lista({"ItemsGroupCode": 307}, self._params()) == "lot"

    def test_valor_fuera_de_la_lista(self):
        from transform.utils.determination_functions import valor_por_lista
        assert valor_por_lista({"ItemsGroupCode": 999}, self._params()) == "none"

    def test_fallback_string_contra_lista_de_enteros(self):
        from transform.utils.determination_functions import valor_por_lista
        assert valor_por_lista({"ItemsGroupCode": "307"}, self._params()) == "lot"

    def test_lista_de_strings(self):
        from transform.utils.determination_functions import valor_por_lista
        params = {"campo_origen": "b", "lista": ["PPAL", "MP"], "si": "s", "no": "n"}
        assert valor_por_lista({"b": "PPAL"}, params) == "s"

    def test_campo_ausente_devuelve_el_no(self):
        from transform.utils.determination_functions import valor_por_lista
        assert valor_por_lista({}, self._params()) == "none"

    def test_lista_vacia_devuelve_el_no(self):
        from transform.utils.determination_functions import valor_por_lista
        params = {"campo_origen": "a", "lista": [], "si": "s", "no": "n"}
        assert valor_por_lista({"a": "x"}, params) == "n"


class TestDocNamePorRango:

    def _params(self):
        return {"campo_origen": "DocNum",
                "rangos": {"1-10000000": "OCNAL", "10000001-20000000": "OCIMP"},
                "separador": "-"}

    def test_primer_rango(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": 3565}, self._params()) == "OCNAL-3565"

    def test_segundo_rango(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": 15000000}, self._params()) == "OCIMP-15000000"

    def test_limite_inferior_incluido(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": 1}, self._params()) == "OCNAL-1"

    def test_limite_superior_incluido(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": 10000000}, self._params()) == "OCNAL-10000000"

    def test_fuera_de_rango_devuelve_vacio(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": 99999999}, self._params()) == ""

    def test_fuera_de_rango_loguea_warning(self):
        from transform.utils.determination_functions import doc_name_por_rango
        logger = MagicMock()
        doc_name_por_rango({"DocNum": 99999999}, self._params(), logger=logger)
        assert logger.warning.called

    def test_valor_no_numerico_devuelve_vacio(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": "abc"}, self._params()) == ""

    def test_valor_no_numerico_loguea_warning(self):
        from transform.utils.determination_functions import doc_name_por_rango
        logger = MagicMock()
        doc_name_por_rango({"DocNum": "abc"}, self._params(), logger=logger)
        assert logger.warning.called

    def test_string_numerico_funciona(self):
        from transform.utils.determination_functions import doc_name_por_rango
        assert doc_name_por_rango({"DocNum": "3565"}, self._params()) == "OCNAL-3565"

    def test_separador_por_defecto_es_guion(self):
        from transform.utils.determination_functions import doc_name_por_rango
        params = {"campo_origen": "DocNum", "rangos": {"1-100": "X"}}
        assert doc_name_por_rango({"DocNum": 5}, params) == "X-5"


class TestSapFieldCombined:

    def _params(self):
        return {"campo1": "U_FB_EnviarWMS", "campo2": "U_FB_EnviarProdWMS",
                "valor_esperado": "Y",
                "texto_ambos": "Producto Terminado, Producción",
                "texto_solo_uno": "Producto Terminado"}

    def test_ambos_coinciden(self):
        from transform.utils.determination_functions import sap_field_combined
        row = {"U_FB_EnviarWMS": "Y", "U_FB_EnviarProdWMS": "Y"}
        assert sap_field_combined(row, self._params()) == "Producto Terminado, Producción"

    def test_solo_el_primero(self):
        from transform.utils.determination_functions import sap_field_combined
        row = {"U_FB_EnviarWMS": "Y", "U_FB_EnviarProdWMS": "N"}
        assert sap_field_combined(row, self._params()) == "Producto Terminado"

    def test_ninguno(self):
        from transform.utils.determination_functions import sap_field_combined
        row = {"U_FB_EnviarWMS": "N", "U_FB_EnviarProdWMS": "N"}
        assert sap_field_combined(row, self._params()) == "Producto Terminado"

    def test_campos_ausentes(self):
        from transform.utils.determination_functions import sap_field_combined
        assert sap_field_combined({}, self._params()) == "Producto Terminado"

    def test_aplica_strip(self):
        from transform.utils.determination_functions import sap_field_combined
        row = {"U_FB_EnviarWMS": " Y ", "U_FB_EnviarProdWMS": "Y"}
        assert sap_field_combined(row, self._params()) == "Producto Terminado, Producción"


# ==========================================================
# TransformWS
# ==========================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformWSGetFlow:

    def _t(self):
        from transform.transform_ws import TransformWS
        return TransformWS(WS_CONFIG)

    def test_flow_type_invalido_devuelve_vacio(self):
        assert self._t().get_flow(conector(), "x", "no_existe", {}) == []

    def test_sin_sql_ni_endpoint_devuelve_vacio(self):
        assert self._t().get_flow(conector(), "items", "items", {}) == []

    def test_con_sql_llama_al_conector(self):
        c = conector(True, [{"referencia": "A1", "descripcion": "P"}])
        self._t().get_flow(c, "items", "items", {"sql": "SELECT 1"})
        assert c.get.call_args.kwargs["endpoint"] == "EjecutarConsultaXML"

    def test_con_sql_pasa_la_consulta(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"sql": "SELECT 1"})
        assert c.get.call_args.kwargs["params"]["sql"] == "SELECT 1"

    def test_con_endpoint_usa_el_camino_excel(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"endpoint": "productos"})
        assert c.get.call_args.kwargs["endpoint"] == "productos"

    def test_endpoint_tiene_prioridad_sobre_sql(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"endpoint": "productos", "sql": "SELECT 1"})
        assert c.get.call_args.kwargs["endpoint"] == "productos"

    def test_conector_falla_devuelve_vacio(self):
        assert self._t().get_flow(conector(False, "error"), "items", "items", {"sql": "S"}) == []

    def test_raw_vacio_devuelve_vacio(self):
        assert self._t().get_flow(conector(True, []), "items", "items", {"sql": "S"}) == []

    def test_excepcion_devuelve_vacio(self):
        c = MagicMock()
        c.get.side_effect = Exception("boom")
        assert self._t().get_flow(c, "items", "items", {"sql": "S"}) == []

    def test_normalize_map_tiene_cinco_flow_types(self):
        from transform.transform_ws import TransformWS
        import inspect
        fuente = inspect.getsource(TransformWS.get_flow)
        for ft in ("items", "customer", "supplier", "purchases", "sales"):
            assert f'"{ft}"' in fuente


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformWSHardcodes:

    def _t(self):
        from transform.transform_ws import TransformWS
        return TransformWS(WS_CONFIG)

    def test_sin_hardcodes_no_modifica(self):
        row = {"a": "1"}
        assert self._t()._apply_hardcodes(row, {}) == {"a": "1"}

    def test_inyecta_campo_nuevo(self):
        assert self._t()._apply_hardcodes({"a": "1"}, {"b": "2"})["b"] == "2"

    def test_pisa_campo_existente(self):
        assert self._t()._apply_hardcodes({"estado": "draft"}, {"estado": "sale"})["estado"] == "sale"

    def test_hardcodes_none_no_revienta(self):
        assert self._t()._apply_hardcodes({"a": "1"}, None) == {"a": "1"}

    def test_se_aplica_antes_de_validar(self):
        # Un registro sin estado se descartaria; el hardcode lo rescata.
        t = self._t()
        fila = dict(sale_ok(), estado="")
        sin = t._normalize_sales([dict(fila)], {})
        con = t._normalize_sales([dict(fila)], {"hardcodes": {"estado": "sale"}})
        assert len(sin) == 0
        assert len(con) == 1


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformWSNormalizes:

    def _t(self):
        from transform.transform_ws import TransformWS
        return TransformWS(WS_CONFIG)

    def test_items_tipa_floats(self):
        raw = [dict(item_ok(), peso="1.5", precio="100.5")]
        r = self._t()._normalize_items(raw, {})
        assert r[0]["peso"] == 1.5 and r[0]["precio"] == 100.5

    def test_items_tipa_enteros(self):
        raw = [dict(item_ok(), vence="30", ind_compra="1")]
        r = self._t()._normalize_items(raw, {})
        assert r[0]["vence"] == 30 and r[0]["ind_compra"] == 1

    def test_items_descarta_invalidos(self):
        raw = [item_ok(), dict(item_ok(), referencia="")]
        assert len(self._t()._normalize_items(raw, {})) == 1

    def test_partners_solo_limpia(self):
        raw = [dict(partner_ok(), nombre="  Cliente  ")]
        assert self._t()._normalize_partners(raw, {})[0]["nombre"] == "Cliente"

    def test_purchases_tipa_y_parsea_fecha(self):
        raw = [dict(purchase_ok(), cantidad="5", fecha_entrega="20260115")]
        r = self._t()._normalize_purchases(raw, {})
        assert r[0]["cantidad"] == 5.0 and r[0]["fecha_entrega"] == "2026-01-15"

    def test_sales_tipa_y_parsea_fecha(self):
        raw = [dict(sale_ok(), cantidad_pedida="5", fecha_pedido="20260115")]
        r = self._t()._normalize_sales(raw, {})
        assert r[0]["cantidad_pedida"] == 5.0 and r[0]["fecha_pedido"] == "2026-01-15"

    def test_raw_vacio_devuelve_lista_vacia(self):
        assert self._t()._normalize_items([], {}) == []

    def test_una_fila_rota_no_tumba_el_resto(self):
        raw = [item_ok(), None, item_ok()]
        assert len(self._t()._normalize_items(raw, {})) == 2

    def test_integra_la_personalizacion_por_documento(self):
        docs = [{
            "codigo": "CDC",
            "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "CDC"},
            "filtros": [],
            "hardcodes": {"estado": "sale"},
        }]
        raw = [dict(sale_ok(), pedido="7-CDC-1"), dict(sale_ok(), pedido="7-CPV-1")]
        r = self._t()._normalize_sales(raw, {"documentos": docs})
        estados = {f["pedido"]: f["estado"] for f in r}
        assert estados["7-CDC-1"] == "sale"
        assert estados["7-CPV-1"] == "draft"

    def test_documento_con_filtro_descarta(self):
        docs = [{
            "codigo": "CPV",
            "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "CPV"},
            "filtros": [{"campo": "almacen", "operador": "=", "valor": "9"}],
            "hardcodes": {},
        }]
        raw = [dict(sale_ok(), pedido="7-CPV-1", almacen="1")]
        assert self._t()._normalize_sales(raw, {"documentos": docs}) == []

    def test_sin_documentos_resultado_identico(self):
        raw = [sale_ok() for _ in range(3)]
        con_clave = self._t()._normalize_sales([dict(f) for f in raw], {"documentos": []})
        sin_clave = self._t()._normalize_sales([dict(f) for f in raw], {})
        assert len(con_clave) == len(sin_clave) == 3


# ==========================================================
# TransformConnekta
# ==========================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformConnektaGetFlow:

    def _t(self):
        from transform.transform_connekta import TransformConnekta
        return TransformConnekta(CONNEKTA_CONFIG)

    def test_flow_type_invalido_devuelve_vacio(self):
        assert self._t().get_flow(conector(), "x", "no_existe", {}) == []

    def test_sin_query_desc_devuelve_vacio(self):
        assert self._t().get_flow(conector(), "items", "items", {}) == []

    def test_pasa_el_query_desc_al_conector(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"query_desc": "consulta_x"})
        assert c.get.call_args.kwargs["params"]["query_desc"] == "consulta_x"

    def test_paginacion_false_activa_no_paginar(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"query_desc": "q", "paginacion": False})
        assert c.get.call_args.kwargs["params"]["no_paginar"] is True

    def test_paginacion_true_desactiva_no_paginar(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"query_desc": "q", "paginacion": True})
        assert c.get.call_args.kwargs["params"]["no_paginar"] is False

    def test_resuelve_los_placeholders_de_parametros(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items",
                           {"query_desc": "q", "parametros": "fecha = {hoy}"})
        assert "{" not in c.get.call_args.kwargs["params"]["parametros"]

    def test_parametros_usa_formato_yyyymmdd(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items",
                           {"query_desc": "q", "parametros": "f = {hoy}"})
        esperado = datetime.now().strftime("%Y%m%d")
        assert esperado in c.get.call_args.kwargs["params"]["parametros"]

    def test_sin_parametros_no_manda_la_clave(self):
        c = conector(True, [])
        self._t().get_flow(c, "items", "items", {"query_desc": "q"})
        assert "parametros" not in c.get.call_args.kwargs["params"]

    def test_conector_falla_devuelve_vacio(self):
        assert self._t().get_flow(conector(False, "err"), "i", "items", {"query_desc": "q"}) == []

    def test_excepcion_devuelve_vacio(self):
        c = MagicMock()
        c.get.side_effect = Exception("boom")
        assert self._t().get_flow(c, "i", "items", {"query_desc": "q"}) == []


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformConnektaMapping:

    def _t(self):
        from transform.transform_connekta import TransformConnekta
        return TransformConnekta(CONNEKTA_CONFIG)

    def test_renombra_los_campos_mapeados(self):
        r = self._t()._apply_mapping({"Referencia_Item": "A1"}, {"Referencia_Item": "referencia"})
        assert r["referencia"] == "A1"

    def test_conserva_los_campos_no_mapeados(self):
        # _apply_mapping es pass-through: no filtra.
        r = self._t()._apply_mapping({"a": "1", "b": "2"}, {"a": "alias"})
        assert r["alias"] == "1" and r["b"] == "2"

    def test_el_nombre_original_desaparece_al_renombrar(self):
        r = self._t()._apply_mapping({"a": "1"}, {"a": "alias"})
        assert "a" not in r

    def test_mapping_vacio_devuelve_la_fila_igual(self):
        row = {"a": "1"}
        assert self._t()._apply_mapping(row, {}) == row

    def test_campo_del_mapping_ausente_no_crea_clave(self):
        r = self._t()._apply_mapping({"a": "1"}, {"no_existe": "alias"})
        assert "alias" not in r


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformConnektaConditionals:

    def _t(self):
        from transform.transform_connekta import TransformConnekta
        return TransformConnekta(CONNEKTA_CONFIG)

    def _regla(self):
        return {
            "tipo": "reglas", "campo_destino": "tracking", "campo_origen": "Maneja_lote",
            "reglas": [{"si": "SI", "entonces": "lot"}], "default": "none",
        }

    def test_regla_que_matchea(self):
        r = self._t()._apply_conditionals({"Maneja_lote": "SI"}, [self._regla()])
        assert r["tracking"] == "lot"

    def test_regla_que_no_matchea_usa_el_default(self):
        r = self._t()._apply_conditionals({"Maneja_lote": "NO"}, [self._regla()])
        assert r["tracking"] == "none"

    def test_aplica_strip_al_comparar(self):
        r = self._t()._apply_conditionals({"Maneja_lote": " SI "}, [self._regla()])
        assert r["tracking"] == "lot"

    def test_sin_default_no_asigna_y_avisa(self):
        t = self._t()
        t.logger = MagicMock()
        cond = dict(self._regla())
        del cond["default"]
        r = t._apply_conditionals({"Maneja_lote": "NO"}, [cond])
        assert "tracking" not in r
        assert t.logger.warning.called

    def test_regla_sin_entonces_loguea_error(self):
        t = self._t()
        t.logger = MagicMock()
        cond = dict(self._regla(), reglas=[{"si": "SI"}])
        t._apply_conditionals({"Maneja_lote": "SI"}, [cond])
        assert t.logger.error.called

    def test_funcion_del_catalogo(self):
        cond = {
            "tipo": "funcion", "campo_destino": "prefijo",
            "funcion": "extraer_prefijo", "params": {"campo_origen": "ref"},
        }
        r = self._t()._apply_conditionals({"ref": "PT001"}, [cond])
        assert r["prefijo"] == "PT"

    def test_funcion_inexistente_no_crea_el_campo(self):
        cond = {"tipo": "funcion", "campo_destino": "x",
                "funcion": "no_existe", "params": {}}
        r = self._t()._apply_conditionals({"a": "1"}, [cond])
        assert "x" not in r

    def test_sin_tipo_se_ignora_el_conditional(self):
        # Sin la clave `tipo` no entra a ninguna rama del dispatch.
        cond = dict(self._regla())
        del cond["tipo"]
        r = self._t()._apply_conditionals({"Maneja_lote": "SI"}, [cond])
        assert "tracking" not in r

    def test_conditionals_vacio_devuelve_la_fila_igual(self):
        row = {"a": "1"}
        assert self._t()._apply_conditionals(row, []) == row

    def test_varios_conditionals_se_aplican_todos(self):
        conds = [
            self._regla(),
            {"tipo": "funcion", "campo_destino": "prefijo",
             "funcion": "extraer_prefijo", "params": {"campo_origen": "ref"}},
        ]
        r = self._t()._apply_conditionals({"Maneja_lote": "SI", "ref": "PT1"}, conds)
        assert r["tracking"] == "lot" and r["prefijo"] == "PT"


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformConnektaNormalizes:

    def _t(self):
        from transform.transform_connekta import TransformConnekta
        return TransformConnekta(CONNEKTA_CONFIG)

    def test_items_aplica_mapping_y_hardcodes(self):
        raw = [{"Referencia_Item": "A1", "name": "Producto"}]
        cfg = {"mapping": {"Referencia_Item": "referencia", "name": "descripcion"},
               "hardcodes": {"categoria": "GENERAL"}}
        r = self._t()._normalize_items(raw, cfg)
        assert r[0]["referencia"] == "A1" and r[0]["categoria"] == "GENERAL"

    def test_purchases_parsea_fecha_compra(self):
        raw = [dict(purchase_ok(), fecha_compra="20260115")]
        r = self._t()._normalize_purchases(raw, {})
        assert r[0]["fecha_compra"] == "2026-01-15"

    def test_sales_parsea_fecha_entrega(self):
        raw = [dict(sale_ok(), fecha_entrega="20260115")]
        r = self._t()._normalize_sales(raw, {})
        assert r[0]["fecha_entrega"] == "2026-01-15"

    def test_orden_hardcodes_pisa_al_mapping(self):
        raw = [{"est": "draft", "referencia": "A1", "descripcion": "P"}]
        cfg = {"mapping": {"est": "estado"}, "hardcodes": {"estado": "sale"}}
        assert self._t()._normalize_items(raw, cfg)[0]["estado"] == "sale"

    def test_integra_la_personalizacion_por_documento(self):
        docs = [{
            "codigo": "PTR",
            "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "PTR"},
            "filtros": [], "hardcodes": {"estado": "sale"},
        }]
        raw = [dict(sale_ok(), pedido="7-PTR-1")]
        assert self._t()._normalize_sales(raw, {"documentos": docs})[0]["estado"] == "sale"


# ==========================================================
# TransformSAP
# ==========================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformSAPGetFlow:

    def _t(self):
        from transform.transform_sap import TransformSAP
        return TransformSAP(SAP_CONFIG)

    def test_flow_type_invalido_devuelve_vacio(self):
        assert self._t().get_flow(conector(), "x", "no_existe", {}) == []

    def test_sin_endpoint_devuelve_vacio(self):
        assert self._t().get_flow(conector(), "items", "purchases", {}) == []

    def test_sin_session_id_hace_login(self):
        c = conector(True, [])
        c.session_id = None
        c.login_api.return_value = True
        self._t().get_flow(c, "x", "purchases", {"endpoint": "PurchaseOrders"})
        assert c.login_api.called

    def test_login_fallido_devuelve_vacio(self):
        c = conector(True, [])
        c.session_id = None
        c.login_api.return_value = False
        assert self._t().get_flow(c, "x", "purchases", {"endpoint": "PO"}) == []

    def test_con_session_id_no_hace_login(self):
        c = conector(True, [])
        self._t().get_flow(c, "x", "purchases", {"endpoint": "PO"})
        assert not c.login_api.called

    def test_pasa_el_filter_al_conector(self):
        c = conector(True, [])
        self._t().get_flow(c, "x", "purchases", {"endpoint": "PO", "filter": "A eq 'B'"})
        assert c.get.call_args.kwargs["params"]["filter"] == "A eq 'B'"

    def test_resuelve_los_placeholders_del_filter_en_formato_iso(self):
        c = conector(True, [])
        self._t().get_flow(c, "x", "purchases",
                           {"endpoint": "PO", "filter": "UpdateDate ge '{hoy}'"})
        esperado = datetime.now().strftime("%Y-%m-%d")
        assert esperado in c.get.call_args.kwargs["params"]["filter"]

    def test_items_dispara_el_prefetch_de_categorias(self):
        c = conector(True, [{"Number": 1, "GroupName": "CAT"}])
        self._t().get_flow(c, "items", "items", {"endpoint": "Items"})
        assert c.get.call_args_list[0].kwargs["endpoint"] == "ItemGroups"

    def test_no_items_no_dispara_el_prefetch(self):
        c = conector(True, [])
        self._t().get_flow(c, "x", "purchases", {"endpoint": "PO"})
        endpoints = [ll.kwargs.get("endpoint") for ll in c.get.call_args_list]
        assert "ItemGroups" not in endpoints

    def test_prefetch_fallido_aborta_el_flow(self):
        c = MagicMock()
        c.session_id = "s"
        c.get.return_value = (False, "error")
        assert self._t().get_flow(c, "items", "items", {"endpoint": "Items"}) == []

    def test_excepcion_devuelve_vacio(self):
        c = MagicMock()
        c.session_id = "s"
        c.get.side_effect = Exception("boom")
        assert self._t().get_flow(c, "x", "purchases", {"endpoint": "PO"}) == []


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformSAPPrefetch:

    def _t(self):
        from transform.transform_sap import TransformSAP
        return TransformSAP(SAP_CONFIG)

    def test_exitoso_devuelve_true(self):
        c = conector(True, [{"Number": 1, "GroupName": "CAT"}])
        assert self._t()._prefetch_categories(c) is True

    def test_exitoso_llena_el_diccionario(self):
        t = self._t()
        t._prefetch_categories(conector(True, [{"Number": 7, "GroupName": "PINTURAS"}]))
        assert t._categorias[7] == "PINTURAS"

    def test_grupo_sin_nombre_usa_valor_por_defecto(self):
        t = self._t()
        t._prefetch_categories(conector(True, [{"Number": 7}]))
        assert t._categorias[7] == "Sin categoría"

    def test_reintenta_tres_veces_antes_de_rendirse(self):
        c = MagicMock()
        c.get.return_value = (False, "error")
        self._t()._prefetch_categories(c)
        assert c.get.call_count == 3

    def test_fallo_devuelve_false(self):
        c = MagicMock()
        c.get.return_value = (False, "error")
        assert self._t()._prefetch_categories(c) is False

    def test_fallo_deja_el_diccionario_vacio(self):
        t = self._t()
        c = MagicMock()
        c.get.return_value = (False, "error")
        t._prefetch_categories(c)
        assert t._categorias == {}

    def test_exito_en_el_segundo_intento(self):
        c = MagicMock()
        c.get.side_effect = [(False, "e"), (True, [{"Number": 1, "GroupName": "X"}])]
        assert self._t()._prefetch_categories(c) is True


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformSAPFlattenLines:

    def _t(self):
        from transform.transform_sap import TransformSAP
        return TransformSAP(SAP_CONFIG)

    def _raw(self):
        return [{"DocNum": 1, "CardCode": "P1",
                 "DocumentLines": [{"ItemCode": "A"}, {"ItemCode": "B"}]}]

    def test_aplana_a_una_fila_por_linea(self):
        ml = {"origen": "DocumentLines", "campos": {}}
        assert len(self._t()._flatten_lines(self._raw(), ml)) == 2

    def test_cada_fila_conserva_la_cabecera(self):
        ml = {"origen": "DocumentLines", "campos": {}}
        filas = self._t()._flatten_lines(self._raw(), ml)
        assert all(f["CardCode"] == "P1" for f in filas)

    def test_cada_fila_trae_su_linea(self):
        ml = {"origen": "DocumentLines", "campos": {}}
        filas = self._t()._flatten_lines(self._raw(), ml)
        assert {f["ItemCode"] for f in filas} == {"A", "B"}

    def test_el_array_original_no_queda_en_la_fila(self):
        ml = {"origen": "DocumentLines", "campos": {}}
        assert "DocumentLines" not in self._t()._flatten_lines(self._raw(), ml)[0]

    def test_sin_mapping_lineas_devuelve_raw(self):
        raw = self._raw()
        assert self._t()._flatten_lines(raw, {}) == raw

    def test_sin_origen_devuelve_raw(self):
        raw = self._raw()
        assert self._t()._flatten_lines(raw, {"campos": {}}) == raw

    def test_documento_sin_lineas_se_descarta(self):
        raw = [{"DocNum": 1, "DocumentLines": []}]
        ml = {"origen": "DocumentLines", "campos": {}}
        assert self._t()._flatten_lines(raw, ml) == []

    def test_documento_sin_lineas_loguea_warning(self):
        t = self._t()
        t.logger = MagicMock()
        t._flatten_lines([{"DocNum": 1, "DocumentLines": []}],
                         {"origen": "DocumentLines", "campos": {}})
        assert t.logger.warning.called

    def test_soporta_stock_transfer_lines(self):
        raw = [{"DocNum": 1, "StockTransferLines": [{"ItemCode": "A"}]}]
        ml = {"origen": "StockTransferLines", "campos": {}}
        assert len(self._t()._flatten_lines(raw, ml)) == 1

    def test_soporta_bp_addresses(self):
        raw = [{"CardCode": "C1", "BPAddresses": [{"AddressName": "S1"}, {"AddressName": "S2"}]}]
        ml = {"origen": "BPAddresses", "campos": {}}
        assert len(self._t()._flatten_lines(raw, ml)) == 2


@patch.dict(os.environ, {"ENV": "dev"})
class TestTransformSAPNormalizes:

    def _t(self):
        from transform.transform_sap import TransformSAP
        return TransformSAP(SAP_CONFIG)

    def test_items_resuelve_la_categoria_del_prefetch(self):
        t = self._t()
        t._categorias = {7: "PINTURAS"}
        raw = [{"ItemCode": "A1", "ItemName": "P", "ItemsGroupCode": 7}]
        cfg = {"mapping": {"ItemCode": "referencia", "ItemName": "descripcion",
                           "ItemsGroupCode_resolved": "categoria"}}
        assert t._normalize_items(raw, cfg)[0]["categoria"] == "PINTURAS"

    def test_items_conserva_el_codigo_original_para_los_conditionals(self):
        t = self._t()
        t._categorias = {7: "PINTURAS"}
        raw = [{"ItemCode": "A1", "ItemName": "P", "ItemsGroupCode": 7}]
        cfg = {"mapping": {"ItemCode": "referencia", "ItemName": "descripcion"}}
        assert t._normalize_items(raw, cfg)[0]["ItemsGroupCode"] == 7

    def test_items_categoria_desconocida_usa_valor_por_defecto(self):
        t = self._t()
        t._categorias = {7: "PINTURAS"}
        raw = [{"ItemCode": "A1", "ItemName": "P", "ItemsGroupCode": 99}]
        cfg = {"mapping": {"ItemCode": "referencia", "ItemName": "descripcion",
                           "ItemsGroupCode_resolved": "categoria"}}
        assert t._normalize_items(raw, cfg)[0]["categoria"] == "Sin categoría"

    def test_purchases_combina_mapping_de_cabecera_y_lineas(self):
        raw = [{"DocNum": "OC-1", "CardCode": "900", "DocDate": "2026-01-01",
                "DocumentLines": [{"ItemCode": "A1", "Quantity": 5, "UnitPrice": 100}]}]
        cfg = {
            "mapping": {"DocNum": "compra", "CardCode": "proveedor", "DocDate": "fecha_entrega"},
            "mapping_lineas": {"origen": "DocumentLines",
                               "campos": {"ItemCode": "producto", "Quantity": "cantidad",
                                          "UnitPrice": "precio_unitario"}},
            "hardcodes": {"sucursal_proveedor": "001", "estado": "draft", "almacen": "1"},
        }
        r = self._t()._normalize_purchases(raw, cfg)
        assert len(r) == 1
        assert r[0]["compra"] == "OC-1" and r[0]["producto"] == "A1"

    def test_sales_combina_mapping_de_cabecera_y_lineas(self):
        raw = [{"DocNum": "PV-1", "CardCode": "900", "DocDate": "2026-01-01",
                "DocumentLines": [{"ItemCode": "A1", "Quantity": 5, "UnitPrice": 100}]}]
        cfg = {
            "mapping": {"DocNum": "pedido", "CardCode": "cliente", "DocDate": "fecha_pedido"},
            "mapping_lineas": {"origen": "DocumentLines",
                               "campos": {"ItemCode": "producto", "Quantity": "cantidad_pedida",
                                          "UnitPrice": "precio_unitario"}},
            "hardcodes": {"sucursal_cliente": "001", "estado": "draft", "almacen": "1"},
        }
        assert len(self._t()._normalize_sales(raw, cfg)) == 1

    def test_partners_sin_mapping_lineas_no_aplana(self):
        raw = [{"CardCode": "900", "CardName": "Cliente"}]
        cfg = {"mapping": {"CardCode": "identificacion", "CardName": "nombre"}}
        assert len(self._t()._normalize_partners(raw, cfg)) == 1

    def test_partners_con_bp_addresses_aplana(self):
        raw = [{"CardCode": "900", "CardName": "Cliente",
                "BPAddresses": [{"AddressName": "S1"}, {"AddressName": "S2"}]}]
        cfg = {"mapping": {"CardCode": "identificacion", "CardName": "nombre"},
               "mapping_lineas": {"origen": "BPAddresses", "campos": {"AddressName": "sucursal"}}}
        assert len(self._t()._normalize_partners(raw, cfg)) == 2

    def test_integra_la_personalizacion_por_documento(self):
        docs = [{
            "codigo": "OCIMP",
            "identificar_por": {"campo": "compra", "operador": "empieza_con", "valor": "OCIMP"},
            "filtros": [], "hardcodes": {"estado": "purchase"},
        }]
        raw = [{"DocNum": "OCIMP-1",
                "DocumentLines": [{"ItemCode": "A1", "Quantity": 5, "UnitPrice": 100}]}]
        cfg = {
            "mapping": {"DocNum": "compra"},
            "mapping_lineas": {"origen": "DocumentLines",
                               "campos": {"ItemCode": "producto", "Quantity": "cantidad",
                                          "UnitPrice": "precio_unitario"}},
            "hardcodes": {"proveedor": "900", "sucursal_proveedor": "001",
                          "fecha_entrega": "2026-01-01", "estado": "draft", "almacen": "1"},
            "documentos": docs,
        }
        assert self._t()._normalize_purchases(raw, cfg)[0]["estado"] == "purchase"


# ==========================================================
# Consistencia entre los tres transforms
# ==========================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestConsistenciaEntreTransforms:

    def _todos(self):
        from transform.transform_ws import TransformWS
        from transform.transform_connekta import TransformConnekta
        from transform.transform_sap import TransformSAP
        return [TransformWS(WS_CONFIG), TransformConnekta(CONNEKTA_CONFIG),
                TransformSAP(SAP_CONFIG)]

    def test_los_tres_tienen_los_cuatro_normalizes(self):
        for t in self._todos():
            for m in ("_normalize_items", "_normalize_partners",
                      "_normalize_purchases", "_normalize_sales"):
                assert hasattr(t, m), f"{type(t).__name__} sin {m}"

    def test_los_tres_tienen_apply_hardcodes(self):
        for t in self._todos():
            assert hasattr(t, "_apply_hardcodes"), type(t).__name__

    def test_los_tres_rechazan_un_flow_type_desconocido(self):
        for t in self._todos():
            assert t.get_flow(conector(), "x", "inexistente", {}) == []

    def test_los_tres_heredan_de_transform(self):
        from transform.base import Transform
        for t in self._todos():
            assert isinstance(t, Transform)

    def test_los_tres_aplican_hardcodes_igual(self):
        for t in self._todos():
            assert t._apply_hardcodes({"estado": "draft"}, {"estado": "sale"})["estado"] == "sale"

    def test_sin_documentos_ninguno_altera_las_filas(self):
        for t in self._todos():
            r = t._normalize_sales([sale_ok()], {})
            assert len(r) == 1 and r[0]["estado"] == "draft"

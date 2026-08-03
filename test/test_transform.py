import os
import pytest
from unittest.mock import patch, MagicMock

# -- Configs ficticios

WS_CONFIG = {
    "client_id": "test_client",
    "erp": {"tipo": "ws"},
}

CONNEKTA_CONFIG = {
    "client_id": "test_client",
    "erp": {"tipo": "connekta"},
}

SAP_CONFIG = {
    "client_id": "test_client",
    "erp": {"tipo": "sap"},
}

# -- Transform — base.py

class TestTransform:

  def test_transform_no_se_puede_instanciar_directamente(self):
      from transform.base import Transform
      with pytest.raises(TypeError):
          Transform()

  def test_subclase_sin_get_flow_no_se_puede_instanciar(self):
      from transform.base import Transform

      class SinGetFlow(Transform):
          pass

      with pytest.raises(TypeError):
          SinGetFlow()

  def test_subclase_con_get_flow_si_se_puede_instanciar(self):
      from transform.base import Transform

      class Completa(Transform):
          def get_flow(self, connector, flow_name, flow_config):
              return []

      t = Completa()
      assert t is not None

# -- Helpers — utils/helpers.py

class TestParseFecha:

  def test_formato_yyyymmdd(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("20260115") == "2026-01-15"

  def test_formato_iso_con_T(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("2026-01-15T14:30:00") == "2026-01-15"

  def test_formato_iso_con_T_y_Z(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("2026-01-15T14:30:00.000Z") == "2026-01-15"

  def test_formato_mm_dd_yyyy(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("01/15/2026", formato="%m/%d/%Y") == "2026-01-15"

  def test_formato_yyyy_mm_dd(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("2026-01-15") == "2026-01-15"

  def test_formato_yyyy_mm_dd_hms(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("2026-01-15 14:30:00") == "2026-01-15"

  def test_formato_dd_mm_yyyy(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("15/01/2026", formato="%d/%m/%Y") == "2026-01-15"

  def test_vacio_retorna_vacio(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("") == ""

  def test_none_retorna_vacio(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha(None) == ""

  def test_invalido_sin_logger_retorna_vacio(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("no-es-fecha") == ""

  def test_invalido_con_logger_loguea_warning(self):
      from transform.utils.helpers import parse_fecha
      mock_logger = MagicMock()
      result = parse_fecha("no-es-fecha", logger=mock_logger)
      assert result == ""
      mock_logger.warning.assert_called_once()

  def test_espacios_alrededor(self):
      from transform.utils.helpers import parse_fecha
      assert parse_fecha("  20260115  ") == "2026-01-15"


class TestCleanString:

  def test_string_normal_sin_cambios(self):
      from transform.utils.helpers import clean_string
      assert clean_string("PRODUCTO A") == "PRODUCTO A"

  def test_none_retorna_vacio(self):
      from transform.utils.helpers import clean_string
      assert clean_string(None) == ""

  def test_elimina_caracteres_no_imprimibles(self):
      from transform.utils.helpers import clean_string
      assert clean_string("ABC\x00DEF\x01") == "ABCDEF"

  def test_strip_espacios(self):
      from transform.utils.helpers import clean_string
      assert clean_string("  hola  ") == "hola"

  def test_numero_se_convierte_a_string(self):
      from transform.utils.helpers import clean_string
      assert clean_string(123) == "123"

class TestToFloat:

    def test_string_numerico(self):
        from transform.utils.helpers import to_float
        assert to_float("3.14") == 3.14

    def test_entero(self):
        from transform.utils.helpers import to_float
        assert to_float(42) == 42.0

    def test_none_retorna_default(self):
        from transform.utils.helpers import to_float
        assert to_float(None) == 0.0

    def test_vacio_retorna_default(self):
        from transform.utils.helpers import to_float
        assert to_float("") == 0.0

    def test_invalido_retorna_default(self):
        from transform.utils.helpers import to_float
        assert to_float("abc") == 0.0

    def test_invalido_con_default_custom(self):
        from transform.utils.helpers import to_float
        assert to_float("abc", default=-1.0) == -1.0

    def test_invalido_con_logger_loguea_warning(self):
        from transform.utils.helpers import to_float
        mock_logger = MagicMock()
        to_float("abc", logger=mock_logger, field_name="precio")
        mock_logger.warning.assert_called_once()
        assert "precio" in mock_logger.warning.call_args[0][0]

    def test_cero_es_valido(self):
        from transform.utils.helpers import to_float
        assert to_float("0") == 0.0
        assert to_float(0) == 0.0

class TestToInt:

    def test_string_entero(self):
        from transform.utils.helpers import to_int
        assert to_int("42") == 42

    def test_float_like_string(self):
        from transform.utils.helpers import to_int
        assert to_int("5.0") == 5

    def test_float_value(self):
        from transform.utils.helpers import to_int
        assert to_int(5.9) == 5

    def test_none_retorna_default(self):
        from transform.utils.helpers import to_int
        assert to_int(None) == 0

    def test_vacio_retorna_default(self):
        from transform.utils.helpers import to_int
        assert to_int("") == 0

    def test_invalido_retorna_default(self):
        from transform.utils.helpers import to_int
        assert to_int("abc") == 0

    def test_invalido_con_logger_loguea_warning(self):
        from transform.utils.helpers import to_int
        mock_logger = MagicMock()
        to_int("abc", logger=mock_logger, field_name="vence")
        mock_logger.warning.assert_called_once()

class TestSplitCodes:

    def test_split_con_comas(self):
        from transform.utils.helpers import split_codes
        assert split_codes("A,B,C") == ["A", "B", "C"]

    def test_strip_espacios(self):
        from transform.utils.helpers import split_codes
        assert split_codes(" A , B , C ") == ["A", "B", "C"]

    def test_filtra_vacios(self):
        from transform.utils.helpers import split_codes
        assert split_codes("A,,B,,") == ["A", "B"]

    def test_separador_custom(self):
        from transform.utils.helpers import split_codes
        assert split_codes("A;B;C", separator=";") == ["A", "B", "C"]

    def test_vacio_retorna_lista_vacia(self):
        from transform.utils.helpers import split_codes
        assert split_codes("") == []

    def test_none_retorna_lista_vacia(self):
        from transform.utils.helpers import split_codes
        assert split_codes(None) == []

    def test_no_string_retorna_lista_vacia(self):
        from transform.utils.helpers import split_codes
        assert split_codes(123) == []

class TestCleanRow:

    def test_limpia_strings(self):
        from transform.utils.helpers import clean_row
        row = {"nombre": "  ABC\x00  ", "codigo": "  123  "}
        result = clean_row(row)
        assert result["nombre"] == "ABC"
        assert result["codigo"] == "123"

    def test_no_modifica_no_strings(self):
        from transform.utils.helpers import clean_row
        row = {"cantidad": 5, "precio": 3.14, "activo": None}
        result = clean_row(row)
        assert result["cantidad"] == 5
        assert result["precio"] == 3.14
        assert result["activo"] is None

class TestValidateRecord:

    # -- items
    def test_items_valido(self):
        from transform.utils.helpers import validate_record
        row = {"referencia" : "SKU001", "descripcion": "Producto A"}
        valid, reason = validate_record(row, "items")
        assert valid is True

    def test_items_referencia_vacia(self):
        from transform.utils.helpers import validate_record
        row = {"referencia": "", "descripcion": "Producto A"}
        valid, reason = validate_record(row, "items")
        assert valid is False
        assert "referencia" in reason

    def test_items_descripcion_vacia(self):
        from transform.utils.helpers import validate_record
        row = {"referencia": "SKU001", "descripcion": ""}
        valid, reason = validate_record(row, "items")
        assert valid is False
        assert "descripcion" in reason

    def test_items_sin_referencia(self):
        from transform.utils.helpers import validate_record
        row = {"descripcion": "Producto A"}
        valid, reason = validate_record(row, "items")
        assert valid is False

    # -- partners
    def test_partners_valido(self):
        from transform.utils.helpers import validate_record
        row = {"nombre": "Empresa X", "identificacion": "900123456"}
        valid, reason = validate_record(row, "partners")
        assert valid is True

    def test_partners_nombre_vacio(self):
        from transform.utils.helpers import validate_record
        row = {"nombre": "", "identificacion": "900123456"}
        valid, reason = validate_record(row, "partners")
        assert valid is False
        assert "nombre" in reason

    def test_partners_identificacion_vacia(self):
        from transform.utils.helpers import validate_record
        row = {"nombre": "Empresa X", "identificacion": ""}
        valid, reason = validate_record(row, "partners")
        assert valid is False
        assert "identificacion" in reason

    # -- purchases
    def test_purchases_valido(self):
        from transform.utils.helpers import validate_record
        row = {
            "compra": "OC-001", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad": "10",
        }
        valid, reason = validate_record(row, "purchases")
        assert valid is True

    def test_purchases_compra_vacia(self):
        from transform.utils.helpers import validate_record
        row = {
            "compra": "", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad": "10",
        }
        valid, reason = validate_record(row, "purchases")
        assert valid is False
        assert "compra" in reason

    def test_purchases_precio_unitario_cero_es_valido(self):
        from transform.utils.helpers import validate_record
        row = {
            "compra": "OC-001", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "0",
            "cantidad": "10",
        }
        valid, reason = validate_record(row, "purchases")
        assert valid is True

    def test_purchases_precio_unitario_ausente(self):
        from transform.utils.helpers import validate_record
        row = {
            "compra": "OC-001", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01",
            "cantidad": "10",
        }
        valid, reason = validate_record(row, "purchases")
        assert valid is False
        assert "precio_unitario" in reason

    def test_purchases_cantidad_cero(self):
        from transform.utils.helpers import validate_record
        row = {
            "compra": "OC-001", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad": "0",
        }
        valid, reason = validate_record(row, "purchases")
        assert valid is False
        assert "cantidad" in reason

    def test_purchases_cantidad_no_numerica(self):
        from transform.utils.helpers import validate_record
        row = {
            "compra": "OC-001", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad": "abc",
        }
        valid, reason = validate_record(row, "purchases")
        assert valid is False
        assert "numérica" in reason

    # -- sales
    def test_sales_valido(self):
        from transform.utils.helpers import validate_record
        row = {
            "pedido": "PV-001", "producto": "SKU001", "cliente": "C001",
            "sucursal_cliente": "S001", "fecha_pedido": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad_pedida": "10",
        }
        valid, reason = validate_record(row, "sales")
        assert valid is True

    def test_sales_pedido_vacio(self):
        from transform.utils.helpers import validate_record
        row = {
            "pedido": "", "producto": "SKU001", "cliente": "C001",
            "sucursal_cliente": "S001", "fecha_pedido": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad_pedida": "10",
        }
        valid, reason = validate_record(row, "sales")
        assert valid is False
        assert "pedido" in reason

    def test_sales_cantidad_pedida_cero(self):
        from transform.utils.helpers import validate_record
        row = {
            "pedido": "PV-001", "producto": "SKU001", "cliente": "C001",
            "sucursal_cliente": "S001", "fecha_pedido": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100",
            "cantidad_pedida": "0",
        }
        valid, reason = validate_record(row, "sales")
        assert valid is False
        assert "cantidad_pedida" in reason

    def test_sales_precio_unitario_cero_es_valido(self):
        from transform.utils.helpers import validate_record
        row = {
            "pedido": "PV-001", "producto": "SKU001", "cliente": "C001",
            "sucursal_cliente": "S001", "fecha_pedido": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "0",
            "cantidad_pedida": "10",
        }
        valid, reason = validate_record(row, "sales")
        assert valid is True

    # -- logger
    def test_validate_con_logger_loguea_warning_en_descarte(self):
        from transform.utils.helpers import validate_record
        mock_logger = MagicMock()
        row = {"referencia": "", "descripcion": "P"}
        validate_record(row, "items", logger=mock_logger)
        mock_logger.warning.assert_called_once()

    # -- entity_type desconocido
    def test_entity_type_desconocido_retorna_true(self):
        from transform.utils.helpers import validate_record
        valid, reason = validate_record({}, "desconocido")
        assert valid is True

# -- Determination Functions — utils/determination_functions.py

class TestGetDeterminationFunction:

    def test_nombre_valido_retorna_funcion(self):
        from transform.utils.determination_functions import get_determination_function
        fn = get_determination_function("extraer_prefijo")
        assert fn is not None
        assert callable(fn)

    def test_nombre_invalido_retorna_none(self):
        from transform.utils.determination_functions import get_determination_function
        fn = get_determination_function("no_existe")
        assert fn is None

    def test_nombre_invalido_con_logger_loguea_error(self):
        from transform.utils.determination_functions import get_determination_function
        mock_logger = MagicMock()
        get_determination_function("no_existe", logger=mock_logger)
        mock_logger.error.assert_called_once()

    def test_todas_las_funciones_del_catalogo_existen(self):
        from transform.utils.determination_functions import get_determination_function
        nombres = [
            "route_compra_manufactura_prefijo", "extraer_prefijo",
            "concatenar_campos", "valor_por_campo", "valor_por_lista",
            "doc_name_por_rango", "sap_field_combined",
        ]
        for nombre in nombres:
            assert get_determination_function(nombre) is not None, f"Falta: {nombre}"

class TestRouteCompraManufacturaPrefijo:

    def test_ambos_true(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "True", "Manufactura": "True", "referencia": "SKU001"}
        params = {"campo_compra": "Compra", "campo_manufactura": "Manufactura",
                "campo_referencia": "referencia", "prefijo_manufactura": ""}
        assert route_compra_manufactura_prefijo(row, params) == "Buy,Fabricación"

    def test_solo_compra(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "True", "Manufactura": "False", "referencia": "SKU001"}
        params = {"campo_compra": "Compra", "campo_manufactura": "Manufactura",
                "campo_referencia": "referencia", "prefijo_manufactura": ""}
        assert route_compra_manufactura_prefijo(row, params) == "Buy"

    def test_solo_manufactura(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "False", "Manufactura": "True", "referencia": "SKU001"}
        params = {"campo_compra": "Compra", "campo_manufactura": "Manufactura",
                "campo_referencia": "referencia", "prefijo_manufactura": ""}
        assert route_compra_manufactura_prefijo(row, params) == "Fabricación"

    def test_ninguno_retorna_vacio(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "False", "Manufactura": "False", "referencia": "SKU001"}
        params = {"campo_compra": "Compra", "campo_manufactura": "Manufactura",
                "campo_referencia": "referencia", "prefijo_manufactura": ""}
        assert route_compra_manufactura_prefijo(row, params) == ""

    def test_prefijo_activa_manufactura(self):
        from transform.utils.determination_functions import route_compra_manufactura_prefijo
        row = {"Compra": "False", "Manufactura": "False", "referencia": "PT001"}
        params = {"campo_compra": "Compra", "campo_manufactura": "Manufactura",
                "campo_referencia": "referencia", "prefijo_manufactura": "PT"}
        assert route_compra_manufactura_prefijo(row, params) == "Fabricación"

class TestExtraerPrefijo:

    def test_prefijo_normal(self):
        from transform.utils.determination_functions import extraer_prefijo
        row = {"referencia": "PT001"}
        assert extraer_prefijo(row, {"campo_origen": "referencia"}) == "PT"

    def test_sin_prefijo_alfabetico(self):
        from transform.utils.determination_functions import extraer_prefijo
        row = {"referencia": "001ABC"}
        assert extraer_prefijo(row, {"campo_origen": "referencia"}) == ""

    def test_campo_vacio(self):
        from transform.utils.determination_functions import extraer_prefijo
        row = {"referencia": ""}
        assert extraer_prefijo(row, {"campo_origen": "referencia"}) == ""

class TestConcatenarCampos:

    def test_concatena_con_separador(self):
        from transform.utils.determination_functions import concatenar_campos
        row = {"co": "001", "tipo": "TEM", "consec": "123"}
        params = {"campos": ["co", "tipo", "consec"], "separador": "-"}
        assert concatenar_campos(row, params) == "001-TEM-123"

    def test_sin_campos_retorna_vacio(self):
        from transform.utils.determination_functions import concatenar_campos
        assert concatenar_campos({}, {"campos": [], "separador": "-"}) == ""

    def test_campo_ausente_usa_vacio(self):
        from transform.utils.determination_functions import concatenar_campos
        row = {"co": "001"}
        params = {"campos": ["co", "no_existe"], "separador": "-"}
        assert concatenar_campos(row, params) == "001-"

class TestValorPorCampo:

    def test_match(self):
        from transform.utils.determination_functions import valor_por_campo
        row = {"PurchaseItem": "tYES"}
        params = {"campo_origen": "PurchaseItem", "valor": "tYES", "si": "Comprar", "no": "Fabricar"}
        assert valor_por_campo(row, params) == "Comprar"

    def test_no_match(self):
        from transform.utils.determination_functions import valor_por_campo
        row = {"PurchaseItem": "tNO"}
        params = {"campo_origen": "PurchaseItem", "valor": "tYES", "si": "Comprar", "no": "Fabricar"}
        assert valor_por_campo(row, params) == "Fabricar"

class TestValorPorLista:

    def test_match_tipo_original(self):
        from transform.utils.determination_functions import valor_por_lista
        row = {"ItemsGroupCode": 307}
        params = {"campo_origen": "ItemsGroupCode", "lista": [307, 313], "si": "lot", "no": "none"}
        assert valor_por_lista(row, params) == "lot"

    def test_no_match(self):
        from transform.utils.determination_functions import valor_por_lista
        row = {"ItemsGroupCode": 999}
        params = {"campo_origen": "ItemsGroupCode", "lista": [307, 313], "si": "lot", "no": "none"}
        assert valor_por_lista(row, params) == "none"

    def test_match_fallback_string(self):
        from transform.utils.determination_functions import valor_por_lista
        row = {"ItemsGroupCode": "307"}
        params = {"campo_origen": "ItemsGroupCode", "lista": [307, 313], "si": "lot", "no": "none"}
        assert valor_por_lista(row, params) == "lot"

class TestDocNamePorRango:

    def test_en_rango(self):
        from transform.utils.determination_functions import doc_name_por_rango
        row = {"DocNum": 12345}
        params = {"campo_origen": "DocNum", "rangos": {"1-10000000": "OCNAL"}, "separador": "-"}
        assert doc_name_por_rango(row, params) == "OCNAL-12345"

    def test_fuera_de_rango(self):
        from transform.utils.determination_functions import doc_name_por_rango
        row = {"DocNum": 99999999}
        params = {"campo_origen": "DocNum", "rangos": {"1-1000": "OCNAL"}, "separador": "-"}
        assert doc_name_por_rango(row, params) == ""

    def test_valor_no_numerico(self):
        from transform.utils.determination_functions import doc_name_por_rango
        row = {"DocNum": "abc"}
        params = {"campo_origen": "DocNum", "rangos": {"1-1000": "OCNAL"}}
        assert doc_name_por_rango(row, params) == ""

class TestSapFieldCombined:

    def test_ambos_match(self):
        from transform.utils.determination_functions import sap_field_combined
        row = {"U_FB_EnviarWMS": "Y", "U_FB_EnviarProdWMS": "Y"}
        params = {"campo1": "U_FB_EnviarWMS", "campo2": "U_FB_EnviarProdWMS",
                "valor_esperado": "Y", "texto_ambos": "Producto Terminado, Producción",
                "texto_solo_uno": "Producto Terminado"}
        assert sap_field_combined(row, params) == "Producto Terminado, Producción"

    def test_solo_uno_match(self):
        from transform.utils.determination_functions import sap_field_combined
        row = {"U_FB_EnviarWMS": "Y", "U_FB_EnviarProdWMS": "N"}
        params = {"campo1": "U_FB_EnviarWMS", "campo2": "U_FB_EnviarProdWMS",
                "valor_esperado": "Y", "texto_ambos": "Ambos",
                "texto_solo_uno": "Solo uno"}
        assert sap_field_combined(row, params) == "Solo uno"

# -- TransformWS — transform_ws.py

@patch.dict(os.environ, {"ENV": "dev"}, clear=True)
class TestTransformWS:

    def test_constructor_asigna_client_id(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        assert t.client_id == "test_client"

    def test_get_flow_flow_invalido_retorna_vacio(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        result = t.get_flow(MagicMock(), "no_existe", {})
        assert result == []

    def test_get_flow_sin_sql_retorna_vacio(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        result = t.get_flow(MagicMock(), "items", {"sql": ""})
        assert result == []

    def test_get_flow_connector_falla_retorna_vacio(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (False, "Error de conexión")
        result = t.get_flow(connector, "items", {"sql": "SELECT 1"})
        assert result == []

    def test_get_flow_raw_vacio_retorna_vacio(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [])
        result = t.get_flow(connector, "items", {"sql": "SELECT 1"})
        assert result == []

    def test_get_flow_items_exitoso(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"referencia": "SKU001", "descripcion": "Producto A", "peso": "1.5", "vence": "30"},
        ])
        result = t.get_flow(connector, "items", {"sql": "SELECT ..."})
        assert len(result) == 1
        assert result[0]["peso"] == 1.5
        assert result[0]["vence"] == 30

    def test_get_flow_items_descarta_invalidos(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"referencia": "SKU001", "descripcion": "Producto A"},
            {"referencia": "", "descripcion": "Sin referencia"},
        ])
        result = t.get_flow(connector, "items", {"sql": "SELECT ..."})
        assert len(result) == 1

    def test_get_flow_partners_exitoso(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"nombre": "Empresa X", "identificacion": "900123456", "direccion": " Calle 1 "},
        ])
        result = t.get_flow(connector, "partners", {"sql": "SELECT ..."})
        assert len(result) == 1
        assert result[0]["direccion"] == "Calle 1"

    def test_get_flow_purchases_tipado(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"compra": "OC-001", "producto": "SKU001", "proveedor": "P001",
            "sucursal_proveedor": "S001", "fecha_entrega": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "100.50",
            "cantidad": "10", "impuesto": "19"},
        ])
        result = t.get_flow(connector, "compras", {"sql": "SELECT ..."})
        assert len(result) == 1
        assert result[0]["cantidad"] == 10.0
        assert result[0]["precio_unitario"] == 100.50
        assert result[0]["fecha_entrega"] == "2026-01-15"

    def test_get_flow_sales_tipado(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"pedido": "PV-001", "producto": "SKU001", "cliente": "C001",
            "sucursal_cliente": "S001", "fecha_pedido": "20260115",
            "estado": "draft", "almacen": "ALM01", "precio_unitario": "200",
            "cantidad_pedida": "5", "impuesto": "19"},
        ])
        result = t.get_flow(connector, "ventas", {"sql": "SELECT ..."})
        assert len(result) == 1
        assert result[0]["cantidad_pedida"] == 5.0
        assert result[0]["fecha_pedido"] == "2026-01-15"

    def test_get_flow_exception_retorna_vacio(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.side_effect = Exception("Boom")
        result = t.get_flow(connector, "items", {"sql": "SELECT 1"})
        assert result == []

    def test_normalize_map_tiene_18_flow_names(self):
        from transform.transform_ws import TransformWS
        t = TransformWS(WS_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [])
        # Verificar que los 18 flow_names conocidos no retornan error de flujo no soportado
        flows = [
            "items", "partners",
            "compras", "compras_importacion", "transferencia_entrada",
            "traslados_entrada", "entrada_mercancia", "entrada_directa",
            "devolucion_in", "nota_credito",
            "ventas", "facturas", "transferencia_salida", "transferencia_interna",
            "salida_mercancia", "salida_directa", "devolucion_out", "requisiciones",
        ]
        for flow_name in flows:
            result = t.get_flow(connector, flow_name, {"sql": "SELECT 1"})
            assert result == [], f"Flow {flow_name} debería retornar [] con raw vacío"

# -- TransformConnekta — transform_connekta.py

@patch.dict(os.environ, {"ENV": "dev"}, clear=True)
class TestTransformConnekta:

    def test_constructor_asigna_client_id(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        assert t.client_id == "test_client"

    def test_get_flow_flow_invalido_retorna_vacio(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        result = t.get_flow(MagicMock(), "no_existe", {})
        assert result == []

    def test_get_flow_sin_query_desc_retorna_vacio(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        result = t.get_flow(MagicMock(), "items", {"query_desc": ""})
        assert result == []

    def test_get_flow_connector_falla_retorna_vacio(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (False, "Error")
        result = t.get_flow(connector, "items", {"query_desc": "items_wms"})
        assert result == []

    def test_get_flow_items_con_mapping_y_hardcodes(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"Referencia_Item": "SKU001", "name": "Producto A", "PesoNeto": "1.5"},
        ])
        flow_config = {
            "query_desc": "items_wms",
            "mapping": {"Referencia_Item": "referencia", "name": "descripcion", "PesoNeto": "peso"},
            "hardcodes": {"impuesto": 19.0},
            "conditionals": [],
        }
        result = t.get_flow(connector, "items", flow_config)
        assert len(result) == 1
        assert result[0]["referencia"] == "SKU001"
        assert result[0]["descripcion"] == "Producto A"
        assert result[0]["peso"] == 1.5
        assert result[0]["impuesto"] == 19.0

    # -- _apply_mapping
    def test_apply_mapping_renombra_keys(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"Referencia_Item": "SKU001", "name": "Producto A"}
        mapping = {"Referencia_Item": "referencia", "name": "descripcion"}
        result = t._apply_mapping(row, mapping)
        assert result == {"referencia": "SKU001", "descripcion": "Producto A"}

    def test_apply_mapping_filtra_campos_no_mapeados(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"Referencia_Item": "SKU001", "campo_extra": "ignorar"}
        mapping = {"Referencia_Item": "referencia"}
        result = t._apply_mapping(row, mapping)
        assert "campo_extra" not in result
        assert result == {"referencia": "SKU001"}

    def test_apply_mapping_vacio_retorna_row_igual(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"a": 1, "b": 2}
        result = t._apply_mapping(row, {})
        assert result == row

    # -- _apply_hardcodes
    def test_apply_hardcodes_inyecta_valores(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"referencia": "SKU001"}
        result = t._apply_hardcodes(row, {"estado": "draft", "impuesto": 19})
        assert result["estado"] == "draft"
        assert result["impuesto"] == 19

    def test_apply_hardcodes_sobreescribe_valor_existente(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"estado": "open"}
        result = t._apply_hardcodes(row, {"estado": "draft"})
        assert result["estado"] == "draft"

    def test_apply_hardcodes_vacio_retorna_row_igual(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"a": 1}
        result = t._apply_hardcodes(row, {})
        assert result == {"a": 1}

    # -- _apply_conditionals modo A (reglas)
    def test_apply_conditionals_reglas_con_match(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"Maneja_lote": "SI"}
        conditionals = [{
            "tipo": "reglas", "campo_origen": "Maneja_lote",
            "campo_destino": "tracking",
            "reglas": [{"si": "SI", "entonces": "lot"}],
            "default": "none",
        }]
        result = t._apply_conditionals(row, conditionals)
        assert result["tracking"] == "lot"

    def test_apply_conditionals_reglas_sin_match_usa_default(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"Maneja_lote": "NO"}
        conditionals = [{
            "tipo": "reglas", "campo_origen": "Maneja_lote",
            "campo_destino": "tracking",
            "reglas": [{"si": "SI", "entonces": "lot"}],
            "default": "none",
        }]
        result = t._apply_conditionals(row, conditionals)
        assert result["tracking"] == "none"

    def test_apply_conditionals_reglas_default_none_no_agrega_campo(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"Maneja_lote": "NO"}
        conditionals = [{
            "tipo": "reglas", "campo_origen": "Maneja_lote",
            "campo_destino": "tracking",
            "reglas": [{"si": "SI", "entonces": "lot"}],
            "default": None,
        }]
        result = t._apply_conditionals(row, conditionals)
        assert "tracking" not in result

    # -- _apply_conditionals modo B (función)
    def test_apply_conditionals_funcion_del_catalogo(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"referencia": "PT001"}
        conditionals = [{
            "tipo": "funcion", "campo_destino": "prefijo",
            "funcion": "extraer_prefijo",
            "params": {"campo_origen": "referencia"},
        }]
        result = t._apply_conditionals(row, conditionals)
        assert result["prefijo"] == "PT"

    def test_apply_conditionals_vacio_retorna_row_igual(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        row = {"a": 1}
        result = t._apply_conditionals(row, [])
        assert result == {"a": 1}

    # -- normalize partners
    def test_normalize_partners_con_mapping(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"NombreTercero": "Empresa X", "NIT": "900123456"},
        ])
        flow_config = {
            "query_desc": "partners_wms",
            "mapping": {"NombreTercero": "nombre", "NIT": "identificacion"},
            "hardcodes": {}, "conditionals": [],
        }
        result = t.get_flow(connector, "partners", flow_config)
        assert len(result) == 1
        assert result[0]["nombre"] == "Empresa X"

    # -- normalize purchases
    def test_normalize_purchases_tipado(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"OC": "OC-001", "Item": "SKU001", "Prov": "P001", "SucProv": "S001",
            "Fecha": "20260115", "Est": "draft", "Alm": "ALM01",
            "Precio": "100.50", "Cant": "10", "Imp": "19"},
        ])
        flow_config = {
            "query_desc": "compras_wms",
            "mapping": {"OC": "compra", "Item": "producto", "Prov": "proveedor",
                        "SucProv": "sucursal_proveedor", "Fecha": "fecha_entrega",
                        "Est": "estado", "Alm": "almacen", "Precio": "precio_unitario",
                        "Cant": "cantidad", "Imp": "impuesto"},
            "hardcodes": {}, "conditionals": [],
        }
        result = t.get_flow(connector, "compras", flow_config)
        assert len(result) == 1
        assert result[0]["cantidad"] == 10.0
        assert result[0]["fecha_entrega"] == "2026-01-15"

    # -- normalize sales
    def test_normalize_sales_tipado(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"PV": "PV-001", "Item": "SKU001", "Cli": "C001", "SucCli": "S001",
            "Fecha": "20260115", "Est": "draft", "Alm": "ALM01",
            "Precio": "200", "CantPed": "5", "Imp": "19"},
        ])
        flow_config = {
            "query_desc": "ventas_wms",
            "mapping": {"PV": "pedido", "Item": "producto", "Cli": "cliente",
                        "SucCli": "sucursal_cliente", "Fecha": "fecha_pedido",
                        "Est": "estado", "Alm": "almacen", "Precio": "precio_unitario",
                        "CantPed": "cantidad_pedida", "Imp": "impuesto"},
            "hardcodes": {}, "conditionals": [],
        }
        result = t.get_flow(connector, "ventas", flow_config)
        assert len(result) == 1
        assert result[0]["cantidad_pedida"] == 5.0
        assert result[0]["fecha_pedido"] == "2026-01-15"

    def test_normalize_map_tiene_20_flow_names(self):
        from transform.transform_connekta import TransformConnekta
        t = TransformConnekta(CONNEKTA_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [])
        flows = [
            "items", "partners",
            "compras", "devoluciones_cliente", "entrada_calidad_recepcion",
            "traslados_entradas", "entrada_inventario_oc", "entrada_ensamble",
            "entrada_desensamble", "traslados_transito_entrada",
            "ventas", "devoluciones_proveedores", "traslados_salidas",
            "traslados_preproduccion", "salidas_ensamble", "salida_desensamble",
            "salidas_consumo_interno", "salida_requisiciones",
            "traslados_transito_salida", "facturas",
        ]
        for flow_name in flows:
            result = t.get_flow(connector, flow_name, {"query_desc": "test"})
            assert result == [], f"Flow {flow_name} debería retornar [] con raw vacío"

# -- TransformSAP — transform_sap.py

@patch.dict(os.environ, {"ENV": "dev"}, clear=True)
class TestTransformSAP:

    def test_constructor_asigna_client_id_y_categorias_vacio(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        assert t.client_id == "test_client"
        assert t._categorias == {}

    def test_get_flow_flow_invalido_retorna_vacio(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        result = t.get_flow(MagicMock(), "no_existe", {})
        assert result == []

    # -- get_flow: autenticación
    def test_get_flow_sin_session_id_hace_login(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = None
        connector.login_api.return_value = True
        connector.get.return_value = (True, [])
        t.get_flow(connector, "compras", {"endpoint": "PurchaseOrders"})
        connector.login_api.assert_called_once()

    def test_get_flow_login_falla_retorna_vacio(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = None
        connector.login_api.return_value = False
        result = t.get_flow(connector, "compras", {"endpoint": "PurchaseOrders"})
        assert result == []
        connector.get.assert_not_called()

    def test_get_flow_sin_endpoint_retorna_vacio(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = "SESSION-123"
        result = t.get_flow(connector, "compras", {})
        assert result == []
        connector.get.assert_not_called()

    # -- get_flow: pre-fetch de categorías
    def test_get_flow_items_llama_prefetch_categories(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = "SESSION-123"
        connector.get.return_value = (True, [])
        with patch.object(t, "_prefetch_categories") as mock_prefetch:
            t.get_flow(connector, "items", {"endpoint": "Items"})
            mock_prefetch.assert_called_once_with(connector)

    def test_get_flow_no_items_no_llama_prefetch(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = "SESSION-123"
        connector.get.return_value = (True, [])
        with patch.object(t, "_prefetch_categories") as mock_prefetch:
            t.get_flow(connector, "compras", {"endpoint": "PurchaseOrders"})
            mock_prefetch.assert_not_called()

    def test_get_flow_pasa_filter_al_connector(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = "SESSION-123"
        connector.get.return_value = (True, [])
        flow_config = {
            "endpoint": "PurchaseOrders",
            "filter": "DocType eq 'dDocument_Items'",
        }
        t.get_flow(connector, "compras", flow_config)
        kwargs = connector.get.call_args[1]
        assert kwargs["endpoint"] == "PurchaseOrders"
        assert kwargs["params"] == {"filter": "DocType eq 'dDocument_Items'"}

    # -- _prefetch_categories
    def test_prefetch_categories_exitoso(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (True, [
            {"Number": 100, "GroupName": "Materias Primas"},
            {"Number": 200, "GroupName": "Producto Terminado"},
        ])
        t._prefetch_categories(connector)
        assert t._categorias == {100: "Materias Primas", 200: "Producto Terminado"}
        connector.get.assert_called_once_with(endpoint="ItemGroups", params={})

    def test_prefetch_categories_falla_deja_dict_vacio(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.get.return_value = (False, "Error de conexión")
        t._prefetch_categories(connector)
        assert t._categorias == {}

    # -- _flatten_lines
    def test_flatten_lines_aplana_document_lines(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [{
            "DocNum": 12345,
            "CardCode": "P-ACME",
            "DocumentLines": [
                {"ItemCode": "SKU001", "Quantity": 10},
                {"ItemCode": "SKU002", "Quantity": 20},
            ],
        }]
        mapping_lineas = {"origen": "DocumentLines", "campos": {"ItemCode": "producto"}}
        result = t._flatten_lines(raw, mapping_lineas)
        assert len(result) == 2
        assert result[0]["DocNum"] == 12345
        assert result[0]["ItemCode"] == "SKU001"
        assert result[1]["ItemCode"] == "SKU002"
        assert "DocumentLines" not in result[0]

    def test_flatten_lines_sin_mapping_lineas_retorna_raw(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [{"ItemCode": "SKU001"}]
        assert t._flatten_lines(raw, {}) == raw

    def test_flatten_lines_documento_sin_lineas_se_descarta(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [
            {"DocNum": 1, "DocumentLines": []},
            {"DocNum": 2, "DocumentLines": [{"ItemCode": "SKU001"}]},
        ]
        mapping_lineas = {"origen": "DocumentLines", "campos": {"ItemCode": "producto"}}
        result = t._flatten_lines(raw, mapping_lineas)
        assert len(result) == 1
        assert result[0]["DocNum"] == 2

    # -- _normalize_items
    def test_normalize_items_inyecta_categoria_resuelta(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        t._categorias = {100: "Materias Primas"}
        raw = [{"ItemCode": "SKU001", "ItemName": "Producto A", "ItemsGroupCode": 100}]
        flow_config = {
            "mapping": {
                "ItemCode": "referencia",
                "ItemName": "descripcion",
                "ItemsGroupCode_resolved": "categoria",
            },
            "hardcodes": {}, "conditionals": [],
        }
        result = t._normalize_items(raw, flow_config)
        assert len(result) == 1
        assert result[0]["categoria"] == "Materias Primas"

    def test_normalize_items_tipado_float_e_int(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [{
            "ItemCode": "SKU001", "ItemName": "Producto A",
            "SalesUnitWeight": "2.5", "U_Vida_Util": "30",
        }]
        flow_config = {
            "mapping": {
                "ItemCode": "referencia", "ItemName": "descripcion",
                "SalesUnitWeight": "peso", "U_Vida_Util": "vence",
            },
            "hardcodes": {"impuesto": 19}, "conditionals": [],
        }
        result = t._normalize_items(raw, flow_config)
        assert len(result) == 1
        assert result[0]["peso"] == 2.5
        assert result[0]["vence"] == 30
        assert result[0]["impuesto"] == 19

    # -- _normalize_partners
    def test_normalize_partners_con_flatten_bp_addresses(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [{
            "CardCode": "900123456", "CardName": "Empresa X",
            "EmailAddress": "contacto@empresax.com",
            "BPAddresses": [
                {"AddressName": "SUC01", "Street": " Calle 1 ", "City": "Medellín"},
            ],
        }]
        flow_config = {
            "mapping": {
                "CardCode": "identificacion", "CardName": "nombre",
                "EmailAddress": "email",
            },
            "mapping_lineas": {
                "origen": "BPAddresses",
                "campos": {
                    "AddressName": "sucursal", "Street": "direccion", "City": "ciudad",
                },
            },
            "hardcodes": {"pais": "Colombia"}, "conditionals": [],
        }
        result = t._normalize_partners(raw, flow_config)
        assert len(result) == 1
        assert result[0]["nombre"] == "Empresa X"
        assert result[0]["identificacion"] == "900123456"
        assert result[0]["sucursal"] == "SUC01"
        assert result[0]["direccion"] == "Calle 1"
        assert result[0]["pais"] == "Colombia"

    # -- _normalize_purchases
    def test_normalize_purchases_combined_mapping(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [{
            "DocNum": 12345, "CardCode": "P-ACME", "DocDate": "2026-01-15T00:00:00",
            "DocumentLines": [
                {"ItemCode": "SKU001", "Quantity": "10", "UnitPrice": "5.50",
                 "WarehouseCode": "WH01"},
            ],
        }]
        flow_config = {
            "mapping": {
                "DocNum": "compra", "CardCode": "proveedor", "DocDate": "fecha_entrega",
            },
            "mapping_lineas": {
                "origen": "DocumentLines",
                "campos": {
                    "ItemCode": "producto", "Quantity": "cantidad",
                    "UnitPrice": "precio_unitario", "WarehouseCode": "bodega_sap",
                },
            },
            "hardcodes": {
                "sucursal_proveedor": "000", "estado": "draft",
                "almacen": "ALM01", "impuesto": 19,
            },
            "conditionals": [],
        }
        result = t._normalize_purchases(raw, flow_config)
        assert len(result) == 1
        assert result[0]["proveedor"] == "P-ACME"
        assert result[0]["producto"] == "SKU001"
        assert result[0]["bodega_sap"] == "WH01"
        assert result[0]["estado"] == "draft"
        assert result[0]["sucursal_proveedor"] == "000"
        assert result[0]["cantidad"] == 10.0
        assert result[0]["precio_unitario"] == 5.50
        assert result[0]["fecha_entrega"] == "2026-01-15"

    # -- _normalize_sales
    def test_normalize_sales_combined_mapping(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        raw = [{
            "DocNum": 56797, "CardCode": "C-001", "DocDate": "2026-01-15T00:00:00",
            "ShipToCode": "S001",
            "DocumentLines": [
                {"ItemCode": "SKU001", "Quantity": "5", "UnitPrice": "200",
                 "WarehouseCode": "WH01"},
            ],
        }]
        flow_config = {
            "mapping": {
                "DocNum": "pedido", "CardCode": "cliente", "DocDate": "fecha_pedido",
                "ShipToCode": "sucursal_cliente",
            },
            "mapping_lineas": {
                "origen": "DocumentLines",
                "campos": {
                    "ItemCode": "producto", "Quantity": "cantidad_pedida",
                    "UnitPrice": "precio_unitario", "WarehouseCode": "bodega_sap",
                },
            },
            "hardcodes": {"estado": "draft", "almacen": "ALM01", "impuesto": 19},
            "conditionals": [],
        }
        result = t._normalize_sales(raw, flow_config)
        assert len(result) == 1
        assert result[0]["cliente"] == "C-001"
        assert result[0]["sucursal_cliente"] == "S001"
        assert result[0]["producto"] == "SKU001"
        assert result[0]["estado"] == "draft"
        assert result[0]["cantidad_pedida"] == 5.0
        assert result[0]["precio_unitario"] == 200.0
        assert result[0]["fecha_pedido"] == "2026-01-15"

    def test_normalize_map_tiene_14_flow_names(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = "SESSION-123"
        connector.get.return_value = (True, [])
        flows = [
            "items", "partners",
            "compras", "compras_importacion", "devolucion_in",
            "entrada_directa", "transferencia_entrada", "nota_credito",
            "ventas", "facturas", "devolucion_out",
            "salida_directa", "transferencia_salida", "transferencia_interna",
        ]
        for flow_name in flows:
            result = t.get_flow(connector, flow_name, {"endpoint": "Test"})
            assert result == [], f"Flow {flow_name} debería retornar [] con raw vacío"

    def test_get_flow_exception_retorna_vacio(self):
        from transform.transform_sap import TransformSAP
        t = TransformSAP(SAP_CONFIG)
        connector = MagicMock()
        connector.session_id = "SESSION-123"
        connector.get.side_effect = Exception("Boom")
        result = t.get_flow(connector, "compras", {"endpoint": "PurchaseOrders"})
        assert result == []
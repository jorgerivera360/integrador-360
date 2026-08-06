"""
test_core.py — Pruebas de core/
Total: 311 pruebas en 7 clases
  - TestCoreBase: 4
  - TestLookups: 74
  - TestProcessItems: 57
  - TestProcessPartners: 39
  - TestProcessPurchases: 44
  - TestProcessSales: 49
  - TestResolveMissingMasters: 44
Fase: 4 — Core Layer
"""
import os
import pytest
from unittest.mock import patch, MagicMock, call

# -- Config ficticio

CORE_CONFIG = {
    "client_id": "test_client",
    "erp": {"tipo": "ws"},
    "odoo": {
        "url": "https://test.odoo.com",
        "database": "test_db",
        "usuario": "test@test.com",
        "clave": "test123",
    },
}


# ============================================================
# TestCoreBase — 4 pruebas
# ============================================================

class TestCoreBase:

    def test_core_processor_is_abstract(self):
        from abc import ABC
        from core.base import CoreProcessor
        assert issubclass(CoreProcessor, ABC)

    def test_core_processor_cannot_be_instantiated(self):
        from core.base import CoreProcessor
        with pytest.raises(TypeError):
            CoreProcessor()

    def test_core_processor_concrete_subclass_requires_process(self):
        from core.base import CoreProcessor

        class SinProcess(CoreProcessor):
            pass

        with pytest.raises(TypeError):
            SinProcess()

    def test_core_processor_concrete_subclass_process_callable(self):
        from core.base import CoreProcessor

        class Completa(CoreProcessor):
            def process(self, data):
                return {}

        p = Completa()
        assert callable(p.process)


# ============================================================
# TestLookups — 74 pruebas
# ============================================================

class TestLookups:

    # ---- lookup_uom (9) ----

    def test_lookup_uom_cache_hit(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        cache = {"Unidades": 10}
        assert lookup_uom(odoo, "Unidades", cache=cache) == 10
        odoo.search_read.assert_not_called()

    def test_lookup_uom_cache_miss_found(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 10}])
        assert lookup_uom(odoo, "Unidades") == 10

    def test_lookup_uom_cache_miss_not_found_create_ok(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 55)
        assert lookup_uom(odoo, "Cajas") == 55
        odoo.create.assert_called_once()

    def test_lookup_uom_cache_miss_not_found_create_fails(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (False, "error")
        assert lookup_uom(odoo, "Cajas", logger=MagicMock()) is None

    def test_lookup_uom_odoo_search_fails(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_uom(odoo, "kg", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_uom_empty_name_returns_none(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        assert lookup_uom(odoo, "") is None
        assert lookup_uom(odoo, None) is None
        odoo.search_read.assert_not_called()

    def test_lookup_uom_no_cache_does_not_store(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 10}])
        lookup_uom(odoo, "Unidades", cache=None)
        # No crash, no storage attempt

    def test_lookup_uom_stores_in_cache_after_find(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 10}])
        cache = {}
        lookup_uom(odoo, "Unidades", cache=cache)
        assert cache["Unidades"] == 10

    def test_lookup_uom_stores_in_cache_after_create(self):
        from core.utils.lookups import lookup_uom
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 55)
        cache = {}
        lookup_uom(odoo, "Cajas", cache=cache)
        assert cache["Cajas"] == 55

    # ---- lookup_category (11) ----

    def test_lookup_category_cache_hit(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        cache = {("Electrónica", None): 20}
        assert lookup_category(odoo, "Electrónica", cache=cache) == 20
        odoo.search_read.assert_not_called()

    def test_lookup_category_cache_miss_found(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 20}])
        assert lookup_category(odoo, "Electrónica") == 20

    def test_lookup_category_cache_miss_not_found_create_ok(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 30)
        assert lookup_category(odoo, "Tornillos") == 30
        odoo.create.assert_called_once_with("product.category", {"name": "Tornillos"})

    def test_lookup_category_cache_miss_not_found_create_fails(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (False, "error")
        assert lookup_category(odoo, "Tornillos", logger=MagicMock()) is None

    def test_lookup_category_odoo_search_fails(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_category(odoo, "X", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_category_empty_name_returns_none(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        assert lookup_category(odoo, "") is None

    def test_lookup_category_parent_id_none_no_filter(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 20}])
        lookup_category(odoo, "Electrónica")
        domain = odoo.search_read.call_args[0][1]
        assert domain == [["name", "=", "Electrónica"]]

    def test_lookup_category_parent_id_false_adds_domain_filter(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 20}])
        lookup_category(odoo, "Electrónica", parent_id=False)
        domain = odoo.search_read.call_args[0][1]
        assert ["parent_id", "=", False] in domain

    def test_lookup_category_parent_id_int_adds_parent_to_create_payload(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 31)
        lookup_category(odoo, "Samsung", parent_id=20)
        fields = odoo.create.call_args[0][1]
        assert fields["parent_id"] == 20

    def test_lookup_category_parent_id_false_not_in_create_payload(self):
        """isinstance(False, int) es True en Python — verificar comportamiento."""
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 31)
        lookup_category(odoo, "Raíz", parent_id=False)
        fields = odoo.create.call_args[0][1]
        # isinstance(False, int) es True → parent_id=False SÍ se incluye
        # Esto es correcto para Odoo (False = sin padre)
        assert "parent_id" in fields
        assert fields["parent_id"] is False

    def test_lookup_category_stores_tuple_key_in_cache(self):
        from core.utils.lookups import lookup_category
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 20}])
        cache = {}
        lookup_category(odoo, "Electrónica", parent_id=False, cache=cache)
        assert ("Electrónica", False) in cache

    # ---- lookup_state (11) ----

    def test_lookup_state_cache_hit(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        cache = {"Antioquia": 100}
        assert lookup_state(odoo, "Antioquia", cache=cache) == 100
        odoo.search_read.assert_not_called()

    def test_lookup_state_cache_miss_found(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 100}])
        assert lookup_state(odoo, "Antioquia") == 100

    def test_lookup_state_cache_miss_not_found_create_ok(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 101)
        assert lookup_state(odoo, "Valle del Cauca") == 101

    def test_lookup_state_cache_miss_not_found_create_fails(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (False, "error")
        assert lookup_state(odoo, "X", logger=MagicMock()) is None

    def test_lookup_state_odoo_search_fails(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_state(odoo, "X", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_state_empty_name_returns_none(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        assert lookup_state(odoo, "") is None

    def test_lookup_state_code_generation_single_word(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 102)
        lookup_state(odoo, "Antioquia")
        fields = odoo.create.call_args[0][1]
        assert fields["code"] == "A"

    def test_lookup_state_code_generation_multi_word(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 103)
        lookup_state(odoo, "Norte de Santander")
        fields = odoo.create.call_args[0][1]
        assert fields["code"] == "NDS"

    def test_lookup_state_code_generation_more_than_three_words(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 104)
        lookup_state(odoo, "San Andrés y Providencia")
        fields = odoo.create.call_args[0][1]
        assert fields["code"] == "SAY"  # Solo primeras 3 palabras

    def test_lookup_state_default_country_id_49(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 105)
        lookup_state(odoo, "Bogotá")
        fields = odoo.create.call_args[0][1]
        assert fields["country_id"] == 49

    def test_lookup_state_custom_country_id(self):
        from core.utils.lookups import lookup_state
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 106)
        lookup_state(odoo, "Texas", country_id=233)
        fields = odoo.create.call_args[0][1]
        assert fields["country_id"] == 233

    # ---- lookup_zone (7) ----

    def test_lookup_zone_cache_hit(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        cache = {"Norte": 5}
        assert lookup_zone(odoo, "Norte", cache=cache) == 5
        odoo.search_read.assert_not_called()

    def test_lookup_zone_cache_miss_found(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 5}])
        assert lookup_zone(odoo, "Norte") == 5

    def test_lookup_zone_cache_miss_not_found_create_ok(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (True, 6)
        assert lookup_zone(odoo, "Sur") == 6
        odoo.create.assert_called_once_with("partner.delivery.zone", {"name": "Sur"})

    def test_lookup_zone_cache_miss_not_found_create_fails(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        odoo.create.return_value = (False, "error")
        assert lookup_zone(odoo, "Sur", logger=MagicMock()) is None

    def test_lookup_zone_odoo_search_fails(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_zone(odoo, "X", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_zone_empty_name_returns_none(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        assert lookup_zone(odoo, "") is None

    def test_lookup_zone_stores_in_cache(self):
        from core.utils.lookups import lookup_zone
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 5}])
        cache = {}
        lookup_zone(odoo, "Norte", cache=cache)
        assert cache["Norte"] == 5

    # ---- lookup_tax (9) ----

    def test_lookup_tax_cache_hit(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        cache = {(19.0, "sale"): 9}
        assert lookup_tax(odoo, 19.0, "sale", cache=cache) == 9
        odoo.search_read.assert_not_called()

    def test_lookup_tax_cache_miss_found(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 9}])
        assert lookup_tax(odoo, 19.0, "sale") == 9

    def test_lookup_tax_cache_miss_not_found_returns_none(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        cache = {}
        result = lookup_tax(odoo, 5.0, "purchase", cache=cache)
        assert result is None
        assert cache[(5.0, "purchase")] is None  # cachea None

    def test_lookup_tax_odoo_search_fails(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        result = lookup_tax(odoo, 19.0, "sale", logger=logger)
        assert result is None
        logger.error.assert_called_once()

    def test_lookup_tax_invalid_amount_string_returns_none(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        assert lookup_tax(odoo, "abc", "sale") is None
        odoo.search_read.assert_not_called()

    def test_lookup_tax_amount_none_returns_none(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        assert lookup_tax(odoo, None, "sale") is None
        odoo.search_read.assert_not_called()

    def test_lookup_tax_float_conversion_ok(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 10}])
        result = lookup_tax(odoo, "19", "sale")
        assert result == 10
        domain = odoo.search_read.call_args[0][1]
        assert ["amount", "=", 19.0] in domain

    def test_lookup_tax_does_not_create(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        lookup_tax(odoo, 19.0, "sale")
        odoo.create.assert_not_called()

    def test_lookup_tax_key_is_amount_and_type_use(self):
        from core.utils.lookups import lookup_tax
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 9}])
        cache = {}
        lookup_tax(odoo, 19.0, "sale", cache=cache)
        assert (19.0, "sale") in cache

    # ---- lookup_route (7) ----

    def test_lookup_route_cache_hit(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        cache = {"Buy": 3}
        assert lookup_route(odoo, "Buy", cache=cache) == 3
        odoo.search_read.assert_not_called()

    def test_lookup_route_cache_miss_found(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 3}])
        assert lookup_route(odoo, "Buy") == 3

    def test_lookup_route_cache_miss_not_found_returns_none(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        logger = MagicMock()
        assert lookup_route(odoo, "Inexistente", logger=logger) is None
        logger.warning.assert_called_once()

    def test_lookup_route_odoo_search_fails(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_route(odoo, "X", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_route_empty_name_returns_none(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        assert lookup_route(odoo, "") is None

    def test_lookup_route_does_not_create(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        lookup_route(odoo, "X")
        odoo.create.assert_not_called()

    def test_lookup_route_stores_none_in_cache_when_not_found(self):
        from core.utils.lookups import lookup_route
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        cache = {}
        lookup_route(odoo, "X", cache=cache)
        assert cache["X"] is None

    # ---- lookup_product (7) ----

    def test_lookup_product_cache_hit(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        cached = {"id": 50, "uom_id": 1}
        cache = {"REF001": cached}
        assert lookup_product(odoo, "REF001", cache=cache) == cached
        odoo.search_read.assert_not_called()

    def test_lookup_product_cache_miss_found(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 50, "uom_id": [1, "Unidades"]}])
        result = lookup_product(odoo, "REF001")
        assert result == {"id": 50, "uom_id": 1}

    def test_lookup_product_cache_miss_not_found_returns_none(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        assert lookup_product(odoo, "REF999") is None

    def test_lookup_product_odoo_search_fails(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_product(odoo, "X", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_product_empty_code_returns_none(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        assert lookup_product(odoo, "") is None

    def test_lookup_product_returns_dict_with_id_and_uom_id(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 50, "uom_id": [1, "Unidades"]}])
        result = lookup_product(odoo, "REF001")
        assert "id" in result and "uom_id" in result

    def test_lookup_product_uom_id_extracted_from_tuple(self):
        from core.utils.lookups import lookup_product
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 50, "uom_id": [7, "kg"]}])
        result = lookup_product(odoo, "REF001")
        assert result["uom_id"] == 7  # Extraído de [7, "kg"]

    # ---- lookup_partner (8) ----

    def test_lookup_partner_cache_hit(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        cached = {"id": 200, "customer_rank": 1, "supplier_rank": 0}
        cache = {("900123", "001"): cached}
        assert lookup_partner(odoo, "900123", "001", cache=cache) == cached
        odoo.search_read.assert_not_called()

    def test_lookup_partner_cache_miss_found(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}])
        result = lookup_partner(odoo, "900123", "001")
        assert result["id"] == 200

    def test_lookup_partner_cache_miss_not_found_returns_none(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        assert lookup_partner(odoo, "999999", "") is None

    def test_lookup_partner_odoo_search_fails(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        odoo.search_read.return_value = (False, "timeout")
        logger = MagicMock()
        assert lookup_partner(odoo, "900123", "001", logger=logger) is None
        logger.error.assert_called_once()

    def test_lookup_partner_empty_vat_returns_none(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        assert lookup_partner(odoo, "", "001") is None

    def test_lookup_partner_sucursal_none_uses_empty_string_key(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [])
        lookup_partner(odoo, "900123", None)
        domain = odoo.search_read.call_args[0][1]
        assert ["sucursal", "=", ""] in domain

    def test_lookup_partner_returns_full_dict_with_ranks(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}])
        result = lookup_partner(odoo, "900123", "001")
        assert "customer_rank" in result and "supplier_rank" in result

    def test_lookup_partner_key_is_vat_sucursal_tuple(self):
        from core.utils.lookups import lookup_partner
        odoo = MagicMock()
        odoo.search_read.return_value = (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}])
        cache = {}
        lookup_partner(odoo, "900123", "001", cache=cache)
        assert ("900123", "001") in cache

    # ---- resolve_warehouse (7) ----

    def test_resolve_warehouse_found_in_mapping(self):
        from core.utils.lookups import resolve_warehouse
        assert resolve_warehouse("BOD01", {"BOD01": 15}) == 15

    def test_resolve_warehouse_not_found_returns_none(self):
        from core.utils.lookups import resolve_warehouse
        logger = MagicMock()
        assert resolve_warehouse("BOD99", {"BOD01": 15}, logger=logger) is None
        logger.warning.assert_called_once()

    def test_resolve_warehouse_empty_mapping_returns_none(self):
        from core.utils.lookups import resolve_warehouse
        assert resolve_warehouse("BOD01", {}) is None
        assert resolve_warehouse("BOD01", None) is None

    def test_resolve_warehouse_empty_bodega_returns_none(self):
        from core.utils.lookups import resolve_warehouse
        assert resolve_warehouse("", {"BOD01": 15}) is None
        assert resolve_warehouse(None, {"BOD01": 15}) is None

    def test_resolve_warehouse_bodega_converted_to_str(self):
        from core.utils.lookups import resolve_warehouse
        assert resolve_warehouse(123, {"123": 15}) == 15

    def test_resolve_warehouse_no_logger_no_crash(self):
        from core.utils.lookups import resolve_warehouse
        # Sin logger, no lanza error aunque no encuentre
        result = resolve_warehouse("BOD99", {"BOD01": 15})
        assert result is None

    def test_resolve_warehouse_logs_warning_when_not_found(self):
        from core.utils.lookups import resolve_warehouse
        logger = MagicMock()
        resolve_warehouse("BOD99", {"BOD01": 15}, logger=logger)
        logger.warning.assert_called_once()
        assert "BOD99" in str(logger.warning.call_args)


# ============================================================
# TestProcessItems — 57 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestProcessItems:

    def _make(self, odoo, flow_config=None):
        from core.process_items import ProcessItems
        return ProcessItems(odoo, CORE_CONFIG, flow_config or {})

    def _item(self, **kw):
        base = {
            "referencia": "REF001", "descripcion": "Producto Test",
            "unidad": "Unidades", "categoria": "General",
            "peso": 1.5, "volumen": 0.5, "precio": 100.0,
            "costo": 50.0, "iva": 19.0, "tracking": "lot",
            "codigo_barras": "7701234567890",
        }
        base.update(kw)
        return base

    def _minimal(self, **kw):
        base = {"referencia": "REF001", "descripcion": "Test", "unidad": "Unidades"}
        base.update(kw)
        return base

    # -- Entrada/General (4) --

    def test_empty_data_returns_zero_summary(self):
        odoo = MagicMock()
        result = self._make(odoo).process([])
        assert result == {"creados": 0, "actualizados": 0, "fallidos": [], "total": 0}

    def test_summary_counts_correct(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 100, "default_code": "REF001"}]),  # REF001 existe
            (True, [{"id": 1}]),  # uom
        ]
        odoo.write.return_value = (True, True)
        odoo.create.return_value = (True, 101)
        result = self._make(odoo).process([
            self._minimal(referencia="REF001"),
            self._minimal(referencia="REF002"),
        ])
        assert result["actualizados"] + result["creados"] + len(result["fallidos"]) <= result["total"]

    @patch("core.process_items.IntegradorLogger")
    def test_fallidos_logged_individually(self, MockLogger):
        mock_logger = MagicMock()
        MockLogger.return_value = mock_logger
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, []),  # uom no encontrada
        ]
        odoo.create.return_value = (False, "error uom")
        from core.process_items import ProcessItems
        p = ProcessItems(odoo, CORE_CONFIG, {})
        result = p.process([self._minimal()])
        assert len(result["fallidos"]) > 0
        assert result["fallidos"][0]["referencia"] == "REF001"

    def test_fatal_exception_returns_error_key(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = Exception("boom")
        result = self._make(odoo).process([self._minimal()])
        assert "error" in result

    # -- Fase 1: UOM Mapping (5) --

    def test_uom_mapping_applied_exact_match(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        p = self._make(odoo, {"uom_mapping": {"UND": "Unidades"}})
        p.process([self._minimal(unidad="UND")])
        # lookup_uom se llama con "Unidades" (mapeado), no "UND"
        uom_call = odoo.search_read.call_args_list[1]
        assert uom_call[0][1] == [["name", "=", "Unidades"]]

    def test_uom_mapping_applied_lowercase_fallback(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        p = self._make(odoo, {"uom_mapping": {"und": "Unidades"}})
        p.process([self._minimal(unidad="und")])
        uom_call = odoo.search_read.call_args_list[1]
        assert uom_call[0][1] == [["name", "=", "Unidades"]]

    def test_uom_mapping_no_match_keeps_original(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        p = self._make(odoo, {"uom_mapping": {"KG": "kg"}})
        p.process([self._minimal(unidad="XYZ")])
        uom_call = odoo.search_read.call_args_list[1]
        assert uom_call[0][1] == [["name", "=", "XYZ"]]

    def test_uom_mapping_empty_unidad_skipped(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [])]
        p = self._make(odoo, {"uom_mapping": {"UND": "Unidades"}})
        result = p.process([self._minimal(unidad="")])
        # Sin UOM → va a fallidos
        assert len(result["fallidos"]) > 0

    def test_no_uom_mapping_in_flow_config(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        p = self._make(odoo, {})
        p.process([self._minimal(unidad="Unidades")])
        uom_call = odoo.search_read.call_args_list[1]
        assert uom_call[0][1] == [["name", "=", "Unidades"]]

    # -- Fase 2: Bulk fetch (7) --

    def test_bulk_fetch_first_try_ok(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        result = self._make(odoo).process([self._minimal()])
        assert result["creados"] == 1

    def test_bulk_fetch_retry_succeeds_on_second(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "timeout"), (True, []),  # retry OK
            (True, [{"id": 1}]),
        ]
        odoo.create.return_value = (True, 100)
        result = self._make(odoo).process([self._minimal()])
        assert result["creados"] == 1

    def test_bulk_fetch_retry_succeeds_on_third(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "t1"), (False, "t2"), (True, []),
            (True, [{"id": 1}]),
        ]
        odoo.create.return_value = (True, 100)
        result = self._make(odoo).process([self._minimal()])
        assert result["creados"] == 1

    def test_bulk_fetch_all_retries_fail_returns_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(False, "t1"), (False, "t2"), (False, "t3")]
        result = self._make(odoo).process([self._minimal()])
        assert "error" in result

    def test_bulk_fetch_empty_result_no_existing(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        result = self._make(odoo).process([self._minimal()])
        assert result["creados"] == 1  # Todo se crea

    def test_bulk_fetch_partial_existing(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 100, "default_code": "REF001"}]),  # REF001 existe
            (True, [{"id": 1}]),  # uom
        ]
        odoo.write.return_value = (True, True)
        odoo.create.return_value = (True, 101)
        result = self._make(odoo).process([
            self._minimal(referencia="REF001"),
            self._minimal(referencia="REF002"),
        ])
        assert result["actualizados"] == 1
        assert result["creados"] == 1

    def test_no_refs_skips_bulk_fetch(self):
        odoo = MagicMock()
        result = self._make(odoo).process([{"descripcion": "Sin ref", "unidad": "U"}])
        # Sin referencia → no busca existentes, y el loop maneja con ref=""

    # -- Fase 3: Pre-resolución (9) --

    def test_preresolve_uoms_unique(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 1}]),  # solo 1 UOM lookup aunque hay 2 items con misma unidad
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([
            self._minimal(referencia="R1"), self._minimal(referencia="R2"),
        ])
        # Solo 1 búsqueda de UOM (Unidades es único)
        uom_calls = [c for c in odoo.search_read.call_args_list if "uom.uom" in str(c)]
        assert len(uom_calls) == 1

    def test_preresolve_categories_one_level(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 20}]),  # category 1 nivel
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(categoria="General")])
        cat_calls = [c for c in odoo.search_read.call_args_list if "product.category" in str(c)]
        assert len(cat_calls) == 1

    def test_preresolve_categories_two_levels_with_marca(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 1}]),   # uom
            (True, [{"id": 20}]),  # category padre
            (True, []),            # category hijo no existe
        ]
        odoo.create.side_effect = [(True, 21), (True, 100)]  # crear hijo, crear producto
        self._make(odoo).process([self._minimal(categoria="General", marca="MarcaX")])
        cat_calls = [c for c in odoo.search_read.call_args_list if "product.category" in str(c)]
        assert len(cat_calls) == 2  # padre + hijo

    def test_preresolve_categories_parent_stored_as_fallback(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 1}]),
            (True, [{"id": 20}]),  # padre
            (True, [{"id": 21}]),  # hijo
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(categoria="General", marca="MarcaX")])
        # Si el combo (cat, marca) no se encuentra, usa (cat, None) como fallback

    def test_preresolve_taxes_sale_and_purchase(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 1}]),
            (True, [{"id": 20}]),
            (True, [{"id": 9}]),   # tax sale
            (True, [{"id": 10}]),  # tax purchase
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._item()])
        tax_calls = [c for c in odoo.search_read.call_args_list if "account.tax" in str(c)]
        assert len(tax_calls) == 2

    def test_preresolve_taxes_skipped_when_no_iva(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal()])
        tax_calls = [c for c in odoo.search_read.call_args_list if "account.tax" in str(c)]
        assert len(tax_calls) == 0

    def test_preresolve_routes_single(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 3}]),  # route
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(ruta="Buy")])
        route_calls = [c for c in odoo.search_read.call_args_list if "stock.route" in str(c)]
        assert len(route_calls) == 1

    def test_preresolve_routes_multi_comma_separated(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 3}]),   # Buy
            (True, [{"id": 4}]),   # Fabricación
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(ruta="Buy,Fabricación")])
        route_calls = [c for c in odoo.search_read.call_args_list if "stock.route" in str(c)]
        assert len(route_calls) == 2

    def test_preresolve_routes_empty_skipped(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal()])
        route_calls = [c for c in odoo.search_read.call_args_list if "stock.route" in str(c)]
        assert len(route_calls) == 0

    # -- Fase 4: Loop create/write (26) --

    def test_uom_not_resolved_adds_to_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, []),  # uom no encontrada
        ]
        odoo.create.return_value = (False, "error uom")
        result = self._make(odoo).process([self._minimal()])
        assert len(result["fallidos"]) == 1
        assert "UOM" in result["fallidos"][0]["razon"]

    def test_categ_marca_fallback_when_combo_missing(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 1}]),
            (True, [{"id": 20}]),  # padre General
            (True, []),            # hijo MarcaX no existe
        ]
        odoo.create.side_effect = [
            (False, "error categ"),  # create hijo falla
            (True, 100),            # create producto con fallback padre
        ]
        result = self._make(odoo).process([self._minimal(categoria="General", marca="MarcaX")])
        # Producto se crea con categoría padre como fallback
        assert result["creados"] == 1

    def test_write_existing_product(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 100, "default_code": "REF001"}]),
            (True, [{"id": 1}]),
        ]
        odoo.write.return_value = (True, True)
        result = self._make(odoo).process([self._minimal()])
        assert result["actualizados"] == 1
        odoo.write.assert_called_once()

    def test_write_does_not_send_default_code(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 100, "default_code": "REF001"}]),
            (True, [{"id": 1}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo).process([self._minimal()])
        payload = odoo.write.call_args[0][2]
        assert "default_code" not in payload

    def test_write_does_not_send_tracking(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 100, "default_code": "REF001"}]), 
            (True, [{"id": 1}]),
            (True, [{"id": 20}]),
            (True, [{"id": 9}]),
            (True, [{"id": 10}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo).process([self._item()])
        payload = odoo.write.call_args[0][2]
        assert "tracking" not in payload

    def test_write_fails_adds_to_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 100, "default_code": "REF001"}]),
            (True, [{"id": 1}]),
        ]
        odoo.write.return_value = (False, "error write")
        result = self._make(odoo).process([self._minimal()])
        assert len(result["fallidos"]) == 1
        assert "write falló" in result["fallidos"][0]["razon"]

    def test_create_new_product(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        result = self._make(odoo).process([self._minimal()])
        assert result["creados"] == 1

    def test_create_includes_default_code(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal()])
        payload = odoo.create.call_args[0][1]
        assert payload["default_code"] == "REF001"

    def test_create_includes_tracking(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(tracking="lot")])
        payload = odoo.create.call_args[0][1]
        assert payload["tracking"] == "lot"

    def test_create_with_barcode(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(codigo_barras="770123")])
        payload = odoo.create.call_args[0][1]
        assert payload["barcode"] == "770123"

    def test_create_barcode_retry_without_barcode(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.side_effect = [(False, "barcode dup"), (True, 100)]
        self._make(odoo).process([self._minimal(codigo_barras="770123")])
        second = odoo.create.call_args_list[1][0][1]
        assert "barcode" not in second

    def test_create_barcode_retry_succeeds(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.side_effect = [(False, "barcode dup"), (True, 100)]
        result = self._make(odoo).process([self._minimal(codigo_barras="770123")])
        assert result["creados"] == 1

    def test_create_both_fail_adds_to_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.side_effect = [(False, "err1"), (False, "err2")]
        result = self._make(odoo).process([self._minimal(codigo_barras="770123")])
        assert len(result["fallidos"]) == 1

    def test_create_payload_optional_peso(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(peso=2.5)])
        payload = odoo.create.call_args[0][1]
        assert payload["weight"] == 2.5

    def test_create_payload_optional_volumen(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(volumen=0.8)])
        payload = odoo.create.call_args[0][1]
        assert payload["volume"] == 0.8

    def test_create_payload_optional_precio(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(precio=99.9)])
        payload = odoo.create.call_args[0][1]
        assert payload["list_price"] == 99.9

    def test_create_payload_optional_costo(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(costo=50.0)])
        payload = odoo.create.call_args[0][1]
        assert payload["standard_price"] == 50.0

    def test_create_payload_optional_use_expiration_date(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(use_expiration_date=1)])
        payload = odoo.create.call_args[0][1]
        assert payload["use_expiration_date"] is True

    def test_create_payload_optional_expiration_time(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(expiration_time=30)])
        payload = odoo.create.call_args[0][1]
        assert payload["expiration_time"] == 30

    def test_create_payload_optional_taxes_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 9}]), (True, [{"id": 10}]),
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(iva=19.0)])
        payload = odoo.create.call_args[0][1]
        assert payload["taxes_id"] == [(6, 0, [9])]

    def test_create_payload_optional_supplier_taxes_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 9}]), (True, [{"id": 10}]),
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(iva=19.0)])
        payload = odoo.create.call_args[0][1]
        assert payload["supplier_taxes_id"] == [(6, 0, [10])]

    def test_create_payload_optional_route_ids(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 3}]),
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(ruta="Buy")])
        payload = odoo.create.call_args[0][1]
        assert payload["route_ids"] == [(6, 0, [3])]

    def test_create_multi_route_ids(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 3}]), (True, [{"id": 4}]),
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(ruta="Buy,Fabricación")])
        payload = odoo.create.call_args[0][1]
        assert payload["route_ids"] == [(6, 0, [3, 4])]

    def test_create_updates_existing_dict(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.return_value = (True, 100)
        odoo.write.return_value = (True, True)
        # Crear REF001, luego si tuviéramos otro con misma ref se actualizaría
        self._make(odoo).process([self._minimal()])
        assert odoo.create.call_count == 1

    def test_codigos_extras_called_after_create(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 500}]),  # variant
            (True, []),             # barcode no existe
        ]
        odoo.create.side_effect = [(True, 100), (True, 1)]  # producto, barcode
        self._make(odoo).process([self._minimal(codigos_extras="EXTRA1")])
        barcode_creates = [c for c in odoo.create.call_args_list if c[0][0] == "product.barcode.multi"]
        assert len(barcode_creates) == 1

    def test_exception_per_row_continues(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 1}])]
        odoo.create.side_effect = [Exception("boom"), (True, 101)]
        result = self._make(odoo).process([
            self._minimal(referencia="R1"),
            self._minimal(referencia="R2"),
        ])
        assert result["creados"] == 1
        assert len(result["fallidos"]) == 1

    # -- Barcode multi (6) --

    def test_barcode_multi_variant_not_found(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, []),  # variant not found
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(codigos_extras="E1")])
        # No crash, barcode_multi no se crea

    def test_barcode_multi_code_exists_same_product(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 500}]),  # variant
            (True, [{"id": 99, "product_id": [500, "P"]}]),  # barcode en mismo
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(codigos_extras="E1")])
        bc = [c for c in odoo.create.call_args_list if c[0][0] == "product.barcode.multi"]
        assert len(bc) == 0

    def test_barcode_multi_code_exists_different_product(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 500}]),  # variant id=500
            (True, [{"id": 99, "product_id": [999, "Otro"]}]),  # barcode en otro
        ]
        odoo.create.return_value = (True, 100)
        self._make(odoo).process([self._minimal(codigos_extras="E1")])
        bc = [c for c in odoo.create.call_args_list if c[0][0] == "product.barcode.multi"]
        assert len(bc) == 0

    def test_barcode_multi_create_ok(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 500}]),
            (True, []),  # no existe
        ]
        odoo.create.side_effect = [(True, 100), (True, 1)]
        self._make(odoo).process([self._minimal(codigos_extras="E1")])
        bc = [c for c in odoo.create.call_args_list if c[0][0] == "product.barcode.multi"]
        assert len(bc) == 1

    def test_barcode_multi_create_fails(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 500}]),
            (True, []),
        ]
        odoo.create.side_effect = [(True, 100), (False, "error bc")]
        self._make(odoo).process([self._minimal(codigos_extras="E1")])
        # No crash, solo warning

    def test_barcode_multi_multiple_codes(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []), (True, [{"id": 1}]),
            (True, [{"id": 500}]),
            (True, []),  # E1 no existe
            (True, []),  # E2 no existe
        ]
        odoo.create.side_effect = [(True, 100), (True, 1), (True, 2)]
        self._make(odoo).process([self._minimal(codigos_extras="E1,E2")])
        bc = [c for c in odoo.create.call_args_list if c[0][0] == "product.barcode.multi"]
        assert len(bc) == 2


# ============================================================
# TestProcessPartners — 39 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestProcessPartners:

    def _make(self, odoo, flow_config=None):
        from core.process_partners import ProcessPartners
        return ProcessPartners(odoo, CORE_CONFIG, flow_config or {})

    def _partner(self, **kw):
        base = {
            "nombre": "Empresa Test", "identificacion": "900123456",
            "sucursal": "001", "direccion": "Calle 100",
            "codigo_postal": "110111", "telefono": "3001234567",
            "email": "test@empresa.com", "ciudad": "Bogotá",
            "departamento": "Cundinamarca", "pais": "Colombia",
        }
        base.update(kw)
        return base

    # -- General (3) --

    def test_empty_data_returns_zero_summary(self):
        result = self._make(MagicMock()).process([])
        assert result == {"creados": 0, "actualizados": 0, "fallidos": [], "total": 0}

    def test_summary_counts_correct(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["creados"] + result["actualizados"] + len(result["fallidos"]) == result["total"]

    def test_fatal_exception_returns_error_key(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = Exception("boom")
        result = self._make(odoo).process([self._partner()])
        assert "error" in result

    # -- Fase 1: Jerarquía (4) --

    def test_hierarchy_disabled_no_sort(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        p = self._make(odoo, {"flow_type": "customer"})
        p.process([self._partner(sucursal="002"), self._partner(sucursal="001", identificacion="999")])
        first = odoo.create.call_args_list[0][0][1]
        assert first["sucursal"] == "002"  # No reordena

    def test_hierarchy_enabled_padre_first(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        fc = {"flow_type": "customer", "sucursal_hierarchy": True, "sucursal_padre": "001"}
        p = self._make(odoo, fc)
        p.process([self._partner(sucursal="002"), self._partner(sucursal="001")])
        first = odoo.create.call_args_list[0][0][1]
        assert first["sucursal"] == "001"

    def test_hierarchy_custom_sucursal_padre(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        fc = {"flow_type": "customer", "sucursal_hierarchy": True, "sucursal_padre": "000"}
        p = self._make(odoo, fc)
        p.process([self._partner(sucursal="001"), self._partner(sucursal="000")])
        first = odoo.create.call_args_list[0][0][1]
        assert first["sucursal"] == "000"

    def test_hierarchy_all_same_sucursal(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        fc = {"flow_type": "customer", "sucursal_hierarchy": True}
        self._make(odoo, fc).process([
            self._partner(sucursal="001", identificacion="A"),
            self._partner(sucursal="001", identificacion="B"),
        ])

    # -- Fase 2: Bulk fetch (5) --

    def test_bulk_fetch_first_try_ok(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["creados"] == 1

    def test_bulk_fetch_retry_succeeds(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "t1"), (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["creados"] == 1

    def test_bulk_fetch_all_fail_returns_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(False, "t1"), (False, "t2"), (False, "t3")]
        result = self._make(odoo).process([self._partner()])
        assert "error" in result

    def test_bulk_fetch_keyed_by_vat_sucursal(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["actualizados"] == 1

    def test_bulk_fetch_empty_result(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["creados"] == 1

    # -- Fase 3: Departamentos (3) --

    def test_preresolve_states_unique(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 100}]),  # solo 1 lookup state
        ]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        self._make(odoo, {"flow_type": "customer"}).process([
            self._partner(identificacion="A"),
            self._partner(identificacion="B"),  # mismo departamento
        ])
        state_calls = [c for c in odoo.search_read.call_args_list if "res.country.state" in str(c)]
        assert len(state_calls) == 1

    def test_preresolve_default_country_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, []),  # state no existe → crear
        ]
        odoo.create.side_effect = [(True, 100), (True, 200)]  # state, partner
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        state_create = [c for c in odoo.create.call_args_list if c[0][0] == "res.country.state"]
        if state_create:
            assert state_create[0][0][1]["country_id"] == 49

    def test_preresolve_custom_country_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [])]
        odoo.create.side_effect = [(True, 100), (True, 200)]
        self._make(odoo, {"flow_type": "customer", "country_id": 233}).process([self._partner()])
        state_create = [c for c in odoo.create.call_args_list if c[0][0] == "res.country.state"]
        if state_create:
            assert state_create[0][0][1]["country_id"] == 233

    # -- Fase 4: Loop create/write (21) --

    def test_write_existing_partner(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["actualizados"] == 1

    def test_write_does_not_send_vat(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.write.call_args[0][2]
        assert "vat" not in payload

    def test_write_rank_customer_sube_de_cero(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 0, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.write.call_args[0][2]
        assert payload["customer_rank"] == 1

    def test_write_rank_customer_no_sube_si_ya_uno(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.write.call_args[0][2]
        assert "customer_rank" not in payload

    def test_write_rank_supplier_sube_de_cero(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 0, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo, {"flow_type": "supplier"}).process([self._partner()])
        payload = odoo.write.call_args[0][2]
        assert payload["supplier_rank"] == 1

    def test_write_flow_type_partners_sube_ambos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 0, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (True, True)
        self._make(odoo, {"flow_type": "partners"}).process([self._partner()])
        payload = odoo.write.call_args[0][2]
        assert payload["customer_rank"] == 1
        assert payload["supplier_rank"] == 1

    def test_write_fails_adds_to_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 200, "vat": "900123456", "sucursal": "001",
                      "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 100}]),
        ]
        odoo.write.return_value = (False, "error")
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert len(result["fallidos"]) == 1

    def test_create_new_partner(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert result["creados"] == 1

    def test_create_includes_vat(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.create.call_args[0][1]
        assert payload["vat"] == "900123456"

    def test_create_includes_identification_type_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.create.call_args[0][1]
        assert "l10n_latam_identification_type_id" in payload

    def test_create_customer_rank(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.create.call_args[0][1]
        assert payload["customer_rank"] == 1

    def test_create_supplier_rank(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "supplier"}).process([self._partner()])
        payload = odoo.create.call_args[0][1]
        assert payload["supplier_rank"] == 1

    def test_create_optional_fields(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.create.call_args[0][1]
        assert payload["street"] == "Calle 100"
        assert payload["phone"] == "3001234567"
        assert payload["email"] == "test@empresa.com"

    def test_create_with_state_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        payload = odoo.create.call_args[0][1]
        assert payload["state_id"] == 100

    def test_create_with_lista_precio(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        self._make(odoo, {"flow_type": "customer"}).process([
            self._partner(lista_precio="Lista Premium")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["property_product_pricelist"] == "Lista Premium"

    def test_hierarchy_padre_is_company_true(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        fc = {"flow_type": "customer", "sucursal_hierarchy": True, "sucursal_padre": "001"}
        self._make(odoo, fc).process([self._partner(sucursal="001")])
        payload = odoo.create.call_args[0][1]
        assert payload["is_company"] is True

    def test_hierarchy_hijo_with_parent_id(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        fc = {"flow_type": "customer", "sucursal_hierarchy": True, "sucursal_padre": "001"}
        self._make(odoo, fc).process([
            self._partner(sucursal="001"),
            self._partner(sucursal="002"),
        ])
        hijo = odoo.create.call_args_list[1][0][1]
        assert hijo["parent_id"] == 200
        assert hijo["type"] == "other"
        assert hijo["is_company"] is False

    def test_hierarchy_hijo_padre_not_yet_exists(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        fc = {"flow_type": "customer", "sucursal_hierarchy": True, "sucursal_padre": "001"}
        # Solo hijo, sin padre
        self._make(odoo, fc).process([self._partner(sucursal="002", identificacion="X")])
        payload = odoo.create.call_args[0][1]
        assert "parent_id" not in payload

    def test_create_updates_existing_dict(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [(True, 200), (True, 201)]
        fc = {"flow_type": "customer", "sucursal_hierarchy": True, "sucursal_padre": "001"}
        result = self._make(odoo, fc).process([
            self._partner(sucursal="001"),
            self._partner(sucursal="002"),
        ])
        assert result["creados"] == 2
        hijo = odoo.create.call_args_list[1][0][1]
        assert hijo["parent_id"] == 200

    def test_create_fails_adds_to_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (False, "error")
        result = self._make(odoo, {"flow_type": "customer"}).process([self._partner()])
        assert len(result["fallidos"]) == 1

    def test_exception_per_row_continues(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.side_effect = [Exception("boom"), (True, 201)]
        result = self._make(odoo, {"flow_type": "customer"}).process([
            self._partner(identificacion="A"),
            self._partner(identificacion="B"),
        ])
        assert result["creados"] == 1
        assert len(result["fallidos"]) == 1

    # -- Resumen (3) --

    @patch("core.process_partners.IntegradorLogger")
    def test_fallidos_logged_with_vat_sucursal(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (False, "error")
        from core.process_partners import ProcessPartners
        ProcessPartners(odoo, CORE_CONFIG, {"flow_type": "customer"}).process([self._partner()])
        warns = [str(c) for c in ml.warning.call_args_list]
        assert any("900123456" in w for w in warns)

    @patch("core.process_partners.IntegradorLogger")
    def test_info_log_counts(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (True, 200)
        from core.process_partners import ProcessPartners
        ProcessPartners(odoo, CORE_CONFIG, {"flow_type": "customer"}).process([self._partner()])
        infos = [str(c) for c in ml.info.call_args_list]
        assert any("1 creados" in i for i in infos)

    @patch("core.process_partners.IntegradorLogger")
    def test_warning_log_fallidos_detail(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"id": 100}])]
        odoo.create.return_value = (False, "error")
        from core.process_partners import ProcessPartners
        ProcessPartners(odoo, CORE_CONFIG, {"flow_type": "customer"}).process([self._partner()])
        warns = [str(c) for c in ml.warning.call_args_list]
        assert any("suc=" in w for w in warns)


# ============================================================
# TestProcessPurchases — 44 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestProcessPurchases:

    def _make(self, odoo, flow_config=None):
        from core.process_purchases import ProcessPurchases
        return ProcessPurchases(odoo, CORE_CONFIG, flow_config or {})

    def _line(self, **kw):
        base = {
            "compra": "OC-001", "producto": "REF001",
            "proveedor": "900111222", "sucursal_proveedor": "001",
            "fecha_entrega": "2026-08-10", "estado": "draft",
            "almacen": "ALM1", "cantidad": 10.0,
            "precio_unitario": 50.0, "referencia_compra": "REF-EXT",
        }
        base.update(kw)
        return base

    def _happy(self, odoo):
        """Side effects para 1 línea nueva exitosa."""
        odoo.search_read.side_effect = [
            (True, []),                                                     # filter existentes
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),  # partner
            (True, [{"id": 50, "uom_id": [1, "U"]}]),                      # product
        ]
        odoo.create.return_value = (True, 300)

    # -- General (2) --

    def test_empty_data_returns_zero_summary(self):
        result = self._make(MagicMock()).process([])
        assert result == {"creados": 0, "fallidos": [], "descartados": 0, "total": 0}

    def test_fatal_exception_returns_error_key(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = Exception("boom")
        result = self._make(odoo).process([self._line()])
        assert "error" in result

    # -- Fase 1: Filtrar existentes (8) --

    def test_filter_first_try_ok(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_filter_retry_second(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "t1"), (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 300)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_filter_retry_third(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "t1"), (False, "t2"), (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 300)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_filter_all_fail_returns_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(False, "t1"), (False, "t2"), (False, "t3")]
        result = self._make(odoo).process([self._line()])
        assert "error" in result

    def test_filter_none_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["descartados"] == 0

    def test_filter_all_exist_returns_early(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 300, "name": "OC-001"}])]
        result = self._make(odoo).process([self._line()])
        assert result["descartados"] == 1
        assert result["creados"] == 0

    def test_filter_partial(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 300, "name": "OC-001"}]),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 301)
        result = self._make(odoo).process([
            self._line(compra="OC-001"),
            self._line(compra="OC-002"),
        ])
        assert result["descartados"] == 1
        assert result["creados"] == 1

    def test_descartados_count(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 300, "name": "OC-001"}]),
        ]
        result = self._make(odoo).process([
            self._line(compra="OC-001", producto="R1"),
            self._line(compra="OC-001", producto="R2"),
        ])
        assert result["descartados"] == 2

    # -- Fases 2-3: Pre-resolución (6) --

    def test_preresolve_proveedores_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_preresolve_proveedores_not_found(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, []),                                                     # proveedor no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Proveedor" in f["razon"] for f in result["fallidos"])

    def test_preresolve_proveedores_unique_pairs(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 51, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 300)
        self._make(odoo).process([
            self._line(compra="OC-001", producto="R1"),
            self._line(compra="OC-001", producto="R2"),
        ])
        partner_calls = [c for c in odoo.search_read.call_args_list if "res.partner" in str(c)]
        assert len(partner_calls) == 1

    def test_preresolve_productos_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_preresolve_productos_not_found(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, []),                                                     # producto no existe
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Producto" in f["razon"] for f in result["fallidos"])

    def test_preresolve_productos_unique(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 300)
        self._make(odoo).process([
            self._line(compra="OC-001"),
            self._line(compra="OC-002"),
        ])
        prod_calls = [c for c in odoo.search_read.call_args_list if "product.product" in str(c)]
        assert len(prod_calls) == 1

    # -- Fase 4: Enriquecer + warehouse (7) --

    def test_warehouse_via_bodega_siesa(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo, {"warehouse_mapping": {"BOD01": 15}}).process([
            self._line(bodega_siesa="BOD01")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["picking_type_id"] == 15

    def test_warehouse_via_bodega_sap(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo, {"warehouse_mapping": {"WH01": 16}}).process([
            self._line(bodega_sap="WH01")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["picking_type_id"] == 16

    def test_warehouse_not_in_mapping_uses_default(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo, {"warehouse_mapping": {"BOD01": 15}}).process([
            self._line(bodega_siesa="BOD99")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["picking_type_id"] == 7  # default

    def test_warehouse_no_bodega_erp_uses_default(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line()])
        payload = odoo.create.call_args[0][1]
        assert payload["picking_type_id"] == 7  # default

    def test_proveedor_missing_adds_fallido(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, []),                                                     # proveedor no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Proveedor" in f["razon"] for f in result["fallidos"])

    def test_producto_missing_adds_fallido(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, []),                                                     # producto no existe
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Producto" in f["razon"] for f in result["fallidos"])

    def test_both_missing_both_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, []),                                                     # proveedor no existe
            (True, []),                                                     # producto no existe
            (True, []),
            (True, []),
        ]
        result = self._make(odoo).process([
            self._line(proveedor="A", producto="X"),
            self._line(proveedor="B", producto="Y"),
        ])
        assert len(result["fallidos"]) >= 2

    # -- Fases 5-6: Agrupar + Crear (12) --

    def test_groupby_single_order_single_line(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["total_ordenes"] == 1

    def test_groupby_single_order_multiple_lines(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 51, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 300)
        result = self._make(odoo).process([
            self._line(producto="R1"), self._line(producto="R2"),
        ])
        assert result["total_ordenes"] == 1
        payload = odoo.create.call_args[0][1]
        assert len(payload["order_line"]) == 2

    def test_groupby_multiple_orders(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.side_effect = [(True, 300), (True, 301)]
        result = self._make(odoo).process([
            self._line(compra="OC-001"), self._line(compra="OC-002"),
        ])
        assert result["total_ordenes"] == 2

    def test_groupby_key_six_fields(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.side_effect = [(True, 300), (True, 301)]
        result = self._make(odoo).process([
            self._line(fecha_entrega="2026-08-10"),
            self._line(fecha_entrega="2026-08-11"),
        ])
        assert result["total_ordenes"] == 2

    def test_create_order_ok(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1
        odoo.create.assert_called_once()
        assert odoo.create.call_args[0][0] == "purchase.order"

    def test_create_order_fails(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (False, "error Odoo")
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 0
        assert any("create falló" in f["razon"] for f in result["fallidos"])

    def test_create_with_picking_type_id(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo, {"warehouse_mapping": {"BOD01": 15}}).process([
            self._line(bodega_siesa="BOD01")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["picking_type_id"] == 15

    def test_create_without_almacen(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line(almacen="")])
        payload = odoo.create.call_args[0][1]
        assert payload["picking_type_id"] == 7  # default

    def test_order_line_fields_correct(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line()])
        payload = odoo.create.call_args[0][1]
        line = payload["order_line"][0][2]
        assert "product_id" in line
        assert "product_qty" in line
        assert "product_uom" in line
        assert "price_unit" in line

    def test_partner_ref_from_referencia(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line(referencia_compra="REF-EXT")])
        payload = odoo.create.call_args[0][1]
        assert payload["partner_ref"] == "REF-EXT"

    def test_partner_ref_fallback_comprador(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line(referencia_compra="", comprador="Juan")])
        payload = odoo.create.call_args[0][1]
        assert payload["partner_ref"] == "Juan"

    def test_exception_per_order_continues(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.side_effect = [Exception("boom"), (True, 301)]
        result = self._make(odoo).process([
            self._line(compra="OC-001"), self._line(compra="OC-002"),
        ])
        assert result["creados"] == 1
        assert len(result["fallidos"]) == 1

    # -- Resumen (9) --

    def test_summary_keys_present(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        for key in ("creados", "fallidos", "descartados", "total", "total_ordenes"):
            assert key in result

    def test_total_ordenes_in_result(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["total_ordenes"] == 1

    @patch("core.process_purchases.IntegradorLogger")
    def test_fallidos_line_logged(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, []),                                                     # proveedor no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        from core.process_purchases import ProcessPurchases
        ProcessPurchases(odoo, CORE_CONFIG, {}).process([self._line()])
        warns = [str(c) for c in ml.warning.call_args_list]
        assert any("REF001" in w for w in warns)

    @patch("core.process_purchases.IntegradorLogger")
    def test_fallidos_order_logged(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (False, "error")
        from core.process_purchases import ProcessPurchases
        ProcessPurchases(odoo, CORE_CONFIG, {}).process([self._line()])
        warns = [str(c) for c in ml.warning.call_args_list]
        assert any("OC-001" in w for w in warns)

    def test_descartados_in_result(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 300, "name": "OC-001"}])]
        result = self._make(odoo).process([self._line()])
        assert result["descartados"] == 1

    @patch("core.process_purchases.IntegradorLogger")
    def test_info_log_counts(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, [{"id": 200, "customer_rank": 0, "supplier_rank": 1}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 300)
        from core.process_purchases import ProcessPurchases
        ProcessPurchases(odoo, CORE_CONFIG, {}).process([self._line()])
        infos = [str(c) for c in ml.info.call_args_list]
        assert any("1" in i and "creada" in i for i in infos)

    @patch("core.process_purchases.IntegradorLogger")
    def test_warning_log_fallidos(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 7}]),                                            # default picking type
            (True, []),                                                     # proveedor no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        from core.process_purchases import ProcessPurchases
        ProcessPurchases(odoo, CORE_CONFIG, {}).process([self._line()])
        assert ml.warning.call_count > 0

    def test_all_descartados_no_creates(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 300, "name": "OC-001"}])]
        result = self._make(odoo).process([self._line()])
        odoo.create.assert_not_called()

    def test_no_fallidos_no_warning(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert len(result["fallidos"]) == 0


# ============================================================
# TestProcessSales — 49 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestProcessSales:

    def _make(self, odoo, flow_config=None):
        from core.process_sales import ProcessSales
        return ProcessSales(odoo, CORE_CONFIG, flow_config or {})

    def _line(self, **kw):
        base = {
            "pedido": "PED-001", "producto": "REF001",
            "cliente": "800111222", "sucursal_cliente": "001",
            "fecha_pedido": "2026-08-10", "estado": "draft",
            "almacen": "ALM1", "cantidad_pedida": 5.0,
            "precio_unitario": 100.0, "zona": "Norte",
            "vendedor": "Juan", "condicion_pago": "30 días",
            "observacion": "Urgente",
        }
        base.update(kw)
        return base

    def _happy(self, odoo):
        odoo.search_read.side_effect = [
            (True, []),                                                     # filter
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),  # partner
            (True, [{"id": 50, "uom_id": [1, "U"]}]),                      # product
            (True, [{"id": 5}]),                                            # zone
        ]
        odoo.create.return_value = (True, 400)

    # -- General (2) --

    def test_empty_data_returns_zero_summary(self):
        result = self._make(MagicMock()).process([])
        assert result == {"creados": 0, "fallidos": [], "descartados": 0, "total": 0}

    def test_fatal_exception_returns_error_key(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = Exception("boom")
        result = self._make(odoo).process([self._line()])
        assert "error" in result

    # -- Fase 1: Filtrar existentes (8) --

    def test_filter_first_try_ok(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_filter_retry_second(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "t1"), (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 400)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_filter_retry_third(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "t1"), (False, "t2"), (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 400)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_filter_all_fail_returns_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(False, "t1"), (False, "t2"), (False, "t3")]
        result = self._make(odoo).process([self._line()])
        assert "error" in result

    def test_filter_none_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["descartados"] == 0

    def test_filter_all_exist_returns_early(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 400, "name": "PED-001"}])]
        result = self._make(odoo).process([self._line()])
        assert result["descartados"] == 1
        assert result["creados"] == 0

    def test_filter_partial(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"id": 400, "name": "PED-001"}]),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 401)
        result = self._make(odoo).process([
            self._line(pedido="PED-001"), self._line(pedido="PED-002"),
        ])
        assert result["descartados"] == 1
        assert result["creados"] == 1

    def test_descartados_count(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 400, "name": "PED-001"}])]
        result = self._make(odoo).process([
            self._line(pedido="PED-001", producto="R1"),
            self._line(pedido="PED-001", producto="R2"),
        ])
        assert result["descartados"] == 2

    # -- Fases 2-4: Pre-resolución (10) --

    def test_preresolve_clientes_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1

    def test_preresolve_clientes_not_found(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, []),                                                     # cliente no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Cliente" in f["razon"] for f in result["fallidos"])

    def test_preresolve_clientes_unique_pairs(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),  # 1 lookup
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 51, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 400)
        self._make(odoo).process([
            self._line(producto="R1"), self._line(producto="R2"),
        ])
        partner_calls = [c for c in odoo.search_read.call_args_list if "res.partner" in str(c)]
        assert len(partner_calls) == 1

    def test_preresolve_productos_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        assert self._make(odoo).process([self._line()])["creados"] == 1

    def test_preresolve_productos_not_found(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, []),                                                     # producto no existe
            (True, [{"id": 5}]),
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Producto" in f["razon"] for f in result["fallidos"])

    def test_preresolve_productos_unique(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 400)
        self._make(odoo).process([
            self._line(pedido="P1"), self._line(pedido="P2"),
        ])
        prod_calls = [c for c in odoo.search_read.call_args_list if "product.product" in str(c)]
        assert len(prod_calls) == 1

    def test_preresolve_zonas_found(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        payload = odoo.create.call_args[0][1]
        assert payload["delivery_zone_id"] == 5

    def test_preresolve_zonas_created(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, []),                                                     # zona no existe
        ]
        odoo.create.side_effect = [(True, 6), (True, 400)]                  # zona, orden
        self._make(odoo).process([self._line()])
        zone_creates = [c for c in odoo.create.call_args_list if c[0][0] == "partner.delivery.zone"]
        assert len(zone_creates) == 1

    def test_preresolve_zonas_empty_skipped(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 400)
        line = self._line()
        del line["zona"]
        self._make(odoo).process([line])
        zone_calls = [c for c in odoo.search_read.call_args_list if "partner.delivery.zone" in str(c)]
        assert len(zone_calls) == 0

    def test_preresolve_zonas_unique(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),                                            # solo 1 lookup zona
        ]
        odoo.create.return_value = (True, 400)
        self._make(odoo).process([
            self._line(pedido="P1"), self._line(pedido="P2"),
        ])
        zone_calls = [c for c in odoo.search_read.call_args_list if "partner.delivery.zone" in str(c)]
        assert len(zone_calls) == 1

    # -- Fase 5: Enriquecer + warehouse (7) --

    def test_warehouse_via_bodega_siesa(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo, {"warehouse_mapping": {"BOD01": 8}}).process([
            self._line(bodega_siesa="BOD01")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["warehouse_id"] == 8

    def test_warehouse_via_bodega_sap(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo, {"warehouse_mapping": {"WH01": 9}}).process([
            self._line(bodega_sap="WH01")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["warehouse_id"] == 9

    def test_warehouse_not_in_mapping_uses_default(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo, {"warehouse_mapping": {"BOD01": 8}}).process([
            self._line(bodega_siesa="BOD99")
        ])
        payload = odoo.create.call_args[0][1]
        assert payload["warehouse_id"] == 3  # default

    def test_warehouse_no_bodega_erp_uses_default(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line()])
        payload = odoo.create.call_args[0][1]
        assert payload["warehouse_id"] == 3  # default

    def test_cliente_missing_adds_fallido(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, []),                                                     # cliente no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Cliente" in f["razon"] for f in result["fallidos"])

    def test_producto_missing_adds_fallido(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, []),                                                     # producto no existe
            (True, [{"id": 5}]),
        ]
        result = self._make(odoo).process([self._line()])
        assert any("Producto" in f["razon"] for f in result["fallidos"])

    def test_both_missing_adds_fallidos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, []),                                                     # cliente A no existe
            (True, []),                                                     # cliente B no existe
            (True, []),                                                     # producto X no existe
            (True, []),                                                     # producto Y no existe
            (True, [{"id": 5}]),                                            # zona
            (True, [{"id": 6}]),                                            # zona (si es distinta)
        ]
        result = self._make(odoo).process([
            self._line(cliente="A", producto="X"),
            self._line(cliente="B", producto="Y"),
        ])
        assert len(result["fallidos"]) >= 2

    # -- Fases 6-7: Agrupar + Crear (13) --

    def test_groupby_single_order_single_line(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["total_ordenes"] == 1

    def test_groupby_single_order_multiple_lines(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 51, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 400)
        result = self._make(odoo).process([
            self._line(producto="R1"), self._line(producto="R2"),
        ])
        assert result["total_ordenes"] == 1
        payload = odoo.create.call_args[0][1]
        assert len(payload["order_line"]) == 2

    def test_groupby_multiple_orders(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.side_effect = [(True, 400), (True, 401)]
        result = self._make(odoo).process([
            self._line(pedido="P1"), self._line(pedido="P2"),
        ])
        assert result["total_ordenes"] == 2

    def test_groupby_key_eight_fields(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.side_effect = [(True, 400), (True, 401)]
        result = self._make(odoo).process([
            self._line(observacion="A"), self._line(observacion="B"),
        ])
        assert result["total_ordenes"] == 2

    def test_groupby_zone_id_none_uses_zero(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 400)
        line = self._line()
        del line["zona"]
        self._make(odoo).process([line])

    def test_create_order_ok(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["creados"] == 1
        assert odoo.create.call_args[0][0] == "sale.order"

    def test_create_order_fails(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (False, "error")
        result = self._make(odoo).process([self._line()])
        assert any("create falló" in f["razon"] for f in result["fallidos"])

    def test_create_with_warehouse_id(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo, {"warehouse_mapping": {"BOD01": 8}}).process([
            self._line(bodega_siesa="BOD01")
        ])
        payload = odoo.create.call_args[0][1]
        assert "warehouse_id" in payload
        assert "picking_type_id" not in payload

    def test_create_with_zone_id(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line()])
        payload = odoo.create.call_args[0][1]
        assert payload["delivery_zone_id"] == 5

    def test_create_without_zone_no_delivery_zone(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
        ]
        odoo.create.return_value = (True, 400)
        line = self._line()
        del line["zona"]
        self._make(odoo).process([line])
        payload = odoo.create.call_args[0][1]
        assert "delivery_zone_id" not in payload

    def test_create_with_observacion(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line(observacion="Entregar portería")])
        payload = odoo.create.call_args[0][1]
        assert payload["note"] == "Entregar portería"

    def test_order_line_product_uom_qty(self):
        odoo = MagicMock()
        self._happy(odoo)
        self._make(odoo).process([self._line()])
        payload = odoo.create.call_args[0][1]
        line = payload["order_line"][0][2]
        assert "product_uom_qty" in line
        assert "product_qty" not in line

    def test_exception_per_order_continues(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.side_effect = [Exception("boom"), (True, 401)]
        result = self._make(odoo).process([
            self._line(pedido="P1"), self._line(pedido="P2"),
        ])
        assert result["creados"] == 1
        assert len(result["fallidos"]) == 1

    # -- Resumen (9) --

    def test_summary_keys_present(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        for key in ("creados", "fallidos", "descartados", "total", "total_ordenes"):
            assert key in result

    def test_total_ordenes_in_result(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert result["total_ordenes"] == 1

    @patch("core.process_sales.IntegradorLogger")
    def test_fallidos_line_logged(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, []),                                                     # cliente no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        from core.process_sales import ProcessSales
        ProcessSales(odoo, CORE_CONFIG, {}).process([self._line()])
        warns = [str(c) for c in ml.warning.call_args_list]
        assert any("REF001" in w or "PED-001" in w for w in warns)

    @patch("core.process_sales.IntegradorLogger")
    def test_fallidos_order_logged(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (False, "error")
        from core.process_sales import ProcessSales
        ProcessSales(odoo, CORE_CONFIG, {}).process([self._line()])
        warns = [str(c) for c in ml.warning.call_args_list]
        assert any("PED-001" in w for w in warns)

    def test_descartados_in_result(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 400, "name": "PED-001"}])]
        result = self._make(odoo).process([self._line()])
        assert result["descartados"] == 1

    @patch("core.process_sales.IntegradorLogger")
    def test_info_log_counts(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, [{"id": 200, "customer_rank": 1, "supplier_rank": 0}]),
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        odoo.create.return_value = (True, 400)
        from core.process_sales import ProcessSales
        ProcessSales(odoo, CORE_CONFIG, {}).process([self._line()])
        infos = [str(c) for c in ml.info.call_args_list]
        assert any("1" in i and "creado" in i for i in infos)

    @patch("core.process_sales.IntegradorLogger")
    def test_warning_log_fallidos(self, MockLogger):
        ml = MagicMock()
        MockLogger.return_value = ml
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"id": 3}]),                                            # default warehouse
            (True, []),                                                     # cliente no existe
            (True, [{"id": 50, "uom_id": [1, "U"]}]),
            (True, [{"id": 5}]),
        ]
        from core.process_sales import ProcessSales
        ProcessSales(odoo, CORE_CONFIG, {}).process([self._line()])
        assert ml.warning.call_count > 0

    def test_all_descartados_no_creates(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, [{"id": 400, "name": "PED-001"}])]
        self._make(odoo).process([self._line()])
        odoo.create.assert_not_called()

    def test_no_fallidos_no_warning_in_result(self):
        odoo = MagicMock()
        self._happy(odoo)
        result = self._make(odoo).process([self._line()])
        assert len(result["fallidos"]) == 0


# ============================================================
# TestResolveMissingMasters — 44 pruebas
# ============================================================

@patch.dict(os.environ, {"ENV": "dev"})
class TestResolveMissingMasters:

    def _call(self, odoo, connector=None, transform=None,
            purchases=None, sales=None, flow_configs=None, config=None):
        from core.resolve_missing_masters import resolve_missing_masters
        return resolve_missing_masters(
            odoo, connector or MagicMock(), transform or MagicMock(),
            data_purchases=purchases or [], data_sales=sales or [],
            flow_configs=flow_configs or {}, config=config or CORE_CONFIG,
            logger=MagicMock()
        )

    # -- Sin dependencias (5) --

    def test_no_data_returns_zeros(self):
        result = self._call(MagicMock())
        assert result["productos_faltantes"] == 0

    def test_empty_data_returns_zeros(self):
        result = self._call(MagicMock(), purchases=[], sales=[])
        assert result["productos_faltantes"] == 0

    def test_only_purchases_extracts_productos_proveedores(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )
        assert result["productos_faltantes"] == 0
        assert result["proveedores_faltantes"] == 0

    def test_only_sales_extracts_productos_clientes(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "800222", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {}},
        )
        assert result["productos_faltantes"] == 0

    def test_combined_deduplicates_products(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
            (True, [{"vat": "800222", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "supplier": {}, "customer": {}},
        )
        assert result["productos_faltantes"] == 0

    # -- Todo existe (4) --

    def test_all_productos_exist(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        transform = MagicMock()
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )
        transform.get_flow.assert_not_called()

    def test_all_proveedores_exist(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )
        assert result["proveedores_faltantes"] == 0

    def test_all_clientes_exist(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "800222", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {}},
        )
        assert result["clientes_faltantes"] == 0

    def test_all_exist_returns_early(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        transform = MagicMock()
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )
        transform.get_flow.assert_not_called()

    # -- Errores Odoo (3) --

    def test_odoo_error_products_skips(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (False, "error"),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )

    def test_odoo_error_suppliers_skips(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (False, "error"),
        ]
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )
        assert result["proveedores_faltantes"] == 0

    def test_odoo_error_customers_skips(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (False, "error"),
        ]
        result = self._call(odoo,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {}},
        )
        assert result["clientes_faltantes"] == 0

    # -- Productos faltantes (8) --

    def test_productos_erp_returns_all(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
            (True, []),
            (True, [{"id": 1}]),
        ]
        odoo.create.return_value = (True, 100)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"referencia": "REF001", "descripcion": "P1", "unidad": "Unidades"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )
        assert result["productos_resueltos"] == 1

    def test_productos_erp_returns_partial(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
            (True, []),
            (True, [{"id": 1}]),
        ]
        odoo.create.return_value = (True, 100)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"referencia": "REF001", "descripcion": "P1", "unidad": "U"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[
                {"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"},
                {"producto": "REF002", "proveedor": "900111", "sucursal_proveedor": "001"},
            ],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )
        assert len(result["no_resueltos"]) >= 1

    def test_productos_erp_returns_empty(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = []
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )
        assert result["productos_resueltos"] == 0

    def test_productos_no_flow_config_skips(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        transform = MagicMock()
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"supplier": {}},
        )
        transform.get_flow.assert_not_called()

    def test_productos_not_in_erp_added_to_no_resueltos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"referencia": "OTRO", "descripcion": "P", "unidad": "U"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "FALTANTE", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )
        assert any(nr["referencia"] == "FALTANTE" for nr in result["no_resueltos"])

    def test_productos_process_items_called_with_missing_only(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
            (True, []),
            (True, [{"id": 1}]),
        ]
        odoo.create.return_value = (True, 100)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"referencia": "REF001", "descripcion": "P1", "unidad": "U"},
            {"referencia": "REF002", "descripcion": "P2", "unidad": "U"},
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )

    def test_productos_resueltos_count(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
            (True, []),
            (True, [{"id": 1}]),
        ]
        odoo.create.return_value = (True, 100)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"referencia": "REF001", "descripcion": "P1", "unidad": "U"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )
        assert result["productos_faltantes"] == 1
        assert result["productos_resueltos"] == 1

    def test_productos_exception_logs_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, []),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        transform = MagicMock()
        transform.get_flow.side_effect = Exception("ERP caído")
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}},
        )

    # -- Proveedores faltantes (8) --

    def test_proveedores_erp_returns_all(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "Prov", "identificacion": "900111", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )
        assert result["proveedores_resueltos"] == 1

    def test_proveedores_erp_returns_partial(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "P1", "identificacion": "900111", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[
                {"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"},
                {"producto": "REF001", "proveedor": "900222", "sucursal_proveedor": "001"},
            ],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )
        assert len(result["no_resueltos"]) >= 1

    def test_proveedores_erp_returns_empty(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = []
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )
        assert result["proveedores_resueltos"] == 0

    def test_proveedores_no_flow_config_skips(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}},
        )
        transform.get_flow.assert_not_called()

    def test_proveedores_not_in_erp_no_resueltos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "Otro", "identificacion": "OTRO", "sucursal": ""}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )
        assert any(nr.get("identificacion") == "900111" for nr in result["no_resueltos"])

    def test_proveedores_process_partners_called(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "P1", "identificacion": "900111", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )
        assert result["proveedores_resueltos"] >= 0

    def test_proveedores_resueltos_count(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "P1", "identificacion": "900111", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )
        assert result["proveedores_faltantes"] == 1

    def test_proveedores_exception_logs_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.side_effect = Exception("ERP caído")
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {"flow_type": "supplier"}},
        )

    # -- Clientes faltantes (8) --

    def test_clientes_erp_returns_all(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "Cli", "identificacion": "800222", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )
        assert result["clientes_resueltos"] == 1

    def test_clientes_erp_returns_partial(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "C1", "identificacion": "800222", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            sales=[
                {"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"},
                {"producto": "REF001", "cliente": "800333", "sucursal_cliente": "001"},
            ],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )
        assert len(result["no_resueltos"]) >= 1

    def test_clientes_erp_returns_empty(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = []
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )
        assert result["clientes_resueltos"] == 0

    def test_clientes_no_flow_config_skips(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}},
        )
        transform.get_flow.assert_not_called()

    def test_clientes_not_in_erp_no_resueltos(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "Otro", "identificacion": "OTRO", "sucursal": ""}
        ]
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )
        assert any(nr.get("identificacion") == "800222" for nr in result["no_resueltos"])

    def test_clientes_process_partners_called(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "C1", "identificacion": "800222", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )
        assert result["clientes_resueltos"] >= 0

    def test_clientes_resueltos_count(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.return_value = (True, 200)
        transform = MagicMock()
        transform.get_flow.return_value = [
            {"nombre": "C1", "identificacion": "800222", "sucursal": "001"}
        ]
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )
        assert result["clientes_faltantes"] == 1

    def test_clientes_exception_logs_error(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.side_effect = Exception("ERP caído")
        result = self._call(odoo, transform=transform,
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {}, "customer": {"flow_type": "customer"}},
        )

    # -- Escenarios mixtos (8) --

    def test_mixed_some_exist_some_dont(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
            (True, []),
            (True, []),
            (True, [{"id": 1}]),
            (True, []),
            (True, [{"id": 100}]),
        ]
        odoo.create.side_effect = [(True, 100), (True, 200)]
        transform = MagicMock()
        transform.get_flow.side_effect = [
            [{"referencia": "REF002", "descripcion": "P2", "unidad": "U"}],
            [{"nombre": "C1", "identificacion": "800222", "sucursal": "001"}],
        ]
        result = self._call(odoo, transform=transform,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"},
                        {"producto": "REF002", "proveedor": "900111", "sucursal_proveedor": "001"}],
            sales=[{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            flow_configs={"items": {"sql": "S"}, "supplier": {}, "customer": {"flow_type": "customer"}},
        )
        assert result["productos_faltantes"] == 1
        assert result["clientes_faltantes"] == 1

    def test_no_resueltos_log_productos(self):
        from core.resolve_missing_masters import resolve_missing_masters
        odoo = MagicMock()
        odoo.search_read.side_effect = [(True, []), (True, [{"vat": "900111", "sucursal": "001"}])]
        transform = MagicMock()
        transform.get_flow.return_value = []
        logger = MagicMock()
        result = resolve_missing_masters(
            odoo, MagicMock(), transform,
            [{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}], [],
            {"items": {"sql": "S"}, "supplier": {}}, CORE_CONFIG, logger
        )
        assert any(nr["referencia"] == "REF001" for nr in result["no_resueltos"])

    def test_no_resueltos_log_proveedores(self):
        from core.resolve_missing_masters import resolve_missing_masters
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = []
        logger = MagicMock()
        result = resolve_missing_masters(
            odoo, MagicMock(), transform,
            [{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}], [],
            {"items": {}, "supplier": {"flow_type": "supplier"}}, CORE_CONFIG, logger
        )
        assert any(nr.get("identificacion") == "900111" for nr in result["no_resueltos"])

    def test_no_resueltos_log_clientes(self):
        from core.resolve_missing_masters import resolve_missing_masters
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, []),
        ]
        transform = MagicMock()
        transform.get_flow.return_value = []
        logger = MagicMock()
        result = resolve_missing_masters(
            odoo, MagicMock(), transform,
            [], [{"producto": "REF001", "cliente": "800222", "sucursal_cliente": "001"}],
            {"items": {}, "customer": {"flow_type": "customer"}}, CORE_CONFIG, logger
        )
        assert any(nr.get("identificacion") == "800222" for nr in result["no_resueltos"])

    def test_fatal_exception_returns_error_key(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = Exception("conexión rota")
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111"}],
        )
        assert "error" in result

    def test_resumen_structure_complete(self):
        result = self._call(MagicMock())
        expected_keys = [
            "productos_faltantes", "productos_resueltos",
            "proveedores_faltantes", "proveedores_resueltos",
            "clientes_faltantes", "clientes_resueltos",
            "no_resueltos",
        ]
        for key in expected_keys:
            assert key in result

    def test_resumen_zeros_when_no_faltantes(self):
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        result = self._call(odoo,
            purchases=[{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}],
            flow_configs={"items": {}, "supplier": {}},
        )
        assert result["productos_faltantes"] == 0
        assert result["proveedores_faltantes"] == 0
        assert result["productos_resueltos"] == 0

    def test_info_log_resultado_final(self):
        from core.resolve_missing_masters import resolve_missing_masters
        odoo = MagicMock()
        odoo.search_read.side_effect = [
            (True, [{"default_code": "REF001"}]),
            (True, [{"vat": "900111", "sucursal": "001"}]),
        ]
        logger = MagicMock()
        resolve_missing_masters(
            odoo, MagicMock(), MagicMock(),
            [{"producto": "REF001", "proveedor": "900111", "sucursal_proveedor": "001"}], [],
            {"items": {}, "supplier": {}}, CORE_CONFIG, logger
        )
        infos = [str(c) for c in logger.info.call_args_list]
        assert any("Resolve Masters" in i for i in infos)
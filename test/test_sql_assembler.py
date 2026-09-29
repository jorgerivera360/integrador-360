import os
import unittest
from unittest.mock import MagicMock, patch

with patch.dict(os.environ, {"ENV": "dev"}):
    from api.utils.sql_assembler import assemble_sql, assemble_from_flow_config, _resolve_variables, _extract_base_parts


class TestResolveVariables(unittest.TestCase):

    def test_reemplaza_variable_simple(self):
        result = _resolve_variables(
            "f120_id_cia = {compania}",
            [{"name": "compania", "type": "text", "default": "1"}],
            {"compania": "5"}
        )
        self.assertEqual(result, "f120_id_cia = 5")

    def test_usa_default_si_no_hay_valor(self):
        result = _resolve_variables(
            "DATEADD(day, -{dias}, GETDATE())",
            [{"name": "dias", "type": "number", "default": "1"}],
            {}
        )
        self.assertEqual(result, "DATEADD(day, -1, GETDATE())")

    def test_tipo_list_genera_comillas(self):
        result = _resolve_variables(
            'TRIM(f470_id_motivo) IN ({motivos})',
            [{"name": "motivos", "type": "list", "default": ""}],
            {"motivos": "04, 01, 91"}
        )
        self.assertEqual(result, 'TRIM(f470_id_motivo) IN ("04", "01", "91")')

    def test_sin_variables_retorna_original(self):
        result = _resolve_variables("SELECT 1", [], {})
        self.assertEqual(result, "SELECT 1")

    def test_multiples_variables(self):
        result = _resolve_variables(
            "{campo} = {valor}",
            [
                {"name": "campo", "type": "text", "default": ""},
                {"name": "valor", "type": "text", "default": ""},
            ],
            {"campo": "f120_id", "valor": "ABC"}
        )
        self.assertEqual(result, "f120_id = ABC")


class TestExtractBaseParts(unittest.TestCase):

    def test_extrae_set_prefix(self):
        sql = "SET QUOTED_IDENTIFIER OFF;\nSELECT col1\nFROM tabla1"
        parts = _extract_base_parts(sql)
        self.assertIn("SET QUOTED_IDENTIFIER OFF;", parts["prefix"])
        self.assertIn("SELECT", parts["select"])
        self.assertIn("FROM tabla1", parts["from"])

    def test_extrae_where(self):
        sql = "SELECT col1\nFROM tabla1\nWHERE col1 = 1"
        parts = _extract_base_parts(sql)
        self.assertEqual(parts["where"], "col1 = 1")

    def test_extrae_group_by(self):
        sql = "SELECT col1, COUNT(*)\nFROM tabla1\nWHERE col1 > 0\nGROUP BY col1"
        parts = _extract_base_parts(sql)
        self.assertEqual(parts["group_by"], "col1")
        self.assertEqual(parts["where"], "col1 > 0")

    def test_sin_where_ni_group_by(self):
        sql = "SELECT col1\nFROM tabla1"
        parts = _extract_base_parts(sql)
        self.assertEqual(parts["where"], "")
        self.assertEqual(parts["group_by"], "")

    def test_sin_from(self):
        sql = "SELECT 1 AS test"
        parts = _extract_base_parts(sql)
        self.assertIn("SELECT 1 AS test", parts["select"])
        self.assertEqual(parts["from"], "")


class TestAssembleSql(unittest.TestCase):

    def setUp(self):
        self.base = {
            "select_fragment": "SET QUOTED_IDENTIFIER OFF;\nSELECT\n    f120_referencia AS referencia,\n    f120_descripcion AS descripcion\nFROM t120_mc_items\nINNER JOIN t121 ON t121.f121_rowid_item = t120.f120_rowid\nWHERE f120_id_cia = 1",
            "variables": [],
            "variables_values": {},
        }

    def test_solo_base_sin_extras(self):
        result = assemble_sql(self.base, [], [])
        self.assertIn("SELECT", result)
        self.assertIn("f120_referencia AS referencia", result)
        self.assertIn("FROM t120_mc_items", result)
        self.assertIn("WHERE f120_id_cia = 1", result)
        self.assertIn("SET QUOTED_IDENTIFIER ON;", result)

    def test_agrega_campo_sin_join(self):
        campo = {
            "select_fragment": '"lot" AS tracking',
            "join_fragment": "",
            "group_by_fragment": "",
            "variables": [],
            "variables_values": {},
        }
        result = assemble_sql(self.base, [campo], [])
        self.assertIn('"lot" AS tracking', result)

    def test_agrega_campo_con_join(self):
        campo = {
            "select_fragment": "t_marca.f106_descripcion AS marca",
            "join_fragment": "LEFT JOIN t106_mc_criterios_items t_marca ON t_marca.f106_rowid = t121.f106_rowid",
            "group_by_fragment": "t_marca.f106_descripcion",
            "variables": [],
            "variables_values": {},
        }
        result = assemble_sql(self.base, [campo], [])
        self.assertIn("t_marca.f106_descripcion AS marca", result)
        self.assertIn("LEFT JOIN t106_mc_criterios_items t_marca", result)
        self.assertIn("GROUP BY", result)
        self.assertIn("t_marca.f106_descripcion", result)

    def test_agrega_filtro(self):
        filtro = {
            "where_fragment": "f120_fecha >= DATEADD(day, -1, GETDATE())",
            "variables": [],
            "variables_values": {},
        }
        result = assemble_sql(self.base, [], [filtro])
        self.assertIn("f120_id_cia = 1", result)
        self.assertIn("AND f120_fecha >= DATEADD(day, -1, GETDATE())", result)

    def test_campo_con_variable(self):
        campo = {
            "select_fragment": "{valor} AS iva",
            "join_fragment": "",
            "group_by_fragment": "",
            "variables": [{"name": "valor", "type": "number", "default": "0"}],
            "variables_values": {"valor": "19"},
        }
        result = assemble_sql(self.base, [campo], [])
        self.assertIn("19 AS iva", result)

    def test_filtro_con_variable_list(self):
        filtro = {
            "where_fragment": 'f350_id_tipo_docto IN ({tipos})',
            "variables": [{"name": "tipos", "type": "list", "default": ""}],
            "variables_values": {"tipos": "EAC, DVN"},
        }
        result = assemble_sql(self.base, [], [filtro])
        self.assertIn('"EAC", "DVN"', result)

    def test_multiples_campos_y_filtros(self):
        campos = [
            {"select_fragment": "19 AS iva", "join_fragment": "", "group_by_fragment": "", "variables": [], "variables_values": {}},
            {"select_fragment": '"lot" AS tracking', "join_fragment": "", "group_by_fragment": "", "variables": [], "variables_values": {}},
        ]
        filtros = [
            {"where_fragment": "f120_activo = 1", "variables": [], "variables_values": {}},
            {"where_fragment": "f120_tipo = 'A'", "variables": [], "variables_values": {}},
        ]
        result = assemble_sql(self.base, campos, filtros)
        self.assertIn("19 AS iva", result)
        self.assertIn('"lot" AS tracking', result)
        self.assertIn("f120_activo = 1", result)
        self.assertIn("f120_tipo = 'A'", result)

    def test_base_vacia_retorna_vacio(self):
        result = assemble_sql({}, [], [])
        self.assertEqual(result, "")

    def test_base_none_retorna_vacio(self):
        result = assemble_sql(None, [], [])
        self.assertEqual(result, "")

    def test_base_con_group_by_existente(self):
        base = {
            "select_fragment": "SELECT col1, col2\nFROM tabla\nGROUP BY col1, col2",
            "variables": [],
            "variables_values": {},
        }
        campo = {
            "select_fragment": "col3",
            "join_fragment": "",
            "group_by_fragment": "col3",
            "variables": [],
            "variables_values": {},
        }
        result = assemble_sql(base, [campo], [])
        self.assertIn("GROUP BY col1, col2, col3", result)


class TestAssembleFromFlowConfig(unittest.TestCase):

    def test_modo_libre_retorna_sql_directo(self):
        fc = {"sql_mode": "libre", "sql": "SELECT 1"}
        result = assemble_from_flow_config(fc, None)
        self.assertEqual(result, "SELECT 1")

    def test_sin_sql_mode_retorna_sql(self):
        fc = {"sql": "SELECT 1"}
        result = assemble_from_flow_config(fc, None)
        self.assertEqual(result, "SELECT 1")

    def test_modo_visual_sin_base_retorna_vacio(self):
        fc = {"sql_mode": "visual"}
        result = assemble_from_flow_config(fc, None)
        self.assertEqual(result, "")

    def test_modo_visual_consulta_bd(self):
        fc = {
            "sql_mode": "visual",
            "sql_base_id": 1,
            "sql_base_variables": {},
            "sql_campos": [{"block_id": 2, "variables": {"valor": "19"}}],
            "sql_filtros": [{"block_id": 3, "variables": {"dias": "1"}}],
        }

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1, "block_type": "base", "is_active": True,
                "select_fragment": "SELECT col1\nFROM tabla",
                "join_fragment": "", "group_by_fragment": "", "where_fragment": "",
                "variables": [],
            },
            {
                "id": 2, "block_type": "campo", "is_active": True,
                "select_fragment": "{valor} AS iva",
                "join_fragment": "", "group_by_fragment": "", "where_fragment": "",
                "variables": [{"name": "valor", "type": "number", "default": "0"}],
            },
            {
                "id": 3, "block_type": "filtro", "is_active": True,
                "select_fragment": "", "join_fragment": "", "group_by_fragment": "",
                "where_fragment": "fecha >= DATEADD(day, -{dias}, GETDATE())",
                "variables": [{"name": "dias", "type": "number", "default": "1"}],
            },
        ]

        result = assemble_from_flow_config(fc, mock_cursor)

        mock_cursor.execute.assert_called_once()
        self.assertIn("col1", result)
        self.assertIn("19 AS iva", result)
        self.assertIn("DATEADD(day, -1, GETDATE())", result)

    def test_modo_visual_base_inactiva_retorna_vacio(self):
        fc = {"sql_mode": "visual", "sql_base_id": 99, "sql_campos": [], "sql_filtros": []}

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        result = assemble_from_flow_config(fc, mock_cursor)
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()

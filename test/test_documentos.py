"""
test_documentos.py — Pruebas de transform/utils/documentos.py

Cubre la personalizacion por tipo de documento: clasificacion de filas,
evaluacion de condiciones, filtros y valores fijos por documento.

Fase: 3 — Transform Layer
"""
from unittest.mock import MagicMock

from transform.utils.documentos import (
    OPERADORES,
    evaluar_condicion,
    clasificar_documento,
    preparar_documentos,
    procesar_fila,
)


# -- Datos de apoyo

DOC_CPV = {
    "codigo": "CPV",
    "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "CPV"},
    "filtros": [{"campo": "bodega_siesa", "operador": "=", "valor": "00550"}],
    "hardcodes": {},
}

DOC_CDC = {
    "codigo": "CDC",
    "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "CDC"},
    "filtros": [],
    "hardcodes": {"estado": "sale"},
}


def fila(pedido="7-CPV-1", bodega="00550", estado="draft"):
    return {"pedido": pedido, "bodega_siesa": bodega, "estado": estado}


# -- evaluar_condicion — operadores

class TestEvaluarCondicionOperadores:

    def test_igual_verdadero(self):
        cond = {"campo": "estado", "operador": "=", "valor": "draft"}
        assert evaluar_condicion({"estado": "draft"}, cond) is True

    def test_igual_falso(self):
        cond = {"campo": "estado", "operador": "=", "valor": "draft"}
        assert evaluar_condicion({"estado": "sale"}, cond) is False

    def test_distinto_verdadero(self):
        cond = {"campo": "estado", "operador": "!=", "valor": "draft"}
        assert evaluar_condicion({"estado": "sale"}, cond) is True

    def test_distinto_falso(self):
        cond = {"campo": "estado", "operador": "!=", "valor": "draft"}
        assert evaluar_condicion({"estado": "draft"}, cond) is False

    def test_contiene_verdadero(self):
        cond = {"campo": "pedido", "operador": "contiene", "valor": "CPV"}
        assert evaluar_condicion({"pedido": "7-CPV-123"}, cond) is True

    def test_contiene_falso(self):
        cond = {"campo": "pedido", "operador": "contiene", "valor": "CPV"}
        assert evaluar_condicion({"pedido": "7-CDC-123"}, cond) is False

    def test_empieza_con_verdadero(self):
        cond = {"campo": "compra", "operador": "empieza_con", "valor": "OCNAL"}
        assert evaluar_condicion({"compra": "OCNAL-3565"}, cond) is True

    def test_empieza_con_falso_si_esta_en_el_medio(self):
        cond = {"campo": "compra", "operador": "empieza_con", "valor": "OCNAL"}
        assert evaluar_condicion({"compra": "X-OCNAL-3565"}, cond) is False

    def test_in_verdadero(self):
        cond = {"campo": "bodega", "operador": "in", "valor": ["PPAL", "MP"]}
        assert evaluar_condicion({"bodega": "PPAL"}, cond) is True

    def test_in_falso(self):
        cond = {"campo": "bodega", "operador": "in", "valor": ["PPAL", "MP"]}
        assert evaluar_condicion({"bodega": "IHIGIENE"}, cond) is False

    def test_in_con_valor_que_no_es_lista_es_falso(self):
        cond = {"campo": "bodega", "operador": "in", "valor": "PPAL"}
        assert evaluar_condicion({"bodega": "PPAL"}, cond) is False

    def test_in_con_valor_que_no_es_lista_loguea_warning(self):
        logger = MagicMock()
        cond = {"campo": "bodega", "operador": "in", "valor": "PPAL"}
        evaluar_condicion({"bodega": "PPAL"}, cond, logger=logger)
        assert logger.warning.called

    def test_operador_por_defecto_es_igual(self):
        # El backend asume "=" cuando falta el operador: es el default estricto.
        # El front siempre lo envia explicito, asi que no deberia darse en la practica.
        cond = {"campo": "pedido", "valor": "CPV"}
        assert evaluar_condicion({"pedido": "7-CPV-1"}, cond) is False
        assert evaluar_condicion({"pedido": "CPV"}, cond) is True


# -- evaluar_condicion — comparacion y bordes

class TestEvaluarCondicionBordes:

    def test_compara_como_string_conserva_ceros_a_la_izquierda(self):
        cond = {"campo": "bodega_siesa", "operador": "=", "valor": "00550"}
        assert evaluar_condicion({"bodega_siesa": "00550"}, cond) is True

    def test_no_confunde_bodega_con_numero_equivalente(self):
        cond = {"campo": "bodega_siesa", "operador": "=", "valor": "00550"}
        assert evaluar_condicion({"bodega_siesa": "550"}, cond) is False

    def test_aplica_strip_al_valor_de_la_fila(self):
        cond = {"campo": "estado", "operador": "=", "valor": "draft"}
        assert evaluar_condicion({"estado": "  draft  "}, cond) is True

    def test_convierte_numeros_a_string(self):
        cond = {"campo": "almacen", "operador": "=", "valor": "1"}
        assert evaluar_condicion({"almacen": 1}, cond) is True

    def test_campo_ausente_en_la_fila_es_falso(self):
        cond = {"campo": "no_existe", "operador": "=", "valor": "x"}
        assert evaluar_condicion({"estado": "draft"}, cond) is False

    def test_campo_none_se_trata_como_vacio(self):
        cond = {"campo": "estado", "operador": "=", "valor": ""}
        assert evaluar_condicion({"estado": None}, cond) is True

    def test_es_sensible_a_mayusculas(self):
        cond = {"campo": "pedido", "operador": "contiene", "valor": "cpv"}
        assert evaluar_condicion({"pedido": "7-CPV-1"}, cond) is False

    def test_condicion_sin_campo_es_falsa(self):
        assert evaluar_condicion({"estado": "draft"}, {"operador": "=", "valor": "draft"}) is False

    def test_condicion_sin_campo_loguea_warning(self):
        logger = MagicMock()
        evaluar_condicion({"estado": "draft"}, {"operador": "="}, logger=logger)
        assert logger.warning.called

    def test_operador_desconocido_es_falso(self):
        cond = {"campo": "estado", "operador": "mayor_que", "valor": "1"}
        assert evaluar_condicion({"estado": "5"}, cond) is False

    def test_operador_desconocido_loguea_warning(self):
        logger = MagicMock()
        cond = {"campo": "estado", "operador": "mayor_que", "valor": "1"}
        evaluar_condicion({"estado": "5"}, cond, logger=logger)
        assert logger.warning.called

    def test_operadores_expone_los_cinco_soportados(self):
        assert set(OPERADORES) == {"=", "!=", "in", "contiene", "empieza_con"}


# -- clasificar_documento

class TestClasificarDocumento:

    def test_devuelve_el_documento_que_matchea(self):
        doc = clasificar_documento(fila(pedido="7-CDC-9"), [DOC_CPV, DOC_CDC])
        assert doc["codigo"] == "CDC"

    def test_devuelve_none_si_ninguno_matchea(self):
        assert clasificar_documento(fila(pedido="7-CPD-9"), [DOC_CPV, DOC_CDC]) is None

    def test_gana_el_primero_de_la_lista(self):
        generico = {
            "codigo": "GEN",
            "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "7-"},
            "filtros": [], "hardcodes": {},
        }
        doc = clasificar_documento(fila(pedido="7-CPV-1"), [generico, DOC_CPV])
        assert doc["codigo"] == "GEN"

    def test_documento_sin_identificar_por_se_omite(self):
        sin_ident = {"codigo": "X", "filtros": [], "hardcodes": {}}
        doc = clasificar_documento(fila(pedido="7-CPV-1"), [sin_ident, DOC_CPV])
        assert doc["codigo"] == "CPV"

    def test_documento_sin_identificar_por_loguea_warning(self):
        logger = MagicMock()
        clasificar_documento(fila(), [{"codigo": "X"}], logger=logger)
        assert logger.warning.called

    def test_lista_vacia_devuelve_none(self):
        assert clasificar_documento(fila(), []) is None


# -- preparar_documentos

class TestPrepararDocumentos:

    def test_sin_documentos_devuelve_activos_vacio(self):
        activos, _ = preparar_documentos(None)
        assert activos == []

    def test_lista_vacia_devuelve_activos_vacio(self):
        activos, _ = preparar_documentos([])
        assert activos == []

    def test_devuelve_los_documentos_activos(self):
        activos, _ = preparar_documentos([DOC_CPV, DOC_CDC])
        assert len(activos) == 2

    def test_omite_los_inactivos(self):
        inactivo = {**DOC_CPV, "activo": False}
        activos, _ = preparar_documentos([inactivo, DOC_CDC])
        assert len(activos) == 1
        assert activos[0]["codigo"] == "CDC"

    def test_documento_sin_clave_activo_se_considera_activo(self):
        activos, _ = preparar_documentos([DOC_CPV])
        assert len(activos) == 1

    def test_omite_elementos_que_no_son_dict(self):
        activos, _ = preparar_documentos(["no soy un dict", DOC_CPV])
        assert len(activos) == 1

    def test_elemento_invalido_loguea_warning(self):
        logger = MagicMock()
        preparar_documentos([123], logger=logger)
        assert logger.warning.called

    def test_todos_inactivos_loguea_warning(self):
        logger = MagicMock()
        preparar_documentos([{**DOC_CPV, "activo": False}], logger=logger)
        assert logger.warning.called

    def test_stats_arranca_con_un_contador_por_documento(self):
        _, stats = preparar_documentos([DOC_CPV, DOC_CDC])
        assert stats["CPV"] == {"aceptados": 0, "descartados": 0}
        assert stats["CDC"] == {"aceptados": 0, "descartados": 0}

    def test_stats_incluye_el_contador_sin_documento(self):
        _, stats = preparar_documentos([DOC_CPV])
        assert stats["_sin_documento"] == 0

    def test_documento_sin_codigo_usa_indice(self):
        _, stats = preparar_documentos([{"identificar_por": {"campo": "a", "valor": "b"}}])
        assert "#0" in stats


# -- procesar_fila

class TestProcesarFila:

    def test_sin_activos_devuelve_la_fila_intacta(self):
        activos, stats = preparar_documentos(None)
        original = fila()
        assert procesar_fila(dict(original), activos, stats) == original

    def test_fila_sin_documento_pasa_sin_cambios(self):
        activos, stats = preparar_documentos([DOC_CPV, DOC_CDC])
        r = procesar_fila(fila(pedido="7-CPD-9"), activos, stats)
        assert r["estado"] == "draft"

    def test_fila_sin_documento_suma_al_contador(self):
        activos, stats = preparar_documentos([DOC_CPV])
        procesar_fila(fila(pedido="7-CPD-9"), activos, stats)
        assert stats["_sin_documento"] == 1

    def test_fila_que_cumple_el_filtro_pasa(self):
        activos, stats = preparar_documentos([DOC_CPV])
        assert procesar_fila(fila(bodega="00550"), activos, stats) is not None

    def test_fila_que_no_cumple_el_filtro_se_descarta(self):
        activos, stats = preparar_documentos([DOC_CPV])
        assert procesar_fila(fila(bodega="02201"), activos, stats) is None

    def test_descarte_suma_al_contador_del_documento(self):
        activos, stats = preparar_documentos([DOC_CPV])
        procesar_fila(fila(bodega="02201"), activos, stats)
        assert stats["CPV"]["descartados"] == 1
        assert stats["CPV"]["aceptados"] == 0

    def test_aceptada_suma_al_contador_del_documento(self):
        activos, stats = preparar_documentos([DOC_CPV])
        procesar_fila(fila(bodega="00550"), activos, stats)
        assert stats["CPV"]["aceptados"] == 1

    def test_documento_sin_filtros_acepta_todo(self):
        activos, stats = preparar_documentos([DOC_CDC])
        assert procesar_fila(fila(pedido="7-CDC-1", bodega="99999"), activos, stats) is not None

    def test_aplica_los_hardcodes_del_documento(self):
        activos, stats = preparar_documentos([DOC_CDC])
        r = procesar_fila(fila(pedido="7-CDC-1"), activos, stats)
        assert r["estado"] == "sale"

    def test_los_hardcodes_no_afectan_a_otros_documentos(self):
        activos, stats = preparar_documentos([DOC_CPV, DOC_CDC])
        cpv = procesar_fila(fila(pedido="7-CPV-1", bodega="00550"), activos, stats)
        assert cpv["estado"] == "draft"

    def test_hardcode_puede_crear_un_campo_nuevo(self):
        doc = {**DOC_CDC, "hardcodes": {"origen": "documento"}}
        activos, stats = preparar_documentos([doc])
        r = procesar_fila(fila(pedido="7-CDC-1"), activos, stats)
        assert r["origen"] == "documento"

    def test_todos_los_filtros_deben_cumplirse(self):
        doc = {
            "codigo": "X",
            "identificar_por": {"campo": "pedido", "operador": "contiene", "valor": "CPV"},
            "filtros": [
                {"campo": "bodega_siesa", "operador": "=", "valor": "00550"},
                {"campo": "estado", "operador": "=", "valor": "sale"},
            ],
            "hardcodes": {},
        }
        activos, stats = preparar_documentos([doc])
        assert procesar_fila(fila(bodega="00550", estado="draft"), activos, stats) is None

    def test_valida_los_campos_configurados_una_sola_vez(self):
        logger = MagicMock()
        doc = {
            "codigo": "X",
            "identificar_por": {"campo": "campo_que_no_llega", "operador": "=", "valor": "1"},
            "filtros": [], "hardcodes": {},
        }
        activos, stats = preparar_documentos([doc], logger=logger)
        for _ in range(5):
            procesar_fila(fila(), activos, stats, logger=logger)
        avisos = [c for c in logger.warning.call_args_list if "no llegan en el dato" in str(c)]
        assert len(avisos) == 1

    def test_no_avisa_si_todos_los_campos_llegan(self):
        logger = MagicMock()
        activos, stats = preparar_documentos([DOC_CPV], logger=logger)
        procesar_fila(fila(), activos, stats, logger=logger)
        avisos = [c for c in logger.warning.call_args_list if "no llegan en el dato" in str(c)]
        assert avisos == []


# -- Escenario completo

class TestEscenarioCompleto:

    def _correr(self, filas, documentos):
        activos, stats = preparar_documentos(documentos)
        salida = []
        for f in filas:
            r = procesar_fila(dict(f), activos, stats)
            if r is not None:
                salida.append(r)
        return salida, stats

    def _filas(self):
        return [
            fila(pedido="7-CPV-1", bodega="00550"),
            fila(pedido="7-CPV-2", bodega="02201"),
            fila(pedido="7-CDC-3", bodega="02201"),
            fila(pedido="7-CPD-4", bodega="00151"),
        ]

    def test_sin_documentos_pasan_todas_las_filas(self):
        salida, _ = self._correr(self._filas(), None)
        assert len(salida) == 4

    def test_sin_documentos_ninguna_fila_se_modifica(self):
        salida, _ = self._correr(self._filas(), None)
        assert all(f["estado"] == "draft" for f in salida)

    def test_con_documentos_descarta_la_que_no_cumple(self):
        salida, _ = self._correr(self._filas(), [DOC_CPV, DOC_CDC])
        assert len(salida) == 3
        assert "7-CPV-2" not in [f["pedido"] for f in salida]

    def test_con_documentos_aplica_el_hardcode_al_correcto(self):
        salida, _ = self._correr(self._filas(), [DOC_CPV, DOC_CDC])
        estados = {f["pedido"]: f["estado"] for f in salida}
        assert estados["7-CDC-3"] == "sale"
        assert estados["7-CPV-1"] == "draft"

    def test_la_fila_no_declarada_pasa_intacta(self):
        salida, _ = self._correr(self._filas(), [DOC_CPV, DOC_CDC])
        estados = {f["pedido"]: f["estado"] for f in salida}
        assert estados["7-CPD-4"] == "draft"

    def test_stats_refleja_el_resultado_completo(self):
        _, stats = self._correr(self._filas(), [DOC_CPV, DOC_CDC])
        assert stats["CPV"] == {"aceptados": 1, "descartados": 1}
        assert stats["CDC"] == {"aceptados": 1, "descartados": 0}
        assert stats["_sin_documento"] == 1

    def test_no_muta_la_configuracion_de_los_documentos(self):
        docs = [dict(DOC_CPV), dict(DOC_CDC)]
        self._correr(self._filas(), docs)
        assert docs[1]["hardcodes"] == {"estado": "sale"}

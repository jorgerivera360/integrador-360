"""
Sap — Conector SAP Business One
Responsabilidades:
  - Conecta con SAP Service Layer via OData
  - Obtiene y reutiliza SessionId — Singleton
  - Maneja paginación con $skip y odata.nextLink
  - Implementa get() y test_connection()
Hereda: ERPConnector
Fase: 2 — Connection Layer
"""
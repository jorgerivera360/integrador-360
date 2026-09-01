"""
test_api.py — Pruebas de la API FastAPI del integrador-360
Total: 75 pruebas en 10 clases
  - TestHealthCheck: 2
  - TestAuth: 8
  - TestRequireRole: 5
  - TestUsers: 10
  - TestClients: 12
  - TestFlows: 14
  - TestExecutions: 10
  - TestDashboard: 4
  - TestChanges: 4
  - TestTestConnections: 6
Fase: 8 — API FastAPI
"""
import os
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, call
from fastapi.testclient import TestClient
from jose import jwt

# --- Constantes ---

JWT_SECRET = "integrador-360-secret-key-cambiar-en-produccion"
JWT_ALGORITHM = "HS256"

SUPERADMIN_USER = {
    "id": 1, "email": "admin@360software.com.co", "name": "Admin",
    "role": "superadmin", "is_active": True
}
ADMIN_USER = {
    "id": 2, "email": "editor@360software.com.co", "name": "Editor",
    "role": "admin", "is_active": True
}
VIEWER_USER = {
    "id": 3, "email": "viewer@360software.com.co", "name": "Viewer",
    "role": "viewer", "is_active": True
}


def _make_token(user, expired=False):
    """Genera un JWT de prueba."""
    exp = datetime.now(timezone.utc) + (timedelta(hours=-1) if expired else timedelta(hours=24))
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "exp": exp,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _auth_header(user):
    """Retorna dict con header Authorization Bearer."""
    return {"Authorization": f"Bearer {_make_token(user)}"}


def _mock_cursor():
    """Retorna un mock de cursor con encadenamiento."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    return cursor


def _mock_db(cursor):
    """Retorna un mock de conexion BD que produce el cursor."""
    conn = MagicMock()
    conn.cursor.return_value = cursor
    return conn


# --- Fixture de app con mocks globales ---

@pytest.fixture
def app_client():
    """TestClient con get_db y get_current_user mockeados."""
    cursor = _mock_cursor()
    conn = _mock_db(cursor)

    from api.app import app
    from api.dependencies import get_db
    from api.auth import get_current_user

    def override_get_db():
        yield conn

    def override_get_current_user():
        return SUPERADMIN_USER

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client, cursor, conn

    app.dependency_overrides.clear()


@pytest.fixture
def app_with_role():
    """Factory fixture que permite inyectar un usuario con rol especifico."""
    def _factory(user):
        from api.app import app
        from api.dependencies import get_db
        from api.auth import get_current_user

        cursor = _mock_cursor()
        conn = _mock_db(cursor)

        def override_get_db():
            yield conn

        def override_get_current_user():
            return user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        client = TestClient(app)
        return client, cursor, conn

    yield _factory

    from api.app import app
    app.dependency_overrides.clear()


# ===========================================================================
# 1. TestHealthCheck (2)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestHealthCheck:

    def test_health_check_retorna_ok(self, app_client):
        client, cursor, conn = app_client
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "integrador-360-api"

    def test_health_check_no_requiere_auth(self):
        from api.app import app
        from api.dependencies import get_db
        conn = MagicMock()
        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        app.dependency_overrides.clear()


# ===========================================================================
# 2. TestAuth (8)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestAuth:

    @patch("api.routes.auth.verify_google_token")
    def test_login_google_token_valido(self, mock_verify):
        mock_verify.return_value = {"email": "admin@360software.com.co"}

        from api.app import app
        from api.dependencies import get_db

        cursor = _mock_cursor()
        conn = _mock_db(cursor)
        cursor.fetchone.side_effect = [
            {"id": 1, "email": "admin@360software.com.co", "name": "Admin",
              "role": "superadmin", "is_active": True},
        ]

        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        resp = client.post("/auth/login", json={"google_token": "valid_token"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["email"] == "admin@360software.com.co"
        app.dependency_overrides.clear()

    @patch("api.routes.auth.verify_google_token")
    def test_login_google_token_invalido(self, mock_verify):
        from fastapi import HTTPException
        mock_verify.side_effect = HTTPException(status_code=401, detail="Token de Google inválido")

        from api.app import app
        from api.dependencies import get_db
        conn = MagicMock()
        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        resp = client.post("/auth/login", json={"google_token": "bad_token"})
        assert resp.status_code == 401
        app.dependency_overrides.clear()

    @patch("api.routes.auth.verify_google_token")
    def test_login_email_no_360software(self, mock_verify):
        mock_verify.return_value = {"email": "user@gmail.com"}

        from api.app import app
        from api.dependencies import get_db
        conn = MagicMock()
        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        resp = client.post("/auth/login", json={"google_token": "valid_token"})
        assert resp.status_code == 403
        assert "360software" in resp.json()["detail"]
        app.dependency_overrides.clear()

    @patch("api.routes.auth.verify_google_token")
    def test_login_usuario_no_registrado(self, mock_verify):
        mock_verify.return_value = {"email": "nuevo@360software.com.co"}

        from api.app import app
        from api.dependencies import get_db
        cursor = _mock_cursor()
        conn = _mock_db(cursor)
        cursor.fetchone.return_value = None

        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        resp = client.post("/auth/login", json={"google_token": "valid_token"})
        assert resp.status_code == 403
        assert "no registrado" in resp.json()["detail"]
        app.dependency_overrides.clear()

    @patch("api.routes.auth.verify_google_token")
    def test_login_usuario_desactivado(self, mock_verify):
        mock_verify.return_value = {"email": "inactivo@360software.com.co"}

        from api.app import app
        from api.dependencies import get_db
        cursor = _mock_cursor()
        conn = _mock_db(cursor)
        cursor.fetchone.return_value = {
            "id": 5, "email": "inactivo@360software.com.co", "name": "Inactivo",
            "role": "viewer", "is_active": False
        }

        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        resp = client.post("/auth/login", json={"google_token": "valid_token"})
        assert resp.status_code == 403
        assert "desactivado" in resp.json()["detail"].lower()
        app.dependency_overrides.clear()

    @patch("api.routes.auth.verify_google_token")
    def test_login_actualiza_last_login(self, mock_verify):
        mock_verify.return_value = {"email": "admin@360software.com.co"}

        from api.app import app
        from api.dependencies import get_db
        cursor = _mock_cursor()
        conn = _mock_db(cursor)
        cursor.fetchone.return_value = {
            "id": 1, "email": "admin@360software.com.co", "name": "Admin",
            "role": "superadmin", "is_active": True
        }

        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        resp = client.post("/auth/login", json={"google_token": "valid_token"})
        assert resp.status_code == 200
        update_calls = [c for c in cursor.execute.call_args_list if "last_login" in str(c)]
        assert len(update_calls) == 1
        conn.commit.assert_called_once()
        app.dependency_overrides.clear()

    def test_me_retorna_usuario_logueado(self, app_client):
        client, cursor, conn = app_client
        resp = client.get("/auth/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == SUPERADMIN_USER["email"]
        assert body["role"] == "superadmin"

    def test_me_sin_token_retorna_401(self):
        from api.app import app
        app.dependency_overrides.clear()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)


# ===========================================================================
# 3. TestRequireRole (5)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestRequireRole:

    def test_superadmin_accede_a_todo(self, app_with_role):
        client, cursor, conn = app_with_role(SUPERADMIN_USER)
        cursor.fetchall.return_value = []
        resp = client.get("/users/")
        assert resp.status_code == 200

    def test_admin_accede_a_clientes(self, app_with_role):
        client, cursor, conn = app_with_role(ADMIN_USER)
        cursor.fetchall.return_value = []
        resp = client.get("/clients/")
        assert resp.status_code == 200

    def test_viewer_no_puede_crear(self, app_with_role):
        client, cursor, conn = app_with_role(VIEWER_USER)
        resp = client.post("/clients/", json={
            "client_id": "test", "name": "Test", "erp_type": "ws"
        })
        assert resp.status_code == 403

    def test_token_expirado_retorna_401(self):
        from api.app import app
        from api.dependencies import get_db

        cursor = _mock_cursor()
        conn = _mock_db(cursor)
        cursor.fetchone.return_value = SUPERADMIN_USER

        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides.pop(
            __import__("api.auth", fromlist=["get_current_user"]).get_current_user, None
        )

        client = TestClient(app, raise_server_exceptions=False)
        token = _make_token(SUPERADMIN_USER, expired=True)
        resp = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (401, 403)
        app.dependency_overrides.clear()

    def test_token_invalido_retorna_401(self):
        from api.app import app
        from api.dependencies import get_db

        cursor = _mock_cursor()
        conn = _mock_db(cursor)

        def override_get_db():
            yield conn
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides.pop(
            __import__("api.auth", fromlist=["get_current_user"]).get_current_user, None
        )

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/users/", headers={"Authorization": "Bearer token_falso_invalido"})
        assert resp.status_code in (401, 403)
        app.dependency_overrides.clear()


# ===========================================================================
# 4. TestUsers (10)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestUsers:

    def test_get_users_lista_todos(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = [
            {"id": 1, "email": "a@360software.com.co", "name": "A",
              "role": "superadmin", "is_active": True,
              "last_login": None, "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"},
        ]
        resp = client.get("/users/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_users_filtro_activos(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/users/?is_active=true")
        assert resp.status_code == 200
        sql_call = cursor.execute.call_args[0][0]
        assert "is_active" in sql_call

    def test_get_user_por_id(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 1, "email": "a@360software.com.co", "name": "A",
            "role": "superadmin", "is_active": True,
            "last_login": None, "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"
        }
        resp = client.get("/users/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_get_user_no_existe_404(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.get("/users/999")
        assert resp.status_code == 404

    def test_create_user_exitoso(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            None,
            {"id": 10, "email": "nuevo@360software.com.co", "name": "Nuevo",
              "role": "viewer", "is_active": True,
              "last_login": None, "created_at": "2026-08-19T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.post("/users/", json={
            "email": "nuevo@360software.com.co", "name": "Nuevo", "role": "viewer"
        })
        assert resp.status_code == 201
        assert resp.json()["email"] == "nuevo@360software.com.co"

    def test_create_user_email_duplicado(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        resp = client.post("/users/", json={
            "email": "existe@360software.com.co", "name": "Dup", "role": "viewer"
        })
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    def test_create_user_rol_invalido(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.post("/users/", json={
            "email": "nuevo@360software.com.co", "name": "Nuevo", "role": "hacker"
        })
        assert resp.status_code == 400

    def test_update_user_campos_parciales(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 2, "email": "old@360software.com.co", "name": "Old",
              "role": "viewer", "is_active": True},
            {"id": 2, "email": "old@360software.com.co", "name": "Nuevo Nombre",
              "role": "viewer", "is_active": True,
              "last_login": None, "created_at": "2026-01-01T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.put("/users/2", json={"name": "Nuevo Nombre"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Nuevo Nombre"

    def test_update_user_email_duplicado(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 2, "email": "old@360software.com.co", "name": "Old",
              "role": "viewer", "is_active": True},
            {"id": 3},
        ]
        resp = client.put("/users/2", json={"email": "taken@360software.com.co"})
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    def test_delete_user_no_auto_eliminarse(self, app_client):
        client, cursor, conn = app_client
        resp = client.delete(f"/users/{SUPERADMIN_USER['id']}")
        assert resp.status_code == 400


# ===========================================================================
# 5. TestClients (12)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestClients:

    def test_get_clients_lista_todos(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = [
            {"id": 1, "client_id": "fenix", "name": "Fenix", "erp_type": "ws",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"},
        ]
        resp = client.get("/clients/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_clients_filtro_erp_type(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/clients/?erp_type=ws")
        assert resp.status_code == 200
        sql_call = cursor.execute.call_args[0][0]
        assert "erp_type" in sql_call

    def test_get_clients_filtro_is_active(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/clients/?is_active=true")
        assert resp.status_code == 200
        sql_call = cursor.execute.call_args[0][0]
        assert "is_active" in sql_call

    def test_get_clients_filtro_search(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/clients/?search=fen")
        assert resp.status_code == 200
        sql_call = cursor.execute.call_args[0][0]
        assert "ILIKE" in sql_call

    def test_get_client_por_id(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 1, "client_id": "fenix", "name": "Fenix", "erp_type": "ws",
            "is_active": True, "created_by": 1, "updated_by": 1,
            "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"
        }
        resp = client.get("/clients/1")
        assert resp.status_code == 200
        assert resp.json()["client_id"] == "fenix"

    def test_get_client_no_existe_404(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.get("/clients/999")
        assert resp.status_code == 404

    def test_create_client_exitoso(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            None,
            {"id": 5, "client_id": "nuevo_cliente", "name": "Nuevo Cliente", "erp_type": "ws",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-08-19T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.post("/clients/", json={
            "client_id": "nuevo_cliente", "name": "Nuevo Cliente", "erp_type": "ws"
        })
        assert resp.status_code == 201
        assert resp.json()["client_id"] == "nuevo_cliente"

    def test_create_client_id_duplicado(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        resp = client.post("/clients/", json={
            "client_id": "fenix", "name": "Fenix 2", "erp_type": "ws"
        })
        assert resp.status_code == 400
        assert "client_id" in resp.json()["detail"]

    def test_create_client_erp_type_invalido(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.post("/clients/", json={
            "client_id": "test", "name": "Test", "erp_type": "invalido"
        })
        assert resp.status_code == 400
        assert "erp_type" in resp.json()["detail"]

    def test_create_client_llena_created_by(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            None,
            {"id": 5, "client_id": "test", "name": "Test", "erp_type": "ws",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-08-19T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.post("/clients/", json={
            "client_id": "test", "name": "Test", "erp_type": "ws"
        })
        assert resp.status_code == 201
        insert_call = [c for c in cursor.execute.call_args_list if "INSERT" in str(c)][0]
        params = insert_call[0][1]
        assert SUPERADMIN_USER["id"] in params

    def test_update_client_campos_parciales(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 1, "client_id": "fenix", "name": "Fenix", "erp_type": "ws",
              "is_active": True},
            {"id": 1, "client_id": "fenix", "name": "Fenix Updated", "erp_type": "ws",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-01-01T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.put("/clients/1", json={"name": "Fenix Updated"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fenix Updated"

    def test_delete_client_cascade(self, app_client):
        client, cursor, conn = app_client
        # El endpoint hace SELECT * y guarda client_id, name y erp_type en
        # change_history antes de borrar, asi que el mock debe traer esas columnas.
        cursor.fetchone.return_value = {
            "id": 1, "client_id": "fenix", "name": "Fenix", "erp_type": "ws"
        }
        resp = client.delete("/clients/1")
        assert resp.status_code == 204
        delete_calls = [c for c in cursor.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) >= 1
        conn.commit.assert_called_once()

    def test_delete_client_registra_change_history(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 1, "client_id": "fenix", "name": "Fenix", "erp_type": "ws"
        }
        client.delete("/clients/1")
        historial = [c for c in cursor.execute.call_args_list if "change_history" in str(c)]
        assert len(historial) >= 1

    def test_delete_client_guarda_los_valores_previos(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 1, "client_id": "fenix", "name": "Fenix", "erp_type": "ws"
        }
        client.delete("/clients/1")
        historial = [c for c in cursor.execute.call_args_list if "change_history" in str(c)]
        assert "fenix" in str(historial[0])


# ===========================================================================
# 6. TestFlows (14)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestFlows:

    def test_get_flows_lista_por_cliente(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = [
            {"id": 1, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": "0 * * * *",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"},
        ]
        resp = client.get("/clients/1/flows/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_flows_filtro_flow_type(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = []
        resp = client.get("/clients/1/flows/?flow_type=items")
        assert resp.status_code == 200
        sql_calls = [str(c) for c in cursor.execute.call_args_list]
        assert any("flow_type" in s for s in sql_calls)

    def test_get_flow_por_id(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 10, "client_id": 1, "flow_name": "items", "flow_type": "items",
            "flow_config": {"sql": "SELECT 1"}, "schedule_cron": None,
            "is_active": True, "created_by": 1, "updated_by": 1,
            "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"
        }
        resp = client.get("/clients/1/flows/10")
        assert resp.status_code == 200
        assert resp.json()["flow_name"] == "items"

    def test_get_flow_cliente_no_existe_404(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.get("/clients/999/flows/")
        assert resp.status_code == 404

    def test_create_flow_exitoso(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 1},
            None,
            {"id": 20, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {"sql": "SELECT 1"}, "schedule_cron": "0 * * * *",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-08-19T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.post("/clients/1/flows/", json={
            "flow_name": "items", "flow_type": "items",
            "flow_config": {"sql": "SELECT 1"}, "schedule_cron": "0 * * * *"
        })
        assert resp.status_code == 201
        assert resp.json()["flow_name"] == "items"

    def test_create_flow_type_invalido(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        resp = client.post("/clients/1/flows/", json={
            "flow_name": "test", "flow_type": "invalido", "flow_config": {}
        })
        assert resp.status_code == 400
        assert "flow_type" in resp.json()["detail"]

    def test_create_flow_duplicado(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 1},
            {"id": 10},
        ]
        resp = client.post("/clients/1/flows/", json={
            "flow_name": "items", "flow_type": "items", "flow_config": {}
        })
        assert resp.status_code == 400
        assert "Ya existe" in resp.json()["detail"]

    def test_create_flow_registra_change_history(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 1},
            None,
            {"id": 20, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": None,
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-08-19T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.post("/clients/1/flows/", json={
            "flow_name": "items", "flow_type": "items", "flow_config": {}
        })
        assert resp.status_code == 201
        history_calls = [c for c in cursor.execute.call_args_list if "change_history" in str(c)]
        assert len(history_calls) >= 1

    def test_update_flow_campos_parciales(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 10, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": None,
              "is_active": True},
            None,
            {"id": 10, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": "*/5 * * * *",
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-01-01T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.put("/clients/1/flows/10", json={"schedule_cron": "*/5 * * * *"})
        assert resp.status_code == 200
        assert resp.json()["schedule_cron"] == "*/5 * * * *"

    def test_update_flow_registra_previous_values(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 10, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": None,
              "is_active": True},
            None,
            {"id": 10, "client_id": 1, "flow_name": "items_v2", "flow_type": "items",
              "flow_config": {}, "schedule_cron": None,
              "is_active": True, "created_by": 1, "updated_by": 1,
              "created_at": "2026-01-01T00:00:00", "updated_at": "2026-08-19T00:00:00"},
        ]
        resp = client.put("/clients/1/flows/10", json={"flow_name": "items_v2"})
        assert resp.status_code == 200
        history_calls = [c for c in cursor.execute.call_args_list if "change_history" in str(c)]
        assert len(history_calls) >= 1
        history_sql = str(history_calls[-1])
        assert "previous_values" in history_sql

    def test_update_flow_unicidad(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 10, "client_id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "schedule_cron": None,
              "is_active": True},
            {"id": 20},
        ]
        resp = client.put("/clients/1/flows/10", json={"flow_name": "compras", "flow_type": "purchases"})
        assert resp.status_code == 400
        assert "Ya existe" in resp.json()["detail"]

    def test_delete_flow_registra_change_history(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 10, "client_id": 1, "flow_name": "items", "flow_type": "items",
            "flow_config": {}, "schedule_cron": None,
            "is_active": True
        }
        resp = client.delete("/clients/1/flows/10")
        assert resp.status_code == 204
        history_calls = [c for c in cursor.execute.call_args_list if "change_history" in str(c)]
        assert len(history_calls) >= 1
        delete_calls = [c for c in cursor.execute.call_args_list if "DELETE" in str(c)]
        assert len(delete_calls) >= 1

    def test_delete_flow_solo_superadmin(self, app_with_role):
        client, cursor, conn = app_with_role(ADMIN_USER)
        resp = client.delete("/clients/1/flows/10")
        assert resp.status_code == 403


# ===========================================================================
# 7. TestExecutions (10)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestExecutions:

    def test_get_executions_historial(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = [
            {"id": 100, "flow_id": 1, "started_at": "2026-08-19T10:00:00",
              "finished_at": "2026-08-19T10:01:00", "status": "success",
              "result": {"creados": 5}, "error_message": None,
              "triggered_by": "scheduler", "triggered_user": None},
        ]
        resp = client.get("/flows/1/executions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_executions_filtro_status(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = []
        resp = client.get("/flows/1/executions?status=error")
        assert resp.status_code == 200
        sql_call = str(cursor.execute.call_args_list[-1])
        assert "status" in sql_call

    def test_get_executions_paginacion(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"id": 1}
        cursor.fetchall.return_value = []
        resp = client.get("/flows/1/executions?limit=10&offset=5")
        assert resp.status_code == 200
        last_call = cursor.execute.call_args_list[-1]
        params = last_call[0][1]
        assert 10 in params
        assert 5 in params

    def test_get_recent_executions(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = [
            {"id": 100, "flow_id": 1, "started_at": "2026-08-19T10:00:00",
              "finished_at": "2026-08-19T10:01:00", "status": "success",
              "result": None, "error_message": None,
              "triggered_by": "scheduler", "triggered_user": None},
        ]
        resp = client.get("/executions/recent")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_error_executions_incluye_client_name(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = [
            {"id": 100, "flow_id": 1, "started_at": "2026-08-19T10:00:00",
              "finished_at": "2026-08-19T10:01:00", "status": "error",
              "result": None, "error_message": "Connection timeout",
              "triggered_by": "scheduler", "triggered_user": None,
              "flow_name": "items", "client_slug": "fenix", "client_name": "Fenix"},
        ]
        resp = client.get("/executions/errors")
        assert resp.status_code == 200
        sql_call = str(cursor.execute.call_args_list[-1])
        assert "client_name" in sql_call or "c.name" in sql_call

    @patch("api.routes.executions.threading")
    def test_execute_flow_retorna_202(self, mock_threading, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "is_active": True,
              "client_slug": "fenix", "client_active": True},
            None,
        ]
        mock_threading.Thread.return_value = MagicMock()

        resp = client.post("/flows/1/execute")
        assert resp.status_code == 202
        body = resp.json()
        assert body["flow_name"] == "items"
        assert body["client"] == "fenix"
        mock_threading.Thread.assert_called_once()
        mock_threading.Thread.return_value.start.assert_called_once()

    def test_execute_flow_desactivado_400(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 1, "flow_name": "items", "flow_type": "items",
            "flow_config": {}, "is_active": False,
            "client_slug": "fenix", "client_active": True
        }
        resp = client.post("/flows/1/execute")
        assert resp.status_code == 400

    def test_execute_flow_cliente_desactivado_400(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {
            "id": 1, "flow_name": "items", "flow_type": "items",
            "flow_config": {}, "is_active": True,
            "client_slug": "fenix", "client_active": False
        }
        resp = client.post("/flows/1/execute")
        assert resp.status_code == 400

    def test_execute_flow_ya_corriendo_409(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"id": 1, "flow_name": "items", "flow_type": "items",
              "flow_config": {}, "is_active": True,
              "client_slug": "fenix", "client_active": True},
            {"id": 50},
        ]
        resp = client.post("/flows/1/execute")
        assert resp.status_code == 409

    def test_execute_flow_no_existe_404(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.post("/flows/999/execute")
        assert resp.status_code == 404


# ===========================================================================
# 8. TestDashboard (4)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestDashboard:

    def test_dashboard_status_retorna_resumen(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"total": 10, "activos": 8},
            {"total": 30, "activos": 25},
            {"total": 100, "exitosas": 80, "parciales": 10, "errores": 5, "en_curso": 5},
        ]
        cursor.fetchall.return_value = []

        resp = client.get("/dashboard/status")
        assert resp.status_code == 200
        body = resp.json()
        assert "result" in body
        result = body["result"]
        assert "clients" in result
        assert "flows" in result
        assert "executions_24h" in result
        assert "recent_executions" in result

    def test_dashboard_status_conteo_24h(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.side_effect = [
            {"total": 5, "activos": 5},
            {"total": 10, "activos": 10},
            {"total": 50, "exitosas": 40, "parciales": 5, "errores": 3, "en_curso": 2},
        ]
        cursor.fetchall.return_value = []

        resp = client.get("/dashboard/status")
        body = resp.json()
        exec_24h = body["result"]["executions_24h"]
        assert exec_24h["total"] == 50
        assert exec_24h["exitosas"] == 40
        assert exec_24h["errores"] == 3

    def test_dashboard_errors_solo_error_partial(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/dashboard/errors")
        assert resp.status_code == 200
        sql_call = str(cursor.execute.call_args_list[-1])
        assert "error" in sql_call.lower()
        assert "partial" in sql_call.lower()

    def test_dashboard_todos_roles_acceden(self, app_with_role):
        for user in [VIEWER_USER, ADMIN_USER, SUPERADMIN_USER]:
            client, cursor, conn = app_with_role(user)
            cursor.fetchone.side_effect = [
                {"total": 0, "activos": 0},
                {"total": 0, "activos": 0},
                {"total": 0, "exitosas": 0, "parciales": 0, "errores": 0, "en_curso": 0},
            ]
            cursor.fetchall.return_value = []
            resp = client.get("/dashboard/status")
            assert resp.status_code == 200, f"Fallo para rol {user['role']}"


# ===========================================================================
# 9. TestChanges (4)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestChanges:

    def test_get_changes_lista_global(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = [
            {"id": 1, "table_name": "flows", "record_id": 10, "action": "create",
              "changed_fields": {}, "previous_values": None, "changed_by": 1,
              "changed_at": "2026-08-19T10:00:00", "changed_by_name": "Admin",
              "changed_by_email": "admin@360software.com.co"},
        ]
        resp = client.get("/changes/")
        assert resp.status_code == 200
        body = resp.json()
        assert "result" in body
        assert len(body["result"]) == 1

    def test_get_changes_filtro_tabla(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/changes/?table_name=flows")
        assert resp.status_code == 200
        sql_call = str(cursor.execute.call_args_list[-1])
        assert "table_name" in sql_call

    def test_get_changes_filtro_usuario(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = []
        resp = client.get("/changes/?changed_by=1")
        assert resp.status_code == 200
        sql_call = str(cursor.execute.call_args_list[-1])
        assert "changed_by" in sql_call

    def test_get_record_history(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchall.return_value = [
            {"id": 1, "table_name": "flows", "record_id": 10, "action": "update",
              "changed_fields": {"flow_name": "items_v2"}, "previous_values": {"flow_name": "items"},
              "changed_by": 1, "changed_at": "2026-08-19T10:00:00",
              "changed_by_name": "Admin", "changed_by_email": "admin@360software.com.co"},
        ]
        resp = client.get("/changes/record/flows/10")
        assert resp.status_code == 200
        body = resp.json()
        assert "result" in body
        assert len(body["result"]) == 1


# ===========================================================================
# 10. TestTestConnections (6)
# ===========================================================================
@patch.dict(os.environ, {"ENV": "dev"})
class TestTestConnections:

    @patch("main.build_connector")
    @patch("config.loader.ConfigLoader")
    def test_erp_connection_exitosa(self, MockLoader, mock_build, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"client_id": "fenix", "erp_type": "ws"}

        mock_loader_inst = MagicMock()
        mock_loader_inst.load_config.return_value = {"erp": {"tipo": "ws"}, "odoo": {}}
        MockLoader.return_value = mock_loader_inst

        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = (True, "Conexion exitosa con SIESA WS")
        mock_build.return_value = mock_connector

        resp = client.post("/clients/1/test/erp")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["erp_type"] == "ws"

    @patch("main.build_connector")
    @patch("config.loader.ConfigLoader")
    def test_erp_connection_falla(self, MockLoader, mock_build, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"client_id": "bycsa", "erp_type": "sap"}

        mock_loader_inst = MagicMock()
        mock_loader_inst.load_config.return_value = {"erp": {"tipo": "sap"}, "odoo": {}}
        MockLoader.return_value = mock_loader_inst

        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = (False, "Timeout de red")
        mock_build.return_value = mock_connector

        resp = client.post("/clients/1/test/erp")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["code"] == 400

    def test_erp_cliente_no_existe_404(self, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = None
        resp = client.post("/clients/999/test/erp")
        assert resp.status_code == 404

    @patch("connection.jsonrpc.JsonRPC")
    @patch("config.loader.ConfigLoader")
    def test_odoo_connection_exitosa(self, MockLoader, MockJsonRPC, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"client_id": "fenix"}

        mock_loader_inst = MagicMock()
        mock_loader_inst.load_config.return_value = {
            "erp": {}, "odoo": {"url": "https://fenix.360software.com.co"}
        }
        MockLoader.return_value = mock_loader_inst

        mock_odoo = MagicMock()
        mock_odoo.test_connection.return_value = (True, "Autenticacion exitosa")
        MockJsonRPC.return_value = mock_odoo

        resp = client.post("/clients/1/test/odoo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "fenix" in body["odoo_url"]

    @patch("connection.jsonrpc.JsonRPC")
    @patch("config.loader.ConfigLoader")
    def test_odoo_connection_falla(self, MockLoader, MockJsonRPC, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"client_id": "fenix"}

        mock_loader_inst = MagicMock()
        mock_loader_inst.load_config.return_value = {
            "erp": {}, "odoo": {"url": "https://fenix.360software.com.co"}
        }
        MockLoader.return_value = mock_loader_inst

        mock_odoo = MagicMock()
        mock_odoo.test_connection.return_value = (False, "Invalid credentials")
        MockJsonRPC.return_value = mock_odoo

        resp = client.post("/clients/1/test/odoo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["code"] == 400

    @patch("config.loader.ConfigLoader")
    def test_odoo_gcp_no_carga_400(self, MockLoader, app_client):
        client, cursor, conn = app_client
        cursor.fetchone.return_value = {"client_id": "fenix"}

        mock_loader_inst = MagicMock()
        mock_loader_inst.load_config.return_value = None
        MockLoader.return_value = mock_loader_inst

        resp = client.post("/clients/1/test/odoo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["code"] == 400

# --- TestCatalog: endpoints de catalogo (sin autenticacion) ---

class TestCatalog:
    """GET /catalog/* — enumeraciones que consume el frontend.
    Son publicos: no llevan Authorization."""

    def _cliente_sin_auth(self):
        from fastapi.testclient import TestClient
        from api.app import app
        app.dependency_overrides.clear()
        return TestClient(app)

    # ---- determination-functions ----

    def test_determination_functions_responde_200(self):
        resp = self._cliente_sin_auth().get("/catalog/determination-functions")
        assert resp.status_code == 200

    def test_determination_functions_no_requiere_token(self):
        # Sin header Authorization debe funcionar igual
        resp = self._cliente_sin_auth().get("/catalog/determination-functions")
        assert resp.status_code != 401
        assert resp.status_code != 403

    def test_determination_functions_estructura_de_respuesta(self):
        body = self._cliente_sin_auth().get("/catalog/determination-functions").json()
        assert body["code"] == 200
        assert isinstance(body["result"], list)

    def test_determination_functions_devuelve_siete(self):
        body = self._cliente_sin_auth().get("/catalog/determination-functions").json()
        assert len(body["result"]) == 7

    def test_determination_functions_coincide_con_el_catalogo(self):
        from transform.utils.determination_functions import CATALOG
        body = self._cliente_sin_auth().get("/catalog/determination-functions").json()
        assert {f["name"] for f in body["result"]} == set(CATALOG)

    def test_determination_functions_cada_una_trae_label_y_descripcion(self):
        body = self._cliente_sin_auth().get("/catalog/determination-functions").json()
        for f in body["result"]:
            assert f["label"], f["name"]
            assert f["descripcion"], f["name"]

    def test_determination_functions_cada_param_trae_su_metadata(self):
        body = self._cliente_sin_auth().get("/catalog/determination-functions").json()
        for f in body["result"]:
            assert isinstance(f["params"], list)
            for p in f["params"]:
                assert "name" in p and "required" in p and "descripcion" in p

    def test_determination_functions_no_expone_la_funcion_python(self):
        # El campo `fn` del CATALOG no debe serializarse hacia el front
        body = self._cliente_sin_auth().get("/catalog/determination-functions").json()
        for f in body["result"]:
            assert "fn" not in f

    # ---- flow-types ----

    def test_flow_types_responde_200(self):
        assert self._cliente_sin_auth().get("/catalog/flow-types").status_code == 200

    def test_flow_types_devuelve_los_cinco(self):
        body = self._cliente_sin_auth().get("/catalog/flow-types").json()
        assert {f["value"] for f in body["result"]} == {
            "items", "customer", "supplier", "purchases", "sales"
        }

    def test_flow_types_coincide_con_valid_flow_types_de_flows(self):
        from api.routes.flows import VALID_FLOW_TYPES
        body = self._cliente_sin_auth().get("/catalog/flow-types").json()
        assert {f["value"] for f in body["result"]} == set(VALID_FLOW_TYPES)

    def test_flow_types_no_incluye_partners(self):
        # `partners` dejo de ser flow_type: se partio en customer y supplier
        body = self._cliente_sin_auth().get("/catalog/flow-types").json()
        assert "partners" not in {f["value"] for f in body["result"]}

    def test_flow_types_cada_uno_trae_label(self):
        body = self._cliente_sin_auth().get("/catalog/flow-types").json()
        assert all(f["label"] for f in body["result"])

    # ---- erp-types ----

    def test_erp_types_responde_200(self):
        assert self._cliente_sin_auth().get("/catalog/erp-types").status_code == 200

    def test_erp_types_devuelve_los_cuatro_soportados(self):
        body = self._cliente_sin_auth().get("/catalog/erp-types").json()
        assert {e["value"] for e in body["result"]} == {"ws", "connekta", "sap", "excel"}

    def test_erp_types_no_incluye_kubapp(self):
        # kubapp no tiene conector: build_connector() lo rechaza con ValueError
        body = self._cliente_sin_auth().get("/catalog/erp-types").json()
        assert "kubapp" not in {e["value"] for e in body["result"]}

    def test_erp_types_todos_tienen_conector_en_build_connector(self):
        import inspect
        import main
        fuente = inspect.getsource(main.build_connector)
        body = self._cliente_sin_auth().get("/catalog/erp-types").json()
        for e in body["result"]:
            assert f'"{e["value"]}"' in fuente, e["value"]

    def test_erp_types_cada_uno_trae_label(self):
        body = self._cliente_sin_auth().get("/catalog/erp-types").json()
        assert all(e["label"] for e in body["result"])


# --- TestSQLIntegridad: chequeos estaticos sobre las sentencias SQL ---

class TestSQLIntegridad:
    """Los tests con cursor mockeado no detectan errores de sintaxis SQL,
    porque la sentencia nunca llega a Postgres. Estas pruebas leen el codigo
    fuente y verifican que columnas y placeholders cuadren."""

    def _insert_de(self, fuente, tabla):
        import re
        m = re.search(
            r"INSERT INTO\s+" + tabla + r"\s*\((.*?)\)\s*VALUES\s*\((.*?)\)",
            fuente, re.S | re.I
        )
        assert m, f"No se encontro el INSERT de {tabla}"
        columnas = [c.strip() for c in m.group(1).split(",") if c.strip()]
        placeholders = m.group(2).count("%s")
        return columnas, placeholders

    def test_insert_de_flows_columnas_igual_placeholders(self):
        # Regresion del bug de la coma faltante en `schedule_cron created_by`,
        # que hacia fallar POST /clients/{id}/flows/ con error de sintaxis.
        import inspect
        from api.routes import flows
        columnas, placeholders = self._insert_de(inspect.getsource(flows), "flows")
        assert len(columnas) == placeholders, (
            f"{len(columnas)} columnas contra {placeholders} placeholders: {columnas}"
        )

    def test_insert_de_flows_no_tiene_columnas_pegadas(self):
        # Dos identificadores separados solo por espacio dentro de la lista de
        # columnas significan que falta una coma.
        import inspect
        from api.routes import flows
        columnas, _ = self._insert_de(inspect.getsource(flows), "flows")
        for col in columnas:
            assert " " not in col, f"Falta una coma antes de: '{col}'"

    def test_insert_de_flows_no_referencia_execution_order(self):
        # La columna se elimino del esquema; referenciarla rompe el INSERT.
        import inspect
        from api.routes import flows
        columnas, _ = self._insert_de(inspect.getsource(flows), "flows")
        assert "execution_order" not in columnas

    def test_insert_de_change_history_columnas_igual_placeholders(self):
        import inspect
        from api.routes import flows
        fuente = inspect.getsource(flows)
        import re
        for m in re.finditer(
            r"INSERT INTO\s+change_history\s*\((.*?)\)\s*VALUES\s*\((.*?)\)",
            fuente, re.S | re.I
        ):
            columnas = [c.strip() for c in m.group(1).split(",") if c.strip()]
            valores = m.group(2)
            placeholders = valores.count("%s") + len(re.findall(r"'\w+'", valores))
            assert len(columnas) == placeholders, columnas

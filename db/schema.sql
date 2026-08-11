-- ============================================================
-- schema.sql — BD del integrador
-- 5 tablas · triggers · indices
-- Fase: 5 — BD del integrador
-- Motor: PostgreSQL 16+
--
-- Tablas:
--   users           — administradores del front (SSO Google)
--   clients         — empresas clientes
--   flows           — configuracion de flujos (flow_config JSONB)
--   executions      — log de cada corrida
--   change_history  — historico de cambios para rollback
-- ============================================================

-- ============================================================
-- 1. USERS
-- ============================================================
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    name          VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'viewer'
                  CHECK (role IN ('superadmin', 'admin', 'viewer')),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 2. CLIENTS
-- ============================================================
CREATE TABLE clients (
    id            SERIAL PRIMARY KEY,
    client_id     VARCHAR(50)  NOT NULL UNIQUE,
    name          VARCHAR(255) NOT NULL,
    erp_type      VARCHAR(20)  NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by    INTEGER      REFERENCES users(id),
    updated_by    INTEGER      REFERENCES users(id),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 3. FLOWS
-- ============================================================
CREATE TABLE flows (
    id            SERIAL PRIMARY KEY,
    client_id     INTEGER      NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    flow_name     VARCHAR(50)  NOT NULL,
    flow_type     VARCHAR(20)  NOT NULL
                  CHECK (flow_type IN ('items', 'customer', 'supplier', 'purchases', 'sales')),
    flow_config   JSONB        NOT NULL DEFAULT '{}',
    schedule_cron VARCHAR(50),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by    INTEGER      REFERENCES users(id),
    updated_by    INTEGER      REFERENCES users(id),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE (client_id, flow_name)
);

-- ============================================================
-- 4. EXECUTIONS
-- ============================================================
CREATE TABLE executions (
    id              SERIAL PRIMARY KEY,
    flow_id         INTEGER      NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          VARCHAR(20)  NOT NULL DEFAULT 'running'
                    CHECK (status IN ('running', 'success', 'partial', 'error')),
    result          JSONB,
    error_message   TEXT,
    triggered_by    VARCHAR(20)  NOT NULL DEFAULT 'scheduler'
                    CHECK (triggered_by IN ('scheduler', 'manual', 'api')),
    triggered_user  INTEGER      REFERENCES users(id)
);

CREATE INDEX idx_executions_flow_started
    ON executions (flow_id, started_at DESC);

CREATE INDEX idx_executions_status
    ON executions (status)
    WHERE status IN ('error', 'partial');

-- ============================================================
-- 5. CHANGE_HISTORY
-- ============================================================
CREATE TABLE change_history (
    id              SERIAL PRIMARY KEY,
    table_name      VARCHAR(50)  NOT NULL,
    record_id       INTEGER      NOT NULL,
    action          VARCHAR(20)  NOT NULL
                    CHECK (action IN ('create', 'update', 'delete')),
    changed_fields  JSONB,
    previous_values JSONB,
    changed_by      INTEGER      REFERENCES users(id),
    changed_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_change_history_record
    ON change_history (table_name, record_id, changed_at DESC);

-- ============================================================
-- TRIGGER: updated_at automatico
-- ============================================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_clients_updated
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_flows_updated
    BEFORE UPDATE ON flows
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================
-- DATOS INICIALES
-- ============================================================

-- Usuarios
INSERT INTO users (email, name, role) VALUES
    ('jorge.rivera@360software.com.co', 'Jorge Rivera', 'superadmin'),
    ('simon.trillos@360software.com.co', 'Simon Trillos', 'superadmin'),
    ('danilo.vergara@360software.com.co', 'Danilo Vergara', 'superadmin');

-- Clientes
INSERT INTO clients (client_id, name, erp_type, created_by) VALUES
    ('fenix',           'Fenix',                'ws',       1),
    ('faizan',          'Faizan',               'ws',       1),
    ('surtinegocios',   'Surtinegocios',        'ws',       1),
    ('papis',           'Papis',                'ws',       1),
    ('titopabon',       'Tito Pabon',           'connekta', 1),
    ('oit',             'OIT',                  'connekta', 1),
    ('simonbolivar',    'R.P. Simon Bolivar',   'connekta', 1),
    ('bycsa',           'BYCSA',                'sap',      1),
    ('fabercastell',    'Faber Castell',        'sap',      1);

# Guía de instalación — Integrador ERP ↔ WMS
### 360 Software — Medellín, Colombia

---

## Requisitos del servidor

```
Sistema operativo:  Ubuntu 20.04 o superior
Python:             3.11 o superior (recomendado)
                    3.10 funciona pero Google dejará de soportarlo en oct 2026
Git:                cualquier versión reciente
Acceso:             SSH con usuario root o sudo
Conexión:           acceso a internet para GCP y los ERPs
```

---

## 1. Configuración de GCP

### 1.1 Habilitar la API de Secret Manager

```
GCP Console
→ APIs y servicios
→ Biblioteca
→ buscar "Secret Manager API"
→ Habilitar
```

> Requiere el rol **Administrador de Service Usage** o ser Owner del proyecto.

---

### 1.2 Crear cuenta de servicio

```
GCP Console
→ IAM y administración
→ Cuentas de servicio
→ Crear cuenta de servicio
  Nombre:      integrador-service-account
  Descripción: Cuenta de servicio del integrador ERP WMS
→ Siguiente
→ Asignar rol: Usuario con acceso a secretos de Secret Manager
→ Listo
```

---

### 1.3 Descargar la clave JSON

```
GCP Console
→ IAM y administración
→ Cuentas de servicio
→ clic en integrador-service-account
→ pestaña Claves
→ Agregar clave → Crear clave nueva → JSON
→ El archivo se descarga automáticamente
```

> ⚠️ Este archivo es la llave de acceso a GCP. Nunca subirlo al repositorio. Guardarlo en un lugar seguro.

---

### 1.4 Crear secrets por cliente

Por cada cliente crear un secret en GCP Secret Manager con el nombre `integrador-{client_id}`.

**Nombre del secret:**
```
integrador-fenix
integrador-faizan
integrador-surtinegocios
integrador-papis
integrador-titopabon
integrador-oit
integrador-rpsimonbolivar
integrador-bycsa
integrador-fabercastell
integrador-autovenz
```

**Formato del JSON según tipo de ERP:**

SIESA WS:
```json
{
  "erp": {
    "tipo":       "ws",
    "url":        "https://ws001.siesacloud.com:8080/...",
    "compania":   "1",
    "usuario":    "usuario_integracion",
    "clave":      "contraseña",
    "conexion":   "UnoEE (Nombre Cliente)",
    "proveedor":  "BEXCONNECT",
    "proxy_host": null,
    "proxy_port": null
  },
  "odoo": {
    "url":      "https://cliente.360software.com.co",
    "database": "cliente_v17_prod",
    "usuario":  "integrador@cliente.com",
    "clave":    "contraseña_odoo"
  }
}
```

SIESA Connekta:
```json
{
  "erp": {
    "tipo":       "connekta",
    "url":        "https://servicios.siesacloud.com/api/connekta/v3/ejecutarconsulta?idCompania=XXXX&descripcion=",
    "url_qa":     "https://serviciosqa.siesacloud.com/api/connekta/v3/ejecutarconsulta?idCompania=XXXX&descripcion=",
    "connikey":   "llave_connekta",
    "connitoken": "token_connekta"
  },
  "odoo": {
    "url":      "https://cliente.360software.com.co",
    "database": "cliente_v17_prod",
    "usuario":  "integrador@cliente.com",
    "clave":    "contraseña_odoo"
  }
}
```

SAP B1:
```json
{
  "erp": {
    "tipo":     "sap",
    "url":      "https://servidor-sap:50000",
    "compania": "SBO_EMPRESA",
    "usuario":  "usuario_sap",
    "clave":    "contraseña_sap"
  },
  "odoo": {
    "url":      "https://cliente.360software.com.co",
    "database": "cliente_v17_prod",
    "usuario":  "integrador@cliente.com",
    "clave":    "contraseña_odoo"
  }
}
```

KubApp:
```json
{
  "erp": {
    "tipo":    "kubapp",
    "url":     "https://www.kubapp.co/api",
    "usuario": "BEXMOVIL@cliente",
    "clave":   "contraseña"
  },
  "odoo": {
    "url":      "https://cliente.360software.com.co",
    "database": "cliente_v17_prod",
    "usuario":  "integrador@cliente.com",
    "clave":    "contraseña_odoo"
  }
}
```

---

## 2. Configuración del servidor

### 2.1 Crear carpetas necesarias

```bash
mkdir -p /etc/integrador/credentials
mkdir -p /var/log/integrador
mkdir -p /app
```

---

### 2.2 Copiar la clave JSON al servidor

Desde tu máquina local:
```bash
scp gcp-key.json usuario@ip-servidor:/etc/integrador/gcp-key.json
```

O desde la consola SSH del servidor:
```bash
nano /etc/integrador/gcp-key.json
# pegar el contenido del JSON
# Ctrl + O → Enter → Ctrl + X
```

Verificar que quedó:
```bash
cat /etc/integrador/gcp-key.json
```

---

### 2.3 Clonar el repositorio

```bash
cd /app
git clone https://github.com/jorgerivera360/integrador-360.git
cd integrador-360
```

Si el repositorio es privado usar token de acceso:
```bash
git clone https://TOKEN@github.com/jorgerivera360/integrador-360.git
```

---

### 2.4 Cambiar a la rama correcta

```bash
git checkout develop
```

O para una fase específica:
```bash
git checkout fase1/config-layer-gcp
```

---

### 2.5 Crear el entorno virtual

```bash
cd /app/integrador-360
python3 -m venv venv
source venv/bin/activate
```

Verificar que está activo:
```bash
which python
# debe mostrar: /app/integrador-360/venv/bin/python
```

---

### 2.6 Instalar dependencias

```bash
pip install -r requirements.txt
```

---

### 2.7 Crear el archivo .env

```bash
nano /app/integrador-360/.env
```

Contenido:
```
ENV=staging
CLIENT_ID=fenix
GCP_PROJECT_ID=hale-treat-398215
GOOGLE_APPLICATION_CREDENTIALS=/etc/integrador/gcp-key.json
LOG_PATH=/var/log/integrador
CREDENTIALS_PATH=/etc/integrador/credentials
```

Guardar con `Ctrl + O` → `Enter` → `Ctrl + X`.

---

### 2.8 Verificar permisos

```bash
# El proceso debe poder escribir en estas carpetas
chmod 755 /etc/integrador/credentials
chmod 755 /var/log/integrador
```

---

## 3. Verificar que funciona

### 3.1 Crear archivo de prueba

```bash
nano /app/integrador-360/prueba.py
```

Contenido:
```python
from config.loader import ConfigLoader

loader = ConfigLoader(client_id='fenix')
config = loader.load_config()
print(config)
```

---

### 3.2 Activar el entorno y ejecutar

```bash
source /app/integrador-360/venv/bin/activate
cd /app/integrador-360
python prueba.py
```

Debe imprimir el dict de configuración de Fénix.

---

### 3.3 Verificar el log

```bash
cat /var/log/integrador/integrador-fenix.log
```

Debe mostrar:
```
INFO — Secret traído exitosamente desde GCP para fenix
INFO — Credenciales guardadas localmente en /etc/integrador/credentials/integrador-fenix.json
```

---

### 3.4 Verificar las credenciales locales

```bash
cat /etc/integrador/credentials/integrador-fenix.json
```

Debe mostrar el JSON completo del cliente.

---

### 3.5 Verificar el fallback

Cambiar el GCP_PROJECT_ID a un valor inválido en el .env:
```bash
nano .env
# Cambiar GCP_PROJECT_ID=hale-treat-398215
# por     GCP_PROJECT_ID=proyecto-invalido
```

Ejecutar de nuevo:
```bash
python prueba.py
```

El log debe mostrar:
```
ERROR   — GCP no disponible: 403 Permission denied
WARNING — Cargando credenciales desde almacenamiento local para fenix
```

Y debe retornar el mismo config. Restaurar el .env con el project_id correcto al terminar.

---

### 3.6 Eliminar el archivo de prueba

```bash
rm /app/integrador-360/prueba.py
```

---

## 4. Cómo actualizar el código

Cuando haya cambios en el repositorio:

```bash
cd /app/integrador-360
source venv/bin/activate
git pull origin develop
```

---

## 5. Cómo agregar un cliente nuevo

### 5.1 Crear el secret en GCP

```
GCP Console
→ Secret Manager
→ Crear secreto
→ Nombre: integrador-{client_id}
→ Valor: JSON con credenciales del cliente
→ Crear
```

### 5.2 Verificar en el servidor

```bash
cd /app/integrador-360
source venv/bin/activate
python -c "
from config.loader import ConfigLoader
loader = ConfigLoader(client_id='nuevo_cliente')
config = loader.load_config()
print('Tipo ERP:', config['erp']['tipo'])
print('Odoo URL:', config['odoo']['url'])
"
```

---

## 6. Ver logs en tiempo real

```bash
# Ver logs de un cliente específico
tail -f /var/log/integrador/integrador-fenix.log

# Ver últimas 50 líneas
tail -50 /var/log/integrador/integrador-fenix.log

# Ver todos los logs
ls /var/log/integrador/
```

---

## 7. Estructura de carpetas en el servidor

```
/app/
└── integrador-360/          ← proyecto clonado desde GitHub
    ├── venv/                ← entorno virtual Python
    ├── config/
    ├── connection/
    ├── transform/
    ├── core/
    ├── scheduler/
    ├── db/
    ├── api/
    ├── frontend/
    ├── tests/
    ├── .env                 ← variables de entorno del servidor
    └── requirements.txt

/etc/integrador/
├── gcp-key.json             ← clave JSON de la cuenta de servicio GCP
└── credentials/             ← respaldo local de credenciales por cliente
    ├── integrador-fenix.json
    ├── integrador-faizan.json
    └── ...

/var/log/integrador/         ← logs del integrador por cliente
    ├── integrador-fenix.log
    ├── integrador-faizan.log
    └── ...
```
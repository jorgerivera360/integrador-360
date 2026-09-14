"""
tunnel.py — Gestión de túneles SSH para conectividad con ERPs/WMS remotos
Si el config del cliente tiene ssh_enabled=true en erp u odoo,
abre un túnel SSH y reescribe la URL a localhost:puerto_local.
Los conectores no saben del túnel — solo ven la URL reescrita.
"""
import logging
import paramiko
from urllib.parse import urlparse, urlunparse

# Parche de compatibilidad: sshtunnel 0.4.0 busca paramiko.DSSKey
# que fue eliminado en paramiko 4.0+ (DSA está obsoleto).
# Se agrega como dummy para que sshtunnel no explote al iniciar.
if not hasattr(paramiko, 'DSSKey'):
    paramiko.DSSKey = paramiko.RSAKey

_logger = logging.getLogger(__name__)


def start_tunnels(config, logger=None):
    """Abre túneles SSH si están configurados en erp y/o odoo.
    Reescribe las URLs en config in-place.
    Retorna lista de túneles activos para cerrar después.
    """
    tunnels = []

    for seccion in ("erp", "odoo"):
        seccion_config = config.get(seccion, {})
        if not seccion_config.get("ssh_enabled"):
            continue

        ssh_host = seccion_config.get("ssh_host")
        ssh_port = int(seccion_config.get("ssh_port", 22))
        ssh_user = seccion_config.get("ssh_user")
        ssh_key_path = seccion_config.get("ssh_key_path")
        ssh_password = seccion_config.get("ssh_password")

        if not ssh_host or not ssh_user:
            msg = f"Túnel SSH habilitado para {seccion} pero faltan ssh_host o ssh_user"
            if logger:
                logger.warning(msg)
            continue

        url_original = seccion_config.get("url", "")
        if not url_original:
            continue

        parsed = urlparse(url_original)
        remote_host = parsed.hostname
        remote_port = parsed.port or (443 if parsed.scheme == "https" else 80)

        try:
            from sshtunnel import SSHTunnelForwarder

            ssh_kwargs = {
                "ssh_address_or_host": (ssh_host, ssh_port),
                "ssh_username": ssh_user,
                "remote_bind_address": (remote_host, remote_port),
            }

            if ssh_key_path:
                ssh_kwargs["ssh_pkey"] = ssh_key_path
            elif ssh_password:
                ssh_kwargs["ssh_password"] = ssh_password
            else:
                msg = f"Túnel SSH para {seccion}: se requiere ssh_key_path o ssh_password"
                if logger:
                    logger.error(msg)
                continue

            tunnel = SSHTunnelForwarder(**ssh_kwargs)
            tunnel.start()

            local_port = tunnel.local_bind_port
            new_url = urlunparse(parsed._replace(
                netloc=f"localhost:{local_port}"
            ))

            config[seccion]["url"] = new_url
            tunnels.append(tunnel)

            log_msg = (
                f"Túnel SSH {seccion}: {ssh_user}@{ssh_host}:{ssh_port} → "
                f"{remote_host}:{remote_port} → localhost:{local_port}"
            )
            if logger:
                logger.info(log_msg)
            else:
                _logger.info(log_msg)

        except ImportError:
            msg = "sshtunnel no instalado. Ejecutar: pip install sshtunnel"
            if logger:
                logger.error(msg)
            raise RuntimeError(msg)
        except Exception as e:
            msg = f"Error al abrir túnel SSH para {seccion}: {e}"
            if logger:
                logger.error(msg)
            raise RuntimeError(msg)

    return tunnels


def stop_tunnels(tunnels):
    """Cierra todos los túneles activos."""
    for tunnel in tunnels:
        try:
            tunnel.stop()
        except Exception:
            pass

def ppk_to_pem(contenido: bytes) -> bytes:
    """Convierte una llave PPK (v2/v3, sin encriptar) a formato PEM OpenSSH."""
    import base64
    import struct
    from cryptography.hazmat.primitives.asymmetric.rsa import (
        RSAPrivateNumbers, RSAPublicNumbers, rsa_crt_dmp1, rsa_crt_dmq1
    )
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    lines = contenido.decode("utf-8", errors="ignore").splitlines()

    public_lines = []
    private_lines = []
    section = None
    count = 0

    for line in lines:
        line = line.strip()
        if line.startswith("Public-Lines:"):
            count = int(line.split(":")[1].strip())
            section = "public"
            continue
        elif line.startswith("Private-Lines:"):
            count = int(line.split(":")[1].strip())
            section = "private"
            continue
        elif ":" in line and section is None:
            continue

        if section == "public" and count > 0:
            public_lines.append(line)
            count -= 1
            if count == 0:
                section = None
        elif section == "private" and count > 0:
            private_lines.append(line)
            count -= 1
            if count == 0:
                section = None

    pub_blob = base64.b64decode("".join(public_lines))
    priv_blob = base64.b64decode("".join(private_lines))

    def read_mpint(data, offset):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        value = int.from_bytes(data[offset:offset + length], "big")
        offset += length
        return value, offset

    def read_string(data, offset):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        offset += length
        return offset

    # Public blob: key_type, e, n
    offset = read_string(pub_blob, 0)
    e, offset = read_mpint(pub_blob, offset)
    n, offset = read_mpint(pub_blob, offset)

    # Private blob: d, p, q, iqmp
    offset = 0
    d, offset = read_mpint(priv_blob, offset)
    p, offset = read_mpint(priv_blob, offset)
    q, offset = read_mpint(priv_blob, offset)
    iqmp, offset = read_mpint(priv_blob, offset)

    dmp1 = rsa_crt_dmp1(d, p)
    dmq1 = rsa_crt_dmq1(d, q)

    public_numbers = RSAPublicNumbers(e, n)
    private_numbers = RSAPrivateNumbers(p, q, d, dmp1, dmq1, iqmp, public_numbers)
    private_key = private_numbers.private_key(default_backend())

    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )
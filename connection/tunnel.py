"""
tunnel.py — Gestión de túneles SSH para conectividad con ERPs/WMS remotos
Si el config del cliente tiene ssh_enabled=true en erp u odoo,
abre un túnel SSH y reescribe la URL a localhost:puerto_local.
Los conectores no saben del túnel — solo ven la URL reescrita.
"""
import logging
from urllib.parse import urlparse, urlunparse

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
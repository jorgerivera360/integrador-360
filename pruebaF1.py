from config.logger import IntegradorLogger

logger = IntegradorLogger(client_id='fenix')
logger.info("Logger inicializado correctamente")
logger.warning("Esto es una advertencia")
logger.error("Esto es un error")
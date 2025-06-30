from loguru import logger


logger = logger.bind(name="univy")
logger.add("logs/univy.log", rotation="10 MB", retention="10 days")

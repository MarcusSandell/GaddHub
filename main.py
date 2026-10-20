""""""
import logging

from config import Config, get_config_path
from watcher import watch

def setup_logging() -> None:
    log_path = get_config_path().with_name("gaddhub.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Application starting")
    try:
        config = Config.load()
        logger.info(config)
    except Exception:
        logger.exception("Failed to load configuration")
        raise

    watch(config.wow_path)

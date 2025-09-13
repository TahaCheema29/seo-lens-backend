import logging

def setup_logger(name: str) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # or INFO in production

    if not logger.handlers:  # Avoid adding duplicate handlers
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # File handler (all logs will also go to app.log)
        fh = logging.FileHandler("app.log", mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)

        # Formatter (applies to both handlers)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # Attach handlers
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger

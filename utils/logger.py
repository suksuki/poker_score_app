import logging
import os
import sys

def setup_logger(name="PokerScoreApp", log_file="app.log", level=logging.INFO):
    """
    Sets up a logger that writes to console and a file.
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # clear existing handlers to avoid duplicates on reload
    if logger.hasHandlers():
        logger.handlers.clear()

    # Stream Handler (stdout)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    # File Handler
    try:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        sys.stderr.write(f"Failed to setup log file handler: {e}\n")

    return logger

# Global logger instance
logger = setup_logger()

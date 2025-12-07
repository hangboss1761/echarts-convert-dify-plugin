"""
Shared logger utility for ECharts conversion tool modules
"""
import logging
import os
from dify_plugin.config.logger_format import plugin_logger_handler


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a configured logger instance for the given module name

    Args:
        name: Module name (defaults to calling module's __name__)

    Returns:
        Configured logger instance
    """
    if name is None:
        name = __name__

    logger = logging.getLogger(name)

    # Set log level based on environment
    # Use DEBUG level for development, INFO for production
    log_level = logging.DEBUG if os.environ.get('ECHARTS_CONVERT_DEBUG') else logging.INFO
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(plugin_logger_handler)

    return logger
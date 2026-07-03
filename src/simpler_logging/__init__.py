from .logger import LogLevel as LogLevel, Logger as Logger, Handler as Handler

logger = Logger("Main")
"""a global Logger instance for convenience."""

debug = logger.debug
info = logger.info
warn = logger.warn
warning = logger.warn
error = logger.error
fatal = logger.fatal
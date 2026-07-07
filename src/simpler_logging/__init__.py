from .logger import LogLevel as LogLevel, Logger as Logger, Handler as Handler, FatalError as FatalError

logger = Logger("Main")
"""a global Logger instance for convenience."""

trace = logger.trace
debug = logger.debug
info = logger.info
warn = logger.warn
warning = logger.warn
error = logger.error
fatal = logger.fatal
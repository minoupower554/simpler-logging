from __future__ import annotations
from functools import wraps
from enum import IntEnum
from colorama import init, Fore, Style
from datetime import datetime
from typing import Protocol, Iterable, Union

init()

class LogLevel(IntEnum):
    """Log Levels. Includes DEBUG, INFO, WARN, ERROR, and FATAL in that severity order."""
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50


class Handler(Protocol):
    """
    A Protocol definition for log Handlers.

    Function following it is expected to be able to receive msg (str), logger_name (str), and do_color (bool).
    """
    def __call__(self, *, level: LogLevel, msg: str, logger_name: str, do_color: bool) -> None:
        ...

_max_logger_name: int = 0

_DEFAULT_LOGGER_INFO: dict[LogLevel, Union[str, int]] = {
    LogLevel.DEBUG:  Fore.CYAN,
    LogLevel.INFO: Fore.GREEN,
    LogLevel.WARN: Fore.YELLOW,
    LogLevel.ERROR: Fore.RED,
    LogLevel.FATAL: Fore.LIGHTRED_EX,
}


# noinspection GrazieStyle
def default_formatter(level: LogLevel, msg: str, logger_name: str, do_color: bool) -> str:
    """Default formatter used by the logger. May be used in custom handlers.

    :param level: The Log Level to use.
    :param msg: The message to log.
    :param logger_name: The name of the logger.
    :param do_color: Whether or not to colorize the message."""
    color = _DEFAULT_LOGGER_INFO[level] if do_color else ""
    dim = Style.DIM if do_color else ""
    timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")

    return (f"{color}{dim}[{timestamp}]"
            f"{color} {level.name:<5} {dim}"
            f"{logger_name:<{_max_logger_name}}"
            f"{color}: {msg}"
            f"{Style.RESET_ALL if do_color else ''}"
            )


# noinspection GrazieStyle
def default_handler(*, level: LogLevel, msg: str, logger_name: str, do_color: bool):
    """Default Handler used by the logger. Can be used to reset Handlers.

    :param level: The Log Level to use.
    :param msg: The message to log.
    :param logger_name: The name of the logger.
    :param do_color: Whether or not to colorize the message."""
    print(default_formatter(level, msg, logger_name, do_color))


class FatalError(Exception):
    __module__ = "builtins"
    pass


class Logger:
    """
    The Logger class. It comes preloaded with default Handlers for all Log Levels.
    """
    __slots__ = ("_name", "_enabled_levels", "_handlers", "_do_color")

    # noinspection PyPep8Naming
    @staticmethod
    @wraps(default_formatter)
    def DEFAULT_FORMATTER():
        return default_formatter

    #noinspection PyPep8Naming
    @staticmethod
    @wraps(default_handler)
    def DEFAULT_HANDLER():
        return default_handler

    def __init__(self, name: str):
        """Create a new Logger instance."""
        self._name = name
        self._enabled_levels = {LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR, LogLevel.FATAL}

        self._handlers: dict[LogLevel, Handler] = {LogLevel.DEBUG: default_handler, LogLevel.INFO: default_handler,
                          LogLevel.WARN: default_handler, LogLevel.ERROR: default_handler,
                          LogLevel.FATAL: default_handler}
        self._do_color = True
        global _max_logger_name
        _max_logger_name = max(_max_logger_name, len(name)+1)

    def log(self, level: LogLevel, msg: str, *args, **kwargs) -> None:
        """Log a message taking into account the active levels. Generally you should use the dedicated per-level log methods instead.

        :param level: The Log Level to use.
        :param msg: The message to log."""
        if level in self._enabled_levels:
            self._handlers[level](
                level=level,
                msg=" ".join(
                    [msg]
                    + [str(x) for x in args]
                    + [f"{k}={v}" for k, v in kwargs.items()]
                ),
                logger_name=self._name,
                do_color=self._do_color,
            )


    @property
    def name(self) -> str:
        """Get the name of the Logger."""
        return self._name


    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log a debug message.

        :param msg: The message to log."""
        self.log(LogLevel.DEBUG, msg, *args, **kwargs)


    def info(self, msg: str, *args, **kwargs) -> None:
        """Log an info message.

        :param msg: The message to log."""
        self.log(LogLevel.INFO, msg, *args, **kwargs)


    def warn(self, msg: str, *args, **kwargs) -> None:
        """Log a warning message.

        :param msg: The message to log."""
        self.log(LogLevel.WARN, msg, *args, **kwargs)

    warning = warn

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log an error message.

        :param msg: The message to log."""
        self.log(LogLevel.ERROR, msg, *args, **kwargs)


    def fatal(self, msg: str, *args, inner: Union[Exception, None]=None, **kwargs) -> None:
        """Log a fatal message and terminate the program with an optional inner Error.

        :param msg: The error message to log.
        :param inner: The optional inner error.
        :raises FatalError: Terminates program."""
        self.log(LogLevel.FATAL, msg, *args, **kwargs)

        if inner is None:
            raise FatalError(msg)
        raise FatalError(msg) from inner


    def set_color(self, state: bool):
        """Change whether Handlers should use colors.

        :param state: Whether Handlers should use colors."""
        self._do_color = state


    def debug_handler(self, handler: Handler):
        """Set the debug Handler.

        :param handler: The handler to use."""
        self._handlers[LogLevel.DEBUG] = handler


    def info_handler(self, handler: Handler):
        """Set the info Handler.

        :param handler: The handler to use."""
        self._handlers[LogLevel.INFO] = handler


    def warn_handler(self, handler: Handler):
        """Set the warn Handler.

        :param handler: The handler to use."""
        self._handlers[LogLevel.WARN] = handler


    def error_handler(self, handler: Handler):
        """Set the error Handler.

        :param handler: The handler to use."""
        self._handlers[LogLevel.ERROR] = handler


    def fatal_handler(self, handler: Handler):
        """Set the fatal Handler.

        :param handler: The handler to use."""
        self._handlers[LogLevel.FATAL] = handler


    def enable_level(self, level: Union[LogLevel, Iterable[LogLevel]]):
        """Enable the given Log Level or Set of Log Levels. Does nothing if the Level is already enabled.

        :param level: The Log Level or Set of Log Levels to enable."""
        if isinstance(level, LogLevel):
            self._enabled_levels.add(level)
        else:
            self._enabled_levels.update(level)


    def disable_level(self, level: Union[LogLevel, Iterable[LogLevel]]):
        """Disable the given Log Level or Set of Log Levels. Does nothing if the Level is already disabled.

        :param level: The Log Level or Set of Log Levels to disable."""
        if isinstance(level, LogLevel):
            self._enabled_levels.discard(level)
        else:
            self._enabled_levels.difference_update(level)


    def toggle_level(self, level: Union[LogLevel, Iterable[LogLevel]]):
        """Toggles the given Log Level or Set of Log Levels.

        :param level: The Log Level or Set of Log Levels to toggle."""
        lvl = {level} if isinstance(level, LogLevel) else level
        self._enabled_levels.symmetric_difference_update(lvl)


    def min_level(self, level: LogLevel):
        """Set the minimum Log Level to use. Overwrites previous Log Level Configuration.

        :param level: The Log Level to use."""
        self._enabled_levels = {x for x in LogLevel if x >= level}
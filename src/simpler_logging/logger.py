from __future__ import annotations

import typing
from functools import wraps
from enum import IntEnum
from colorama import init, Fore, Style
from datetime import datetime
from typing import Protocol, Iterable, Union

init()

class LogLevel(IntEnum):
    """Log Levels. Includes TRACE, DEBUG, INFO, WARN, ERROR, and FATAL in that severity order."""
    TRACE = 10
    DEBUG = 20
    INFO = 30
    WARN = 40
    ERROR = 50
    FATAL = 60


class Handler(Protocol):
    """
    A Protocol definition for log Handlers.

    Function following it is expected to be able to receive msg (str), logger_name (str), do_color (bool) as well as *args and **kwargs.
    """
    def __call__(self, *args, level: LogLevel, msg: str, logger_name: str, do_color: bool, **kwargs) -> None:
        ...

# a bit of global state, so terrifying!
_max_logger_name: int = 0
_default_level: typing.Set[LogLevel] = {LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR, LogLevel.FATAL}

_DEFAULT_LOGGER_INFO: typing.Dict[LogLevel, Union[str, int]] = {
    LogLevel.TRACE: Fore.CYAN,
    LogLevel.DEBUG: Fore.MAGENTA,
    LogLevel.INFO: Fore.GREEN,
    LogLevel.WARN: Fore.YELLOW,
    LogLevel.ERROR: Fore.RED,
    LogLevel.FATAL: Fore.LIGHTRED_EX,
}


# noinspection GrazieStyle
def default_formatter(*args, level: LogLevel, msg: str, logger_name: str, do_color: bool, **kwargs) -> str:
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
            f"""{color}: {' '.join(
                    [msg]
                    + [repr(x) for x in args]
                    + [f'{k}={v!r}' for k, v in kwargs.items()]
                )}"""
            f"{Style.RESET_ALL if do_color else ''}"
            )


# noinspection GrazieStyle
def default_handler(*args, level: LogLevel, msg: str, logger_name: str, do_color: bool, **kwargs):
    """Default Handler used by the logger. Can be used to reset Handlers.

    :param level: The Log Level to use.
    :param msg: The message to log.
    :param logger_name: The name of the logger.
    :param do_color: Whether or not to colorize the message."""
    print(default_formatter(*args, level, msg, logger_name, do_color, **kwargs))


class FatalError(Exception):
    __module__ = "builtins"
    pass


class Logger:
    """
    The Logger class. It comes preloaded with default Handlers for all Log Levels.
    """
    __slots__ = ("_name", "_enabled_levels", "_handlers", "_do_color")


    @staticmethod
    def get_default_formatter() -> typing.Callable[..., str]:
        """Get the default formatter used by the logger."""
        return default_formatter


    @staticmethod
    def get_default_handler() -> Handler:
        """Get the default handler used by the logger."""
        return default_handler

    @staticmethod
    def enable_default_level(level: Union[LogLevel, Iterable[LogLevel]], *args: LogLevel) -> None:
        """Enable the given Loglevel or LogLevels in the default, affecting any Loggers created in the future.
        does NOT affect existing Loggers and does nothing if the LogLevel is already enabled.

        :param level: The LogLevel or LogLevels to enable."""
        _default_level.update(({level} if isinstance(level, LogLevel) else set(level)).union(args))

    @staticmethod
    def disable_default_level(level: Union[LogLevel, Iterable[LogLevel]], *args) -> None:
        """Disable the given Loglevel or LogLevels in the default, affecting any Loggers created in the future.
        does NOT affect existing Loggers and does nothing if the LogLevel is already disabled.

        :param level: The LogLevel or LogLevels to disable."""
        _default_level.difference_update(({level} if isinstance(level, LogLevel) else set(level)).union(args))

    @staticmethod
    def toggle_default_level(level: Union[LogLevel, Iterable[LogLevel]], *args) -> None:
        """Toggle the given Loglevel or LogLevels in the default, affecting any Loggers created in the future.
        does NOT affect existing Loggers.

        :param level: The LogLevel or LogLevels to toggle."""
        _default_level.symmetric_difference_update(({level} if isinstance(level, LogLevel) else set(level)).union(args))

    def __init__(self, name: str):
        """Create a new Logger instance."""
        self._name = name
        self._enabled_levels = _default_level.copy()

        self._handlers: typing.Dict[LogLevel, Handler] = {LogLevel.TRACE: default_handler, LogLevel.DEBUG: default_handler,
                          LogLevel.INFO: default_handler, LogLevel.WARN: default_handler,
                          LogLevel.ERROR: default_handler, LogLevel.FATAL: default_handler}
        self._do_color = True
        global _max_logger_name
        _max_logger_name = max(_max_logger_name, len(name)+1)

    def log(self, level: LogLevel, msg: str, *args, **kwargs) -> None:
        """Log a message taking into account the active levels. Generally you should use the dedicated per-level log methods instead.

        :param level: The Log Level to use.
        :param msg: The message to log."""
        if level in self._enabled_levels:
            self._handlers[level](
                *args,
                level=level,
                msg=msg,
                logger_name=self._name,
                do_color=self._do_color,
                **kwargs,
            )


    @property
    def name(self) -> str:
        """Get the name of the Logger."""
        return self._name


    def trace(self, msg: str, *args, **kwargs) -> None:
        """Log a trace message.

        :param msg: The message to log."""
        self.log(LogLevel.TRACE, msg, *args, **kwargs)


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


    def trace_handler(self, handler: Handler):
        """Set the trace Handler.

        :param handler: The handler to use."""
        self._handlers[LogLevel.TRACE] = handler


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


    def enable_level(self, level: Union[LogLevel, Iterable[LogLevel]], *args):
        """Enable the given LogLevel or LogLevels. Does nothing if the Level is already enabled.

        :param level: The LogLevel or LogLevels to enable."""
        self._enabled_levels.update(({level} if isinstance(level, LogLevel) else set(level)).union(args))


    def disable_level(self, level: Union[LogLevel, Iterable[LogLevel]], *args):
        """Disable the given LogLevel or LogLevels. Does nothing if the Level is already disabled.

        :param level: The LogLevel or LogLevels to disable."""
        self._enabled_levels.difference_update(({level} if isinstance(level, LogLevel) else set(level)).union(args))


    def toggle_level(self, level: Union[LogLevel, Iterable[LogLevel]], *args):
        """Toggles the given LogLevel or LogLevels.

        :param level: The LogLevel or LogLevels to toggle."""
        self._enabled_levels.symmetric_difference_update(({level} if isinstance(level, LogLevel) else set(level)).union(args))


    def min_level(self, level: LogLevel):
        """Set the minimum LogLevel to use. Overwrites previous LogLevel Configuration.

        :param level: The LogLevel to use."""
        self._enabled_levels = {x for x in LogLevel if x >= level}
import logging
from multiprocessing import Queue, Value
from multiprocessing import Process, get_context
from ctypes import c_wchar_p, c_int

class MPLogger:
    def __init__(self, logger_name, log_level) -> None:
        self._logger_name = logger_name
        self._log_level = log_level
        self._proc = None
        self._ctx = get_context("spawn")
        self._event_queue = self._ctx.Queue()

    def start(self):
        if self._proc is None or not self._proc.is_alive:
            logger_name = self._ctx.Value(c_wchar_p, self._logger_name)
            logger_level = self._ctx.Value(c_wchar_p, self._log_level)
            self._proc = self._ctx.Process(
                target=self._log,
                args=(self._event_queue, logger_name, logger_level)
            )

        self._proc.start()

    def log(self, msg, level):
        self._event_queue.put((msg, level))

    @staticmethod
    def _log(event_queue, logger_name, logger_level):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
        msg, level = event_queue.get()
        logger.log(logging.getLevelName(level), msg, exc_info=False)
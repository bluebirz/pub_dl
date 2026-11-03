import logging
import logging.config
from dataclasses import dataclass
from pathlib import Path

from components.file_manager import make_folder, read_yaml
from components.utils import get_current_time_str


@dataclass
class CustomLog(logging.Logger):
    """
    Class for create Logger
    credit: https://stackoverflow.com/questions/13733552/logger-configuration-to-log-to-file-and-print-to-stdout


    Attributes:
        logger_name: name of the logger object
    """

    logger_name: str = None
    __logger = None

    def __post_init__(self):
        log_config = read_yaml("./configs/logger_conf.yaml")
        logging.config.dictConfig(log_config)
        self.__logger = logging.getLogger(self.logger_name)

    def log(self, level: int, msg: str) -> None:
        # self._logger.log(level, remove_bash_color_str(msg))
        self.__logger.log(level, str(msg))

    def debug(self, msg: str) -> None:
        self.log(logging.DEBUG, msg)

    def info(self, msg: str) -> None:
        self.log(logging.INFO, msg)

    def warning(self, msg: str) -> None:
        self.log(logging.WARNING, msg)

    def error(self, msg: str) -> None:
        self.log(logging.ERROR, msg)

    def critical(self, msg: str) -> None:
        self.log(logging.CRITICAL, msg)

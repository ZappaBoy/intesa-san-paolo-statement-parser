import argparse
import importlib.metadata as metadata
import os
from argparse import Namespace

from isparser.models.log_level import LogLevel
from isparser.shared.utils.logger import Logger

__version__ = metadata.version(__package__ or __name__)


class ISParser:
    def __init__(self):
        self.logger = Logger()
        self.args = self.parse_args()
        self.set_verbosity()

    def run(self):
        self.check_args()
        self.logger.info(f"Running...")
        self.logger.debug(self.args)

    @staticmethod
    def parse_args() -> Namespace:
        parser = argparse.ArgumentParser(description="isparser is a simple parser made to extract and convert the "
                                                     "Intesa San Paolo PDF bank statement to csv.")
        parser.add_argument('--verbose', '-v', action='count', default=1,
                            help='Increase verbosity. Use more than once to increase verbosity level (e.g. -vvv).')
        parser.add_argument('--debug', action='store_true', default=False,
                            help='Enable debug mode.')
        parser.add_argument('--quiet', '-q', action=argparse.BooleanOptionalAction, default=False,
                            required=False, help='Do not print any output/log')
        parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}',
                            help='Show version and exit.')
        parser.add_argument('--file', '-f', action='store', required=True,
                            help='Statement PDF file to use')

        return parser.parse_args()

    def check_args(self) -> None:
        error_message = None
        if self.args.file is None or len(self.args.file) == 0 or not os.path.exists(self.args.file):
            error_message = f"Incorrect input file: {self.args.file}"
        if error_message:
            self.logger.error(error_message)
            exit(1)

    def set_verbosity(self) -> None:
        if self.args.quiet:
            verbosity_level = LogLevel.DISABLED
        else:
            if self.args.debug or self.args.verbose > LogLevel.DEBUG.value:
                verbosity_level = LogLevel.DEBUG
            else:
                verbosity_level = self.args.verbose
        self.logger.set_log_level(verbosity_level)

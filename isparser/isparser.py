import argparse
import importlib.metadata as metadata
import logging
import os
from argparse import Namespace

from isparser.models.log_level import LogLevel
from isparser.shared.utils.logger import Logger

__version__ = metadata.version(__package__ or __name__)

from isparser.statement_parser import StatementParser


class ISParser:
    def __init__(self):
        self.logger = Logger()
        self.args = self.parse_args()
        self.set_verbosity()
        self.statement_parser = StatementParser()

    def run(self):
        self.check_args()
        self.logger.info(f"Running...")
        self.logger.debug(self.args)
        for file in self.args.files:
            self.logger.info(f"Processing file: {file}")
            self.statement_parser.parse(file)
        self.statement_parser.to_csv(self.args.output, split=self.args.split, only_positive=self.args.only_positive)

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
        parser.add_argument('--files', '-f', required=True, action='store',
                            nargs='+', help='Statement PDF file(s) to use')
        parser.add_argument('--output', '-o', required=False, action='store', default='./movements.csv',
                            help='Output CSV file path (Default: ./output.csv)')
        parser.add_argument('--split', '-s', action=argparse.BooleanOptionalAction, required=False,
                            default=False, help=f'Split income and outcome movements in multiple files. Default: False')
        parser.add_argument('--only-positive', '-p', action=argparse.BooleanOptionalAction, required=False,
                            default=False, help=f'If --split is used, convert income and outcome to only positive '
                                                f'numbers. Default: False')
        return parser.parse_args()

    def check_args(self) -> None:
        error_message = ""
        for file in self.args.files:
            if not os.path.exists(file):
                error_message += f"\nIncorrect input file: {file}"
        if error_message != "":
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
        logging.getLogger("pdfminer").setLevel(logging.WARNING)

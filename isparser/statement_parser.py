import re
from datetime import datetime
from typing import Any, Tuple, List

import pandas as pd
import pdfplumber

from isparser.models.movement import Movement
from isparser.shared.exceptions.movement_pages_not_found import MovementPagesNotFoundError
from isparser.shared.utils.logger import Logger

starting_movement_pattern = r'^\d{2}\.\d{2}\.\d{4}\s\d{2}\.\d{2}\.\d{4}.*'
starting_movement_page_pattern = "Dettaglio movimenti del conto corrente"
ending_movement_page_pattern = "Saldo finale al"
income_pattern = "Bonifico a Vostro favore disposto da"


class StatementParser:
    def __init__(self):
        self.logger = Logger()
        self.movements_df = pd.DataFrame(columns=["date", "description", "amount"])

    def parse(self, filepath: str) -> None:
        self.logger.debug(f"Parsing {filepath}")
        with pdfplumber.open(filepath) as pdf:
            movements_starting_page_index, movements_ending_page_index = self.find_movements_pages(pdf)
            for page_index in range(movements_starting_page_index, movements_ending_page_index):
                page_content = pdf.pages[page_index].extract_text()
                movements: List[Movement] = self.extract_movements(page_content)
                self.add_movements(movements)

    def to_csv(self, filepath: str) -> None:
        self.logger.debug(f"Exporting to csv: {filepath}")
        self.movements_df.to_csv(filepath, index=False)

    @staticmethod
    def exists_in_page(page: Any, text: str):
        return len(page.search(text)) > 0

    def find_movements_pages(self, pdf: Any) -> Tuple[int, int]:
        movements_starting_page_index = None
        movements_ending_page_index = None
        for index, page in enumerate(pdf.pages):
            if movements_starting_page_index is None:
                if self.exists_in_page(page, starting_movement_page_pattern) > 0:
                    movements_starting_page_index = index
            if movements_starting_page_index is not None and movements_ending_page_index is None:
                if self.exists_in_page(page, ending_movement_page_pattern) > 0:
                    movements_ending_page_index = index
            if movements_starting_page_index is not None and movements_ending_page_index is not None:
                return movements_starting_page_index, movements_ending_page_index
        raise MovementPagesNotFoundError()

    @staticmethod
    def extract_movements(page_content: str) -> List[Movement]:
        movements: List[Movement] = []
        lines = page_content.splitlines()
        for index, line in enumerate(lines):
            if re.match(starting_movement_pattern, line):
                columns = line.split()
                raw_date = columns[0]
                raw_description = " ".join(columns[2:-1])  # Skip the first two date columns and the last amount column
                raw_amount = columns[-1]

                date = datetime.strptime(raw_date, "%d.%m.%Y")
                description = raw_description

                if len(lines) > index + 1:
                    next_line_exists = True
                    next_line = lines[index + 1]
                    while next_line_exists and re.match(starting_movement_pattern, next_line) is None:
                        description += " " + next_line
                        index += 1
                        if len(lines) <= index + 1:
                            next_line_exists = False
                        else:
                            next_line = lines[index + 1]

                raw_amount = (raw_amount
                              .replace('\x19', '.')  # replace weird dot character
                              .replace(".", "")
                              .replace(",", "."))
                amount = float(raw_amount)
                # TODO: add other income cases
                if income_pattern not in description:
                    amount = -amount
                movement = Movement(date=date, description=description, amount=amount)
                movements.append(movement)
        return movements

    def add_movements(self, movements: List[Movement]) -> None:
        for movement in movements:
            self.movements_df.loc[len(self.movements_df)] = movement.model_dump(mode="json")
        self.movements_df.sort_values(by="date", inplace=True)

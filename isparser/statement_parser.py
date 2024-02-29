import re
from datetime import datetime
from typing import Any, Tuple, List, Dict, Pattern

import pandas as pd
import pdfplumber

from isparser.models.movement import Movement
from isparser.shared.exceptions.movement_pages_not_found import MovementPagesNotFoundError
from isparser.shared.utils.logger import Logger

starting_movement_pattern = r'^\d{2}\.\d{2}\.\d{4}\s\d{2}\.\d{2}\.\d{4}.*'
starting_movement_page_pattern = "Dettaglio movimenti del conto corrente"
ending_movement_page_pattern = "Saldo finale al"
bank_transfer_income_pattern = r"^Bonifico a Vostro favore"
deposit_income_pattern = r"^Versamento"
payment_reversal_income_pattern = r"^Storno Pagamento Pos"

income_patterns = [
    bank_transfer_income_pattern,
    deposit_income_pattern,
    payment_reversal_income_pattern
]

page_index_text_pattern = r"Pagina \d{1,3} di \d{1,3}"
movements_summary_pattern = r"^Totali"
ignore_line_patterns = [
    page_index_text_pattern,
    movements_summary_pattern
]


class StatementParser:
    def __init__(self):
        self.logger = Logger()
        self.movements_df = pd.DataFrame(columns=["date", "amount", "description", "tags"])

    def parse(self, filepath: str, tag_patterns: Dict[str, Pattern] = None) -> None:
        self.logger.debug(f"Parsing {filepath}")
        self.logger.debug(f"Using tag patterns {tag_patterns}")
        # The following check can be improved using python-magic or the file unix command but in this case is probably
        # an overkill
        is_pdf_file = filepath.lower().endswith('.pdf')
        if is_pdf_file:
            self.parse_pdf(filepath, tag_patterns)
        else:
            self.parse_xlsx(filepath, tag_patterns)

    def parse_pdf(self, filepath: str, tag_patterns: Dict[str, Pattern] = None) -> None:
        with pdfplumber.open(filepath) as pdf:
            movements_starting_page_index, movements_ending_page_index = self.find_movements_pages(pdf)
            for page_index in range(movements_starting_page_index, movements_ending_page_index + 1):
                page_content = pdf.pages[page_index].extract_text()
                movements: List[Movement] = self.extract_movements(page_content, tag_patterns)
                self.add_movements(movements)

    def parse_xlsx(self, filepath: str, tag_patterns: Dict[str, Pattern] = None) -> None:
        df = pd.read_excel(filepath, header=None,
                           names=['date', 'operation', 'description', 'account', 'accounted_status', 'category',
                                  'currency', 'amount'])

        df = df[df['date'].apply(isinstance, args=[datetime])]

        movements: List[Movement] = []

        for index, row in df.iterrows():
            amount = row['amount']
            description = row['description']
            date = row['date']
            movement = self.build_movement(date, amount, description, tag_patterns)
            movements.append(movement)

        self.add_movements(movements)

    def to_csv(self, filepath: str, split: bool = False, only_positive: bool = False) -> None:
        self.logger.debug(f"Exporting to csv: {filepath}")
        extension = '.csv'
        filepath = self.check_filepath_extension(filepath, extension)
        self.format_movements()
        if not split:
            self.save_csv(self.movements_df, filepath)
        else:
            income_df, outcome_df = self.get_split_movements(only_positive)
            income_filepath, outcome_filepath = self.get_split_filepaths(filepath, extension)
            self.save_csv(income_df, income_filepath)
            self.save_csv(outcome_df, outcome_filepath)

    def to_json(self, filepath: str, split: bool = False, only_positive: bool = False) -> None:
        self.logger.debug(f"Exporting to json: {filepath}")
        extension = '.json'
        filepath = self.check_filepath_extension(filepath, extension)
        self.format_movements()
        if not split:
            self.save_json(self.movements_df, filepath)
        else:
            income_df, outcome_df = self.get_split_movements(only_positive)
            income_filepath, outcome_filepath = self.get_split_filepaths(filepath, extension)
            self.save_json(income_df, income_filepath)
            self.save_json(outcome_df, outcome_filepath)

    @staticmethod
    def save_csv(df: pd.DataFrame, filepath: str) -> None:
        df.to_csv(filepath, index=False)

    @staticmethod
    def save_json(df: pd.DataFrame, filepath: str) -> None:
        df.to_json(filepath, orient='records', index=False)

    def get_split_movements(self, only_positive) -> Tuple[pd.DataFrame, pd.DataFrame]:
        income_df = self.movements_df[self.movements_df["amount"] > 0]
        outcome_df = self.movements_df[self.movements_df["amount"] < 0]
        if only_positive:
            outcome_df = outcome_df.assign(amount=outcome_df["amount"].abs())
        return income_df, outcome_df

    @staticmethod
    def get_split_filepaths(filepath, extension) -> Tuple[str, str]:
        income_filepath = filepath.replace(extension, f"_income{extension}")
        outcome_filepath = filepath.replace(extension, f"_outcome{extension}")
        return income_filepath, outcome_filepath

    def format_movements(self):
        self.movements_df["tags"] = self.movements_df["tags"].apply(lambda x: "|".join(x))

    @staticmethod
    def check_filepath_extension(filepath, extension) -> str:
        if not filepath.endswith(extension):
            filepath += extension
        return filepath

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

    def extract_movements(self, page_content: str, tag_patterns: Dict[str, Pattern] = None) -> List[Movement]:
        movements: List[Movement] = []
        lines = page_content.splitlines()
        for index, line in enumerate(lines):
            if re.match(starting_movement_pattern, line):
                columns = line.split()
                raw_date = columns[0]
                raw_description = " ".join(columns[2:-1])  # Skip the first two date columns and the last amount column
                amount = columns[-1]

                date = self.format_date(raw_date)
                description = raw_description.replace("*", "").strip()

                if len(lines) > index + 1:
                    next_line_exists = True
                    next_line = lines[index + 1]
                    while (next_line_exists and re.match(starting_movement_pattern, next_line) is None
                           and not self.is_line_to_ignore(next_line)):
                        description += " " + next_line
                        index += 1
                        if len(lines) <= index + 1:
                            next_line_exists = False
                        else:
                            next_line = lines[index + 1]
                movement = self.build_movement(date, amount, description, tag_patterns)
                movements.append(movement)
        return movements

    def build_movement(self, date, amount, description, tag_patterns):
        amount = self.format_amount(str(amount), description)
        tags = self.extract_tags(description, tag_patterns)
        return Movement(date=date, amount=amount, description=description, tags=tags)

    @staticmethod
    def format_date(raw_date: str) -> datetime:
        return datetime.strptime(raw_date, "%d.%m.%Y")

    @staticmethod
    def format_amount(raw_amount: str, description: str) -> float:
        raw_amount = (raw_amount
                      .replace('\x19', '.')  # replace weird dot character
                      .replace(".", "")
                      .replace(",", "."))
        amount = float(raw_amount)
        # TODO: add other income cases
        income_amount = False
        for income_pattern in income_patterns:
            if re.match(income_pattern, description) is not None:
                income_amount = True
                break
        if not income_amount:
            amount = -amount
        return amount

    @staticmethod
    def extract_tags(description: str, tag_patterns: Dict[str, Pattern] = None) -> List[str]:
        tags = []
        if tag_patterns is not None:
            for tag_name, tag_pattern in tag_patterns.items():
                if re.match(tag_pattern, description) is not None:
                    tags.append(tag_name)
        return tags

    def add_movements(self, movements: List[Movement]) -> None:
        for movement in movements:
            self.movements_df.loc[len(self.movements_df)] = movement.model_dump(mode="json")
        self.movements_df.sort_values(by="date", inplace=True)

    @staticmethod
    def is_line_to_ignore(line: str) -> bool:
        for ignore_line_pattern in ignore_line_patterns:
            if re.match(ignore_line_pattern, line) is not None:
                return True
        return False

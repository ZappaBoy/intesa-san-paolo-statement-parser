from datetime import date
from typing import List

from isparser.models.custom_base_model import CustomBaseModel


class Movement(CustomBaseModel):
    date: date
    description: str
    amount: float
    tags: List[str] = []

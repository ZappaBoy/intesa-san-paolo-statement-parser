from datetime import date

from isparser.models.custom_base_model import CustomBaseModel


class Movement(CustomBaseModel):
    date: date
    description: str
    amount: float

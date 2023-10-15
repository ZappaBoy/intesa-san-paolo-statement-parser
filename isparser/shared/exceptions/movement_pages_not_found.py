class MovementPagesNotFoundError(Exception):
    def __init__(self):
        super().__init__("Movement pages not found")

# handlers/__init__.py
from .pet_handler import PetHandler
from .bank_handler import BankHandler
from .casino_handler import CasinoHandler
from .transfer_handler import TransferHandler
from .fishing_handler import FishingHandler
from .meow_handler import MeowHandler
from .fridge_handler import FridgeHandler

__all__ = [
    'PetHandler',
    'BankHandler',
    'CasinoHandler',
    'TransferHandler',
    'FishingHandler',
    'MeowHandler',
    'FridgeHandler'
]
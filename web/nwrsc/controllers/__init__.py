""" Present blueprints to outside but force import of other modules that link via decorators """

from .blueprints import *
from .live import live_background_thread

__all__ = [x for x in dir(blueprints) if "__" not in x] + ["live_background_thread"]

from . import admin
from . import api
from . import docs
from . import dynamic
from . import entranteditor
from . import live
from . import payments
from . import register
from . import results

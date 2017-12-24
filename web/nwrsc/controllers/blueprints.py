"""
    Store all blueprints in one place so its easy to import and move pieces around
"""

from flask import Blueprint

Admin     = Blueprint("Admin",     __name__)
Announcer = Blueprint("Announcer", __name__) 
Xml       = Blueprint("Xml",       __name__)
Json      = Blueprint("Json",      __name__) 
Register  = Blueprint("Register",  __name__) 
Results   = Blueprint("Results",   __name__)


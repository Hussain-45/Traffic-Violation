# Forward all imports to the backend/app/models/ package
# to prevent duplicate model definition conflicts between models.py and models/ directory.
from backend.app.models.__init__ import *

import sys
import os

# Add parent directory to path so we can import backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel expects a variable called 'app' or 'application'
application = app
handler = app

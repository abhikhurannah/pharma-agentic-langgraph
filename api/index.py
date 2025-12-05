from mangum import Mangum
import sys
import os

# Add parent directory to path so we can import backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

# Vercel expects a handler that works with AWS Lambda format
handler = Mangum(app, lifespan="off")

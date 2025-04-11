import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.config import DEEPSEEK_API_KEY

print(DEEPSEEK_API_KEY)


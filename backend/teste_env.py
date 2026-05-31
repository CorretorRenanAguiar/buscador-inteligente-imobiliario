from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / ".env"

print("\n==============================")
print("TESTE .ENV")
print("==============================")

print("BASE_DIR:")
print(BASE_DIR)

print("\nENV_PATH:")
print(ENV_PATH)

print("\nARQUIVO EXISTE?")
print(ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

print("\nSUPABASE_URL:")
print(os.getenv("SUPABASE_URL"))

print("\nSUPABASE_KEY EXISTE?")
print(bool(os.getenv("SUPABASE_KEY")))

print("\nNUMERO_CORRETOR:")
print(os.getenv("NUMERO_CORRETOR"))

print("\n==============================")

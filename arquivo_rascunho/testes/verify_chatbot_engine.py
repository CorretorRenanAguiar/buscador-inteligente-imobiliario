import subprocess
import sys
import py_compile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHATBOT_PATH = BASE_DIR / "chatbot_engine.py"


def run_py_compile(path: Path) -> None:
    print(f"Verificando sintaxe: {path}")
    py_compile.compile(str(path), doraise=True)
    print("✔ python -m py_compile ok")


def run_black_check(path: Path) -> None:
    print(f"Verificando formatação com black: {path}")
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("black check falhou")
    print("✔ black --check ok")


if __name__ == "__main__":
    try:
        run_py_compile(CHATBOT_PATH)
        run_black_check(CHATBOT_PATH)
    except Exception as exc:
        print(f"Falha na verificação: {exc}")
        sys.exit(1)
    print("Verificação concluída com sucesso.")

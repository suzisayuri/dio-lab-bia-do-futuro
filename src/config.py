from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"

AGENTE_NOME = "Bússola"

# Descrições recorrentes tratadas como gasto discricionário (cortável) nos cálculos.
GASTOS_CORTAVEIS = {"Academia", "Netflix", "Assinatura Figma"}

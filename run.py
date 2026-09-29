import uvicorn
import os

if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando HashBack DApp - Blockchain Local de Fidelidade")
    print("Interface Web disponivel em: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

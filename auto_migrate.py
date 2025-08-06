# auto_migrate.py
from flask_migrate import upgrade
from app import app, db

with app.app_context():
    try:
        print("🔁 Aplicando migrações...")
        upgrade()
        print("✅ Migrações aplicadas com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao aplicar migrações: {e}")

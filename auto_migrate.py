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
from models import User

# Criar usuário admin se ainda não existir
existing_user = User.query.filter_by(username="admin").first()
if not existing_user:
    novo = User(username="admin")
    novo.set_password("admin@2025")
    db.session.add(novo)
    db.session.commit()
    print("✅ Usuário 'admin' criado automaticamente.")
else:
    print("⚠️ Usuário 'admin' já existe.")

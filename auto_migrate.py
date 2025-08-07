# auto_migrate.py

from flask_migrate import upgrade
from app import app, db  # <-- ESSENCIAL: certifique-se que 'app' e 'db' vêm do seu app Flask

with app.app_context():
    try:
        print("🔁 Aplicando migrações...")
        upgrade()
        print("✅ Migrações aplicadas com sucesso.")

        from models import User  # ou o caminho correto para o seu modelo

        # Criar usuário admin se não existir
        if not User.query.filter_by(username="admin").first():
            user = User(username="admin")
            user.set_password("admin@2025")
            db.session.add(user)
            db.session.commit()
            print("✅ Usuário admin criado com sucesso.")
        else:
            print("ℹ️ Usuário admin já existe.")
    except Exception as e:
        print(f"❌ Erro: {e}")

from app import app, db
from models import User
from flask_migrate import upgrade

print("🔁 Aplicando migrações...")
with app.app_context():
    upgrade()
    print("✅ Migrações aplicadas com sucesso.")

    # Criar usuário admin se não existir
    if not User.query.filter_by(username="admin").first():
        user = User(username="admin")
        user.set_password("admin@2025")
        db.session.add(user)
        db.session.commit()
        print("✅ Usuário admin criado com sucesso.")
    else:
        print("ℹ️ Usuário admin já existe.")

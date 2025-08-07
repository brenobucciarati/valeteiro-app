from app import app, db
from models import User  # ou de onde estiver o seu modelo User
from flask_migrate import upgrade

print("🔁 Aplicando migrações...")
with app.app_context():
    upgrade()
    print("✅ Migrações aplicadas com sucesso.")

    # Criar usuário admin se não existir
    existing_user = User.query.filter_by(username="admin").first()
    if not existing_user:
        user = User(username="admin")
        user.set_password("admin@2025")  # ajuste para sua lógica de senha
        db.session.add(user)
        db.session.commit()
        print("✅ Usuário admin criado.")
    else:
        print("ℹ️ Usuário admin já existe.")

from app import app, db
from models import User
from flask_migrate import upgrade

print("🔁 Aplicando migrações...")
with app.app_context():
    upgrade()
    print("✅ Migrações aplicadas com sucesso.")

    # Criar ou atualizar usuário admin
    user = User.query.filter_by(username="admin").first()
    if not user:
        user = User(username="admin")
        print("🆕 Criando usuário admin...")
    else:
        print("✏️ Atualizando senha do admin...")

    user.set_password("admin@2025")  # força a senha correta
    db.session.add(user)
    db.session.commit()

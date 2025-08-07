from app import app, db
from models import User
from flask_migrate import upgrade, downgrade
from alembic.config import Config

print("🔁 Aplicando migrações...")

with app.app_context():
    alembic_cfg = Config("migrations/alembic.ini")

    print("🔄 Realizando downgrade...")
    downgrade(alembic_cfg, 'base')  # desfaz tudo

    print("🔼 Reaplicando upgrade...")
    upgrade()

    print("✅ Migrações aplicadas com sucesso.")

    # Criar ou atualizar usuário admin
    user = User.query.filter_by(username="admin").first()
    if not user:
        user = User(username="admin")
        print("🆕 Criando usuário admin...")
    else:
        print("✏️ Atualizando senha do admin...")

    user.set_password("admin@2025")  # senha segura com hash
    db.session.add(user)
    db.session.commit()
    print("🔐 Senha do admin definida com sucesso.")

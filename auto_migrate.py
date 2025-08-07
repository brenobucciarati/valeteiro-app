from app import app, db
from models import User
from flask_migrate import upgrade, downgrade
import os
from alembic.config import Config

print("🔁 Aplicando migrações...")

with app.app_context():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))  # ou SQLite local

    print("🔄 Realizando downgrade...")
    downgrade(alembic_cfg, 'base')

    print("⬆️ Realizando upgrade...")
    upgrade(alembic_cfg)

    print("✅ Migrações aplicadas com sucesso.")

    # Criação/atualização do admin
    user = User.query.filter_by(username="admin").first()
    if not user:
        user = User(username="admin")
        print("🆕 Criando usuário admin...")
    else:
        print("✏️ Atualizando senha do admin...")

    user.set_password("admin@2025")
    db.session.add(user)
    db.session.commit()

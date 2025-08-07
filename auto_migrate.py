from app import app, db
from models import User
from flask_migrate import upgrade, downgrade
from alembic.config import Config
import os

print("🔁 Aplicando migrações...")

# Caminho absoluto do alembic.ini
base_dir = os.path.abspath(os.path.dirname(__file__))
alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))

with app.app_context():
    print("🔄 Realizando downgrade...")
    downgrade(alembic_cfg, 'base')  # volta ao início

    print("🔼 Realizando upgrade...")
    upgrade(alembic_cfg)

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


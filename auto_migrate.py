from app import app, db
from models import User
from flask_migrate import upgrade

with app.app_context():
    print("🔁 Aplicando migrações...")
    print("📦 Usando banco de dados:", app.config["SQLALCHEMY_DATABASE_URI"])  # <-- DEBUG CRUCIAL

    upgrade()
    print("✅ Migrações aplicadas com sucesso.")

    existing_user = User.query.filter_by(username="admin").first()
    if not existing_user:
        user = User(username="admin")
        user.set_password("admin@2025")
        db.session.add(user)
        db.session.commit()
        print("✅ Usuário admin criado.")
    else:
        print("ℹ️ Usuário admin já existe.")

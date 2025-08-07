from app import app
from models import db, User

with app.app_context():
    existing_user = User.query.filter_by(username="admin").first()
    if existing_user:
        print("⚠️ Usuário 'admin' já existe.")
    else:
        novo = User(username="admin")
        novo.set_password("admin@2025")
        db.session.add(novo)
        db.session.commit()
        print("✅ Usuário 'admin' criado com sucesso.")

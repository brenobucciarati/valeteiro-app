from app import app
from models import db, User

with app.app_context():
    if not User.query.filter_by(username="admin").first():
        novo = User(username="admin")
        novo.set_password("admin@2025")
        db.session.add(novo)
        db.session.commit()
        print("✅ Usuário 'admin' criado com sucesso.")
    else:
        print("⚠️ Usuário 'admin' já existe.")

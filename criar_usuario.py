from app import app
from models import db, User

with app.app_context():
    novo = User(username="admin")
    novo.set_password("admin@2026")  # 🔐 Escolha uma senha forte
    db.session.add(novo)
    db.session.commit()
    print("Usuário criado com sucesso.")


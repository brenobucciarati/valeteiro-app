with app.app_context():
    try:
        print("🔁 Aplicando migrações...")
        upgrade()
        print("✅ Migrações aplicadas com sucesso.")

        from models import User  # certifique-se de importar aqui dentro do contexto

        # Criar usuário admin se não existir
        if not User.query.filter_by(username="admin").first():
            user = User(username="admin")
            user.set_password("admin@2025")
            db.session.add(user)
            db.session.commit()
            print("✅ Usuário admin criado com sucesso.")
        else:
            print("ℹ️ Usuário admin já existe.")
    except Exception as e:
        print(f"❌ Erro: {e}")

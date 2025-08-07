import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Usa PostgreSQL no Render ou SQLite localmente
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'inspecaovaleteiro_frota.db')
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'minhasecret')


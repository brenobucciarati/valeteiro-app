from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    id = db.Column(db.Integer, primary_key=True)
    numero_frota = db.Column(db.Integer, nullable=False, unique=True)
    tipo_frota = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='ativo')

class Programacao(db.Model):
    __tablename__ = 'programacoes'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'), nullable=False)
    compareceu = db.Column(db.Boolean, nullable=True, default=None)
    remarcado_para = db.Column(db.Date, nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    motivo_classificado = db.Column(db.String(50), nullable=True)
    habilitado_para_vistoria = db.Column(db.Boolean, default=False)

    veiculo = db.relationship("Veiculo", backref="programacoes")

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

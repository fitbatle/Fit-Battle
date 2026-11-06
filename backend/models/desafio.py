from database import db
from models.base import ModeloBase


class Desafio(ModeloBase):
    __tablename__ = "desafio"

    id_desafio = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.String(500))
    exercicio = db.Column(db.String(120))
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    recompensa_xp = db.Column(db.Integer, nullable=False, default=0)
    tipo_metrica = db.Column(db.String(12), nullable=False, default="treinos")
    valor_objetivo = db.Column(db.Numeric(8, 2), nullable=False, default=1)

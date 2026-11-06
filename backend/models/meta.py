from database import db
from models.base import ModeloBase


class Meta(ModeloBase):
    __tablename__ = "meta"

    id_meta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    descricao = db.Column(db.String(300), nullable=False)
    tipo = db.Column(db.String(12), nullable=False, default="curto_prazo")
    tipo_metrica = db.Column(db.String(12), nullable=False)
    exercicio = db.Column(db.String(120))
    valor_objetivo = db.Column(db.Numeric(8, 2), nullable=False)
    valor_partida = db.Column(db.Numeric(8, 2))
    data_inicio = db.Column(db.Date, nullable=False)
    data_final = db.Column(db.Date)
    status = db.Column(db.String(12), nullable=False, default="em_andamento")
    concluida_em = db.Column(db.DateTime)

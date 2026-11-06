from database import db
from models.base import ModeloBase
from utils import agora, iso_utc


class Compartilhamento(ModeloBase):
    __tablename__ = "compartilhamento"

    id_comp = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_conteudo = db.Column(db.String(10), nullable=False)
    id_atividade = db.Column(
        db.Integer,
        db.ForeignKey("atividade.id_atividade", ondelete="SET NULL"),
    )
    id_meta = db.Column(
        db.Integer,
        db.ForeignKey("meta.id_meta", ondelete="SET NULL"),
    )
    chave_medalha = db.Column(db.String(40))
    rede_social = db.Column(db.String(40))
    data_comp = db.Column(db.DateTime, nullable=False, default=agora)

    @staticmethod
    def formatar(c):
        return {
            "id": c["id_comp"],
            "id_usuario": c["id_usuario"],
            "tipo_conteudo": c["tipo_conteudo"],
            "id_atividade": c["id_atividade"],
            "id_meta": c["id_meta"],
            "chave_medalha": c["chave_medalha"],
            "rede_social": c["rede_social"],
            "data_comp": iso_utc(c["data_comp"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())

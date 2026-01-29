"""
Immagine model (read-only).
"""
from sqlalchemy import Column, Integer, String, ForeignKey

from app.database import Base


class Immagine(Base):
    """
    Immagine model - READ ONLY.
    From dbimmobiligb-staging.immagini
    """
    __tablename__ = "immagini"

    id = Column(Integer, primary_key=True)
    id_immobile = Column(Integer, ForeignKey('immobilpostgres.id'))
    url = Column(String(500))
    ordine = Column(Integer, default=0)

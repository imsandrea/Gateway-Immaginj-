"""
Immobile model (read-only, subset of fields).
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ARRAY
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Immobile(Base):
    """
    Immobile model - READ ONLY.
    Subset of fields from dbimmobiligb-staging.immobilpostgres
    """
    __tablename__ = "immobilpostgres"

    id = Column(Integer, primary_key=True)
    codice_dam = Column(String(50))
    titolo = Column(String(200))
    tipo_immobile = Column(String(100))
    descrizione_web_breve_it = Column(Text)
    descrizione_web_estesa_it = Column(Text)

    # Location
    comune = Column(String(100))
    localita = Column(String(100))
    via = Column(String(200))
    posizione_lat = Column(Float)
    posizione_long = Column(Float)

    # Caratteristiche
    mq_commerciali = Column(Float)
    camere_da_letto = Column(Integer)
    bagni = Column(Integer)

    # Pricing
    prezzo_vendita = Column(Float)

    # Images (legacy field)
    immagini_600 = Column(Text)

    # AI Features
    features_ai = Column(JSONB)

    # Privacy flags
    is_attivo = Column(Boolean)
    is_ufficiale = Column(Boolean)
    is_riservato_direzione = Column(Boolean)

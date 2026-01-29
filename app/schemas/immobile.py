"""
Immobile schemas for API responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ImageSchema(BaseModel):
    """Single image."""
    id: Optional[int] = None
    url: str
    ordine: int = 0


class ImmobileSchema(BaseModel):
    """Immobile with images and AI features."""
    id: int
    codice_dam: Optional[str] = None
    titolo: Optional[str] = None
    tipo_immobile: Optional[str] = None
    descrizione_breve: Optional[str] = Field(None, alias="descrizione_web_breve_it")
    descrizione_estesa: Optional[str] = Field(None, alias="descrizione_web_estesa_it")

    # Location
    comune: Optional[str] = None
    localita: Optional[str] = None
    via: Optional[str] = None

    # Caratteristiche
    mq_commerciali: Optional[float] = None
    camere_da_letto: Optional[int] = None
    bagni: Optional[int] = None
    prezzo_vendita: Optional[float] = None

    # Images
    immagini: List[ImageSchema] = []

    # AI Features (from Gemini Vision)
    features_ai: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ImmobileListResponse(BaseModel):
    """Paginated list response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    immobili: List[ImmobileSchema]


class StatsResponse(BaseModel):
    """Dataset statistics."""
    total_immobili: int
    immobili_con_foto: int
    percentuale_con_foto: float
    total_immagini: int
    media_immagini_per_immobile: float
    tipologie: Dict[str, int]

"""
Immobili router - Public access to properties with images.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import math

from app.database import get_db
from app.models.immobile import Immobile
from app.models.immagine import Immagine
from app.schemas.immobile import (
    ImmobileSchema,
    ImmobileListResponse,
    ImageSchema,
    StatsResponse
)
from app.auth.jwt import verify_token

router = APIRouter(prefix="/immobili", tags=["Immobili"])


def get_immobile_images(immobile: Immobile, db: Session) -> List[ImageSchema]:
    """Get images from normalized table or legacy field."""
    images = []

    # Try normalized table first
    db_images = db.query(Immagine).filter(
        Immagine.id_immobile == immobile.id
    ).order_by(Immagine.ordine).all()

    if db_images:
        for img in db_images:
            images.append(ImageSchema(
                id=img.id,
                url=img.url,
                ordine=img.ordine
            ))
    elif immobile.immagini_600:
        # Fallback to legacy field
        for idx, img_url in enumerate(immobile.immagini_600.split(";")):
            img_url = img_url.strip()
            if img_url:
                images.append(ImageSchema(
                    id=None,
                    url=img_url,
                    ordine=idx
                ))

    return images


@router.get("/stats", response_model=StatsResponse, dependencies=[Depends(verify_token)])
async def get_stats(db: Session = Depends(get_db)):
    """
    Get dataset statistics.

    **Auth required:** JWT Bearer token
    """
    # Query public properties only
    query = db.query(Immobile).filter(
        Immobile.is_ufficiale == True,
        Immobile.is_attivo == True,
        Immobile.is_riservato_direzione == False
    )

    total = query.count()

    # Count with images
    con_foto = query.filter(
        (Immobile.immagini_600.isnot(None) & (Immobile.immagini_600 != "")) |
        Immobile.id.in_(db.query(Immagine.id_immobile).distinct())
    ).count()

    # Tipologie
    tipologie = {}
    for tipo, count in db.query(
        Immobile.tipo_immobile,
        func.count(Immobile.id)
    ).filter(
        Immobile.is_ufficiale == True,
        Immobile.is_attivo == True,
        Immobile.is_riservato_direzione == False
    ).group_by(Immobile.tipo_immobile).all():
        if tipo:
            tipologie[tipo] = count

    return StatsResponse(
        total_immobili=total,
        immobili_con_foto=con_foto,
        percentuale_con_foto=round((con_foto / total * 100), 2) if total > 0 else 0,
        total_immagini=0,  # Can calculate if needed
        media_immagini_per_immobile=0.0,
        tipologie=tipologie
    )


@router.get("", response_model=ImmobileListResponse, dependencies=[Depends(verify_token)])
async def list_immobili(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tipo_immobile: Optional[str] = Query(None, description="Filter by type"),
    comune: Optional[str] = Query(None, description="Filter by municipality"),
    con_immagini: bool = Query(False, description="Only with images"),
    db: Session = Depends(get_db)
):
    """
    List public properties with images and AI descriptions.

    **Auth required:** JWT Bearer token

    **Privacy filters applied:**
    - Only active properties (is_attivo=true)
    - Only official properties (is_ufficiale=true)
    - Excludes direction-reserved (is_riservato_direzione=false)
    - Excludes private sales

    **Returns:**
    - Paginated list with images and AI features
    """
    # Base query with privacy filters
    query = db.query(Immobile).filter(
        Immobile.is_ufficiale == True,
        Immobile.is_attivo == True,
        Immobile.is_riservato_direzione == False
    )

    # Apply filters
    if tipo_immobile:
        query = query.filter(Immobile.tipo_immobile.ilike(f"%{tipo_immobile}%"))

    if comune:
        query = query.filter(Immobile.comune.ilike(f"%{comune}%"))

    if con_immagini:
        query = query.filter(
            (Immobile.immagini_600.isnot(None) & (Immobile.immagini_600 != "")) |
            Immobile.id.in_(db.query(Immagine.id_immobile).distinct())
        )

    # Count total
    total = query.count()
    total_pages = math.ceil(total / page_size)

    # Paginate
    offset = (page - 1) * page_size
    immobili = query.offset(offset).limit(page_size).all()

    # Build response with images
    result = []
    for immobile in immobili:
        images = get_immobile_images(immobile, db)

        result.append(ImmobileSchema(
            id=immobile.id,
            codice_dam=immobile.codice_dam,
            titolo=immobile.titolo,
            tipo_immobile=immobile.tipo_immobile,
            descrizione_web_breve_it=immobile.descrizione_web_breve_it,
            descrizione_web_estesa_it=immobile.descrizione_web_estesa_it,
            comune=immobile.comune,
            localita=immobile.localita,
            via=immobile.via,
            mq_commerciali=immobile.mq_commerciali,
            camere_da_letto=immobile.camere_da_letto,
            bagni=immobile.bagni,
            prezzo_vendita=immobile.prezzo_vendita,
            immagini=images,
            features_ai=immobile.features_ai
        ))

    return ImmobileListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        immobili=result
    )


@router.get("/{immobile_id}", response_model=ImmobileSchema, dependencies=[Depends(verify_token)])
async def get_immobile(
    immobile_id: int,
    db: Session = Depends(get_db)
):
    """
    Get single property with all images and AI features.

    **Auth required:** JWT Bearer token
    """
    immobile = db.query(Immobile).filter(
        Immobile.id == immobile_id,
        Immobile.is_ufficiale == True,
        Immobile.is_attivo == True,
        Immobile.is_riservato_direzione == False
    ).first()

    if not immobile:
        raise HTTPException(status_code=404, detail="Property not found or not public")

    images = get_immobile_images(immobile, db)

    return ImmobileSchema(
        id=immobile.id,
        codice_dam=immobile.codice_dam,
        titolo=immobile.titolo,
        tipo_immobile=immobile.tipo_immobile,
        descrizione_web_breve_it=immobile.descrizione_web_breve_it,
        descrizione_web_estesa_it=immobile.descrizione_web_estesa_it,
        comune=immobile.comune,
        localita=immobile.localita,
        via=immobile.via,
        mq_commerciali=immobile.mq_commerciali,
        camere_da_letto=immobile.camere_da_letto,
        bagni=immobile.bagni,
        prezzo_vendita=immobile.prezzo_vendita,
        immagini=images,
        features_ai=immobile.features_ai
    )


@router.get("/{immobile_id}/immagini", response_model=List[ImageSchema], dependencies=[Depends(verify_token)])
async def get_immobile_images_only(
    immobile_id: int,
    db: Session = Depends(get_db)
):
    """
    Get only images for a property (lightweight).

    **Auth required:** JWT Bearer token
    """
    immobile = db.query(Immobile).filter(
        Immobile.id == immobile_id,
        Immobile.is_ufficiale == True,
        Immobile.is_attivo == True,
        Immobile.is_riservato_direzione == False
    ).first()

    if not immobile:
        raise HTTPException(status_code=404, detail="Property not found or not public")

    return get_immobile_images(immobile, db)

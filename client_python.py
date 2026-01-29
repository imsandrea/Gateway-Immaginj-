"""
Image Gateway Client
====================
Client per accedere all'API Immobili con immagini e generare embeddings.

Uso:
    from image_gateway import ImageGateway

    gateway = ImageGateway()

    # Lista immobili con immagini
    immobili = gateway.get_immobili(con_immagini=True, page_size=50)

    # Cerca immagini per query testuale
    results = gateway.search_images("villa con piscina vista mare")
"""
import os
import json
import httpx
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

# Configurazione API
API_BASE_URL = os.getenv("IMAGE_API_URL", "http://85.215.222.63:8002/api/v1")
API_USERNAME = os.getenv("IMAGE_API_USER", "public_api")
API_PASSWORD = os.getenv("IMAGE_API_PASS", "WyaJrRCUC0dyC//pLVM3Qmdvj+wIDM/M")

# Cache per token e embeddings
CACHE_DIR = Path(__file__).parent / "cache" / "images"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ImageGateway:
    """Client per l'API Immobili con immagini."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or API_BASE_URL
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._client = httpx.Client(timeout=30.0)
        self._embeddings_cache: Dict[str, np.ndarray] = {}
        self._model = None

    def _get_token(self) -> str:
        """Ottieni o rinnova token JWT."""
        if self._token and self._token_expires and datetime.now() < self._token_expires:
            return self._token

        response = self._client.post(
            f"{self.base_url}/auth/login",
            json={"username": API_USERNAME, "password": API_PASSWORD}
        )
        response.raise_for_status()
        data = response.json()

        self._token = data["access_token"]
        self._token_expires = datetime.now() + timedelta(seconds=data.get("expires_in", 604800) - 3600)

        return self._token

    def _headers(self) -> dict:
        """Headers con autenticazione."""
        return {"Authorization": f"Bearer {self._get_token()}"}

    def get_stats(self) -> dict:
        """Statistiche dataset."""
        response = self._client.get(
            f"{self.base_url}/immobili/stats",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_immobili(
        self,
        page: int = 1,
        page_size: int = 20,
        con_immagini: bool = True,
        tipo_immobile: str = None,
        comune: str = None
    ) -> Dict[str, Any]:
        """Lista immobili con filtri."""
        params = {
            "page": page,
            "page_size": page_size,
            "con_immagini": str(con_immagini).lower()
        }
        if tipo_immobile:
            params["tipo_immobile"] = tipo_immobile
        if comune:
            params["comune"] = comune

        response = self._client.get(
            f"{self.base_url}/immobili",
            params=params,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_immobile(self, immobile_id: int) -> dict:
        """Dettaglio singolo immobile."""
        response = self._client.get(
            f"{self.base_url}/immobili/{immobile_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_all_immobili(self, con_immagini: bool = True) -> List[dict]:
        """Fetch tutti gli immobili (paginazione automatica)."""
        all_immobili = []
        page = 1

        while True:
            data = self.get_immobili(page=page, page_size=100, con_immagini=con_immagini)
            immobili = data.get("immobili", [])

            if not immobili:
                break

            all_immobili.extend(immobili)

            if len(immobili) < 100:
                break

            page += 1

        return all_immobili

    def _load_clip_model(self):
        """Carica modello CLIP per embeddings."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('clip-ViT-B-32')
                print("Modello CLIP caricato")
            except ImportError:
                raise ImportError("Installa sentence-transformers: pip install sentence-transformers")
        return self._model

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Genera embedding per testo con CLIP."""
        model = self._load_clip_model()
        return model.encode(text, convert_to_numpy=True)

    def generate_image_embedding(self, image_url: str) -> np.ndarray:
        """Genera embedding per immagine con CLIP."""
        from PIL import Image
        from io import BytesIO

        # Check cache
        cache_key = image_url.split("/")[-1]
        cache_file = CACHE_DIR / f"{cache_key}.npy"

        if cache_file.exists():
            return np.load(cache_file)

        # Download image
        response = self._client.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        # Generate embedding
        model = self._load_clip_model()
        embedding = model.encode(image, convert_to_numpy=True)

        # Cache
        np.save(cache_file, embedding)

        return embedding

    def build_embeddings_index(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Costruisce indice embeddings per tutte le immagini.
        Usa le descrizioni AI come testo (più veloce) o le immagini stesse.

        Returns:
            Dict con:
            - embeddings: np.array (N, dim)
            - metadata: List[dict] con info per ogni embedding
        """
        index_file = CACHE_DIR / "embeddings_index.json"
        embeddings_file = CACHE_DIR / "embeddings.npy"

        if not force_rebuild and index_file.exists() and embeddings_file.exists():
            print("Caricando indice esistente...")
            with open(index_file) as f:
                metadata = json.load(f)
            embeddings = np.load(embeddings_file)
            return {"embeddings": embeddings, "metadata": metadata}

        print("Costruendo indice embeddings...")
        immobili = self.get_all_immobili(con_immagini=True)

        embeddings_list = []
        metadata = []

        for idx, immobile in enumerate(immobili):
            print(f"\r[{idx+1}/{len(immobili)}] {immobile.get('titolo', 'N/A')[:40]}...", end="")

            features_ai = immobile.get("features_ai", {})
            descrizione_visuale = features_ai.get("descrizione_visuale_completa", "")

            if not descrizione_visuale:
                continue

            # Genera embedding dalla descrizione visuale (text embedding)
            embedding = self.generate_text_embedding(descrizione_visuale[:2000])
            embeddings_list.append(embedding)

            # Salva metadata
            metadata.append({
                "immobile_id": immobile.get("id"),
                "titolo": immobile.get("titolo"),
                "tipo": immobile.get("tipo_immobile"),
                "comune": immobile.get("comune"),
                "prezzo": immobile.get("prezzo_vendita"),
                "immagini": [img.get("url") for img in immobile.get("immagini", [])[:5]],
                "features": {
                    "vista_mare": features_ai.get("vista_mare"),
                    "piscina": features_ai.get("piscina_privata"),
                    "stile": features_ai.get("stile"),
                    "landmarks": features_ai.get("landmarks_visibili", [])
                }
            })

        print("\nSalvando indice...")
        embeddings_array = np.array(embeddings_list)
        np.save(embeddings_file, embeddings_array)

        with open(index_file, "w") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"Indice creato: {len(metadata)} immobili")
        return {"embeddings": embeddings_array, "metadata": metadata}

    def search_images(
        self,
        query: str,
        top_k: int = 5,
        filters: dict = None
    ) -> List[Dict[str, Any]]:
        """
        Cerca immagini per query testuale.

        Args:
            query: Testo di ricerca (es. "villa con piscina vista mare")
            top_k: Numero risultati
            filters: Filtri opzionali (tipo, comune, prezzo_max)

        Returns:
            Lista di risultati con score e metadata
        """
        # Carica o costruisci indice
        index = self.build_embeddings_index()
        embeddings = index["embeddings"]
        metadata = index["metadata"]

        # Genera embedding query
        query_embedding = self.generate_text_embedding(query)

        # Calcola similarità coseno
        similarities = np.dot(embeddings, query_embedding) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Applica filtri
        if filters:
            mask = np.ones(len(metadata), dtype=bool)

            if "tipo" in filters:
                mask &= np.array([filters["tipo"].lower() in m.get("tipo", "").lower() for m in metadata])

            if "comune" in filters:
                mask &= np.array([filters["comune"].lower() in m.get("comune", "").lower() for m in metadata])

            if "prezzo_max" in filters:
                mask &= np.array([
                    (m.get("prezzo") or float("inf")) <= filters["prezzo_max"]
                    for m in metadata
                ])

            similarities = np.where(mask, similarities, -1)

        # Top-K
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] < 0:
                continue

            result = metadata[idx].copy()
            result["score"] = float(similarities[idx])
            results.append(result)

        return results

    def find_images_for_article(
        self,
        article_title: str,
        article_content: str,
        num_images: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Trova le immagini migliori per un articolo.

        Args:
            article_title: Titolo articolo
            article_content: Contenuto articolo (o abstract)
            num_images: Numero immagini da trovare

        Returns:
            Lista immagini con score e URL
        """
        # Combina titolo e contenuto per query
        query = f"{article_title}. {article_content[:500]}"

        results = self.search_images(query, top_k=num_images * 2)

        # Diversifica per immobile (non tutte foto stesso immobile)
        seen_immobili = set()
        diverse_results = []

        for r in results:
            immobile_id = r.get("immobile_id")
            if immobile_id not in seen_immobili:
                diverse_results.append(r)
                seen_immobili.add(immobile_id)

            if len(diverse_results) >= num_images:
                break

        return diverse_results

    def close(self):
        """Chiudi client HTTP."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ============ CLI ============

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Image Gateway CLI")
    parser.add_argument("command", choices=["stats", "list", "search", "build-index"])
    parser.add_argument("--query", "-q", help="Query di ricerca")
    parser.add_argument("--top", "-k", type=int, default=5, help="Numero risultati")
    parser.add_argument("--tipo", help="Filtro tipo immobile")
    parser.add_argument("--comune", help="Filtro comune")

    args = parser.parse_args()

    with ImageGateway() as gateway:
        if args.command == "stats":
            stats = gateway.get_stats()
            print(json.dumps(stats, indent=2))

        elif args.command == "list":
            data = gateway.get_immobili(page_size=10)
            for imm in data.get("immobili", []):
                print(f"[{imm['id']}] {imm['titolo']} - {imm['comune']} ({len(imm.get('immagini', []))} foto)")

        elif args.command == "search":
            if not args.query:
                print("Specifica --query")
                exit(1)

            filters = {}
            if args.tipo:
                filters["tipo"] = args.tipo
            if args.comune:
                filters["comune"] = args.comune

            results = gateway.search_images(args.query, top_k=args.top, filters=filters or None)

            print(f"\nRisultati per: '{args.query}'\n")
            for r in results:
                print(f"[{r['score']:.3f}] {r['titolo']} - {r['comune']}")
                print(f"         Tipo: {r['tipo']}")
                if r['immagini']:
                    print(f"         Img:  {r['immagini'][0]}")
                print()

        elif args.command == "build-index":
            gateway.build_embeddings_index(force_rebuild=True)
            print("Indice costruito!")

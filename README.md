# 🏡 Immobili Images API

Public API for accessing property images with AI-generated descriptions.
Designed for **embedding generation**, **content retrieval**, and **blog enrichment**.

---

## 🚀 Quick Start

### 1. Authentication

```bash
# Get JWT token
curl -X POST http://85.215.222.63:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "public_api",
    "password": "WyaJrRCUC0dyC//pLVM3Qmdvj+wIDM/M"
  }'

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

**Token validity:** 7 days

---

### 2. Fetch Properties with Images

```bash
# List properties (paginated)
curl -X GET 'http://85.215.222.63:8002/api/v1/immobili?page=1&page_size=20&con_immagini=true' \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get single property
curl -X GET 'http://85.215.222.63:8002/api/v1/immobili/123' \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get only images (lightweight)
curl -X GET 'http://85.215.222.63:8002/api/v1/immobili/123/immagini' \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📊 Response Format

### Property with Images

```json
{
  "id": 264,
  "codice_dam": "PRF4626V",
  "titolo": "Luxury Villa with Sea View",
  "tipo_immobile": "villa",
  "descrizione_breve": "Stunning villa in Porto Cervo...",
  "descrizione_estesa": "Full description here...",
  "comune": "Arzachena",
  "localita": "Porto Cervo",
  "mq_commerciali": 450.0,
  "camere_da_letto": 5,
  "bagni": 4,
  "prezzo_vendita": 3500000.0,
  "immagini": [
    {
      "id": 1234,
      "url": "https://cdn.immobilsarda.com/img/villa1.jpg",
      "ordine": 0
    },
    {
      "id": 1235,
      "url": "https://cdn.immobilsarda.com/img/villa2.jpg",
      "ordine": 1
    }
  ],
  "features_ai": {
    "vista_mare": true,
    "piscina": true,
    "giardino": true,
    "qualita_costruzione": "lusso",
    "stile_architettonico": "mediterranean"
  }
}
```

---

## 🤖 Python Client for Claude CLI

### Installation

```bash
pip install requests python-jose
```

### Client Code

```python
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ImmobiliImagesClient:
    """Client for Immobili Images API."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expires = None

    def _ensure_token(self):
        """Ensure valid JWT token."""
        if self.token and self.token_expires > datetime.now():
            return

        # Get new token
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": self.username, "password": self.password}
        )
        response.raise_for_status()

        data = response.json()
        self.token = data["access_token"]
        self.token_expires = datetime.now() + timedelta(seconds=data["expires_in"])

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        self._ensure_token()
        return {"Authorization": f"Bearer {self.token}"}

    def get_stats(self) -> Dict:
        """Get dataset statistics."""
        response = requests.get(
            f"{self.base_url}/api/v1/immobili/stats",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def list_immobili(
        self,
        page: int = 1,
        page_size: int = 20,
        tipo_immobile: Optional[str] = None,
        comune: Optional[str] = None,
        con_immagini: bool = True
    ) -> Dict:
        """List properties with filters."""
        params = {
            "page": page,
            "page_size": page_size,
            "con_immagini": con_immagini
        }
        if tipo_immobile:
            params["tipo_immobile"] = tipo_immobile
        if comune:
            params["comune"] = comune

        response = requests.get(
            f"{self.base_url}/api/v1/immobili",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_immobile(self, immobile_id: int) -> Dict:
        """Get single property with all details."""
        response = requests.get(
            f"{self.base_url}/api/v1/immobili/{immobile_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()

    def get_images(self, immobile_id: int) -> List[Dict]:
        """Get only images for a property."""
        response = requests.get(
            f"{self.base_url}/api/v1/immobili/{immobile_id}/immagini",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()


# Usage example
if __name__ == "__main__":
    client = ImmobiliImagesClient(
        base_url="http://85.215.222.63:8002",
        username="public_api",
        password="WyaJrRCUC0dyC//pLVM3Qmdvj+wIDM/M"
    )

    # Get statistics
    stats = client.get_stats()
    print(f"Total properties: {stats['total_immobili']}")
    print(f"With photos: {stats['immobili_con_foto']}")

    # List villas with images
    result = client.list_immobili(
        tipo_immobile="villa",
        con_immagini=True,
        page_size=10
    )

    for immobile in result["immobili"]:
        print(f"\n{immobile['titolo']} ({immobile['codice_dam']})")
        print(f"  Images: {len(immobile['immagini'])}")
        print(f"  AI Features: {immobile.get('features_ai', {})}")
```

---

## 🎯 Use Case: Generate CLIP Embeddings

### Workflow for Blog Enrichment

```python
from sentence_transformers import SentenceTransformer
import requests
from PIL import Image
from io import BytesIO

# Initialize CLIP model
model = SentenceTransformer('clip-ViT-B-32')

# Initialize client
client = ImmobiliImagesClient(
    base_url="http://85.215.222.63:8002",
    username="public_api",
    password="WyaJrRCUC0dyC//pLVM3Qmdvj+wIDM/M"
)

# 1. Fetch properties
properties = client.list_immobili(con_immagini=True, page_size=50)

# 2. Generate embeddings for each image
embeddings_db = []

for prop in properties["immobili"]:
    prop_id = prop["id"]
    title = prop["titolo"]

    for img in prop["immagini"]:
        # Download image
        response = requests.get(img["url"])
        image = Image.open(BytesIO(response.content))

        # Generate CLIP embedding
        embedding = model.encode(image)

        embeddings_db.append({
            "property_id": prop_id,
            "title": title,
            "image_url": img["url"],
            "embedding": embedding.tolist(),
            "ai_features": prop.get("features_ai", {})
        })

# 3. Query with text
query = "luxury villa with sea view and infinity pool"
query_embedding = model.encode(query)

# 4. Find most similar images (cosine similarity)
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

similarities = []
for item in embeddings_db:
    sim = cosine_similarity(
        [query_embedding],
        [np.array(item["embedding"])]
    )[0][0]
    similarities.append((sim, item))

# 5. Get top 5 matches
top_matches = sorted(similarities, key=lambda x: x[0], reverse=True)[:5]

print("Top matching properties:")
for score, item in top_matches:
    print(f"  - {item['title']} (score: {score:.3f})")
    print(f"    Image: {item['image_url']}")
    print(f"    Features: {item['ai_features']}")
```

---

## 🔒 Privacy & Security

### ✅ Applied Filters

The API **automatically filters** properties to ensure only public data is exposed:

- ✅ `is_attivo = true` (active properties only)
- ✅ `is_ufficiale = true` (official listings only)
- ❌ `is_riservato_direzione = false` (excludes direction-reserved)
- ❌ No private sales
- ❌ No inactive/archived properties

### 🔐 Authentication

- **JWT tokens** required for all endpoints (except `/` and `/health`)
- Token validity: **7 days**
- Tokens are stateless (no server-side session)

### 🚨 Rate Limiting

- **60 requests/minute** per IP (configurable)
- Exceeding limit returns `429 Too Many Requests`

---

## 🛠️ Deployment (VPS)

### Prerequisites

- Docker & Docker Compose installed on VPS
- Access to VPS: `ssh root@85.215.222.63`

### Deploy Steps

```bash
# 1. Clone repository on VPS
ssh root@85.215.222.63
cd /opt
git clone /path/to/immobili-images-api.git
cd immobili-images-api

# 2. Create .env file (copy from .env.example)
cp .env.example .env
nano .env  # Edit with actual credentials

# 3. Build and run
docker-compose up -d

# 4. Check status
docker-compose ps
curl http://localhost:8002/health

# 5. View logs
docker-compose logs -f
```

### Port Mapping

- **Internal:** Container port `8002`
- **External:** VPS port `8002`
- **Access:** `http://85.215.222.63:8002`

---

## 📚 API Documentation

### Interactive Docs

Once deployed, visit:

- **Swagger UI:** `http://85.215.222.63:8002/docs`
- **ReDoc:** `http://85.215.222.63:8002/redoc`

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all configuration options.

**Key settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | 85.215.222.63 | PostgreSQL host |
| `DB_NAME` | dbimmobiligb-staging | Database name |
| `PORT` | 8002 | API port |
| `JWT_EXPIRATION_HOURS` | 168 | Token validity (7 days) |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | 60 | Rate limit |

---

## 🐛 Troubleshooting

### 401 Unauthorized

- Check token is valid (not expired)
- Verify `Authorization: Bearer TOKEN` header is included

### 404 Property Not Found

- Property may not be public (check privacy flags)
- Property may be inactive or archived

### Connection Refused

- Check VPS firewall allows port `8002`
- Verify Docker container is running: `docker ps`

---

## 📞 Support

For issues or questions, contact the development team.

---

**Version:** 1.0.0
**Last updated:** 2025-01-29
**Status:** ✅ Production Ready

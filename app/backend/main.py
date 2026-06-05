import json
import logging
import os
import time
from decimal import Decimal
from typing import Generator, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, Gauge, generate_latest
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("realidadstore-backend")


# -----------------------------------------------------------------------------
# Database configuration
# -----------------------------------------------------------------------------
DATABASE_HOST = os.getenv("DATABASE_HOST", "postgres")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "realidadstoredb")
DATABASE_USER = os.getenv("DATABASE_USER", "realidad_user")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "RealidadStore2026")

DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# -----------------------------------------------------------------------------
# Prometheus metrics
# -----------------------------------------------------------------------------
HTTP_REQUESTS_TOTAL = Counter(
    "realidadstore_http_requests_total",
    "Total HTTP requests received by RealidadStore backend",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "realidadstore_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

PRODUCT_SEARCH_TOTAL = Counter(
    "realidadstore_product_search_total",
    "Total product searches in RealidadStore",
    ["category"]
)

CART_ADD_TOTAL = Counter(
    "realidadstore_cart_add_total",
    "Total cart add operations"
)

CHECKOUT_TOTAL = Counter(
    "realidadstore_checkout_total",
    "Total checkout operations",
    ["status"]
)

ACTIVE_CARTS_GAUGE = Gauge(
    "realidadstore_active_carts",
    "Current number of active carts"
)

ORDERS_GAUGE = Gauge(
    "realidadstore_orders_total_gauge",
    "Total orders registered in database"
)


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class StoreProduct(Base):
    __tablename__ = "store_products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(40), unique=True, nullable=False)
    name = Column(String(140), nullable=False)
    category = Column(String(80), nullable=False)
    brand = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    old_price = Column(Numeric(10, 2), nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    rating = Column(Numeric(3, 2), nullable=False, default=4.5)
    sold_count = Column(Integer, nullable=False, default=0)
    featured = Column(Boolean, nullable=False, default=False)
    image_url = Column(String(500), nullable=False)
    tags = Column(String(300), nullable=False, default="")
    specs_json = Column(Text, nullable=False, default="{}")


class StoreCartItem(Base):
    __tablename__ = "store_cart_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(120), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("store_products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StoreWishlistItem(Base):
    __tablename__ = "store_wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(120), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("store_products.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StoreReview(Base):
    __tablename__ = "store_reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("store_products.id"), nullable=False)
    username = Column(String(80), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StoreOrder(Base):
    __tablename__ = "store_orders"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(120), nullable=False, index=True)
    customer_name = Column(String(120), nullable=False)
    customer_email = Column(String(160), nullable=False)
    shipping_address = Column(Text, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    status = Column(String(40), nullable=False, default="CREATED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StoreOrderItem(Base):
    __tablename__ = "store_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("store_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("store_products.id"), nullable=False)
    product_name = Column(String(140), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class CartUpdateRequest(BaseModel):
    quantity: int = Field(ge=1, le=20)


class ReviewRequest(BaseModel):
    product_id: int
    username: str = Field(min_length=2, max_length=80)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=3, max_length=500)


class CheckoutRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: str = Field(min_length=5, max_length=160)
    shipping_address: str = Field(min_length=5, max_length=300)


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(
    title="RealidadStore API",
    description="API ecommerce para tienda VR, AR & Gaming sobre Kubernetes",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_id(x_session_id: str = Header(default="anonymous", alias="X-Session-Id")) -> str:
    return x_session_id.strip() or "anonymous"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def money(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def parse_specs(specs_json: str) -> dict:
    try:
        return json.loads(specs_json)
    except Exception:
        return {}


def product_to_dict(product: StoreProduct, favorite: bool = False) -> dict:
    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "description": product.description,
        "price": money(product.price),
        "old_price": money(product.old_price) if product.old_price else None,
        "stock": product.stock,
        "rating": money(product.rating),
        "sold_count": product.sold_count,
        "featured": product.featured,
        "image_url": product.image_url,
        "tags": [tag.strip() for tag in product.tags.split(",") if tag.strip()],
        "specs": parse_specs(product.specs_json),
        "favorite": favorite
    }


def get_cart_payload(db: Session, session_id: str) -> dict:
    items = (
        db.query(StoreCartItem)
        .filter(StoreCartItem.session_id == session_id)
        .order_by(StoreCartItem.id)
        .all()
    )

    response_items = []
    total = Decimal("0.00")

    for item in items:
        product = db.query(StoreProduct).filter(StoreProduct.id == item.product_id).first()

        if not product:
            continue

        subtotal = product.price * item.quantity
        total += subtotal

        response_items.append({
            "id": item.id,
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "quantity": item.quantity,
            "stock": product.stock,
            "unit_price": money(product.price),
            "subtotal": money(subtotal)
        })

    return {
        "session_id": session_id,
        "items": response_items,
        "total": money(total),
        "items_count": len(response_items)
    }


# -----------------------------------------------------------------------------
# Seed
# -----------------------------------------------------------------------------
def seed_products(db: Session) -> None:
    existing = db.query(StoreProduct).count()

    if existing > 0:
        logger.info("SEED_PRODUCTS_SKIPPED existing_products=%s", existing)
        return

    products = [
        StoreProduct(
            sku="VR-META-Q3-128",
            name="Meta Quest 3 128GB",
            category="Visores VR",
            brand="Meta",
            description="Visor standalone de realidad mixta para gaming, fitness, simuladores y productividad inmersiva.",
            price=8999.00,
            old_price=10499.00,
            stock=16,
            rating=4.8,
            sold_count=124,
            featured=True,
            image_url="https://images.unsplash.com/photo-1593508512255-86ab42a8e620?auto=format&fit=crop&w=900&q=80",
            tags="VR,standalone,bestseller,realidad mixta",
            specs_json=json.dumps({
                "Resolución": "Alta definición",
                "Uso": "Standalone",
                "Conectividad": "WiFi / Bluetooth",
                "Ideal para": "Gaming y experiencias inmersivas"
            })
        ),
        StoreProduct(
            sku="VR-PSVR2-HMD",
            name="PlayStation VR2",
            category="Visores VR",
            brand="Sony",
            description="Sistema VR para consola con controles hápticos, seguimiento ocular y experiencia de juego inmersiva.",
            price=11999.00,
            old_price=12999.00,
            stock=9,
            rating=4.7,
            sold_count=88,
            featured=True,
            image_url="https://images.unsplash.com/photo-1622979135225-d2ba269cf1ac?auto=format&fit=crop&w=900&q=80",
            tags="VR,consola,haptico,premium",
            specs_json=json.dumps({
                "Compatibilidad": "Consola",
                "Control": "Sense controllers",
                "Experiencia": "Gaming premium",
                "Audio": "3D compatible"
            })
        ),
        StoreProduct(
            sku="VR-VIVE-PRO2",
            name="HTC Vive Pro 2",
            category="Visores VR",
            brand="HTC",
            description="Visor VR de alto rendimiento para simuladores, capacitación, diseño y experiencias profesionales.",
            price=18999.00,
            old_price=20999.00,
            stock=5,
            rating=4.6,
            sold_count=42,
            featured=False,
            image_url="https://images.unsplash.com/photo-1617802690992-15d93263d3a9?auto=format&fit=crop&w=900&q=80",
            tags="VR,profesional,simulacion,alta resolucion",
            specs_json=json.dumps({
                "Segmento": "Profesional",
                "Uso": "Simulación / capacitación",
                "Tracking": "Externo",
                "Ideal para": "Empresas y laboratorios"
            })
        ),
        StoreProduct(
            sku="AR-DEV-KIT-01",
            name="AR Developer Glasses",
            category="Lentes AR",
            brand="Reality Labs",
            description="Kit de lentes de realidad aumentada para prototipos, visualización 3D y desarrollo de interfaces espaciales.",
            price=15999.00,
            old_price=None,
            stock=7,
            rating=4.4,
            sold_count=31,
            featured=True,
            image_url="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=900&q=80",
            tags="AR,developer,prototipo,espacial",
            specs_json=json.dumps({
                "Uso": "Desarrollo",
                "SDK": "Compatible con prototipos",
                "Pantalla": "Transparente",
                "Ideal para": "AR y demos empresariales"
            })
        ),
        StoreProduct(
            sku="ACC-HAPTIC-02",
            name="Control Háptico VR Pro",
            category="Accesorios",
            brand="HaptiX",
            description="Control con retroalimentación háptica avanzada para juegos VR, simuladores y entrenamiento inmersivo.",
            price=2499.00,
            old_price=2999.00,
            stock=28,
            rating=4.5,
            sold_count=210,
            featured=False,
            image_url="https://images.unsplash.com/photo-1605901309584-818e25960a8f?auto=format&fit=crop&w=900&q=80",
            tags="control,haptico,VR,accesorio",
            specs_json=json.dumps({
                "Batería": "Hasta 10 horas",
                "Conexión": "Bluetooth",
                "Vibración": "Haptics avanzada",
                "Compatibilidad": "VR estándar"
            })
        ),
        StoreProduct(
            sku="ACC-TRACK-FULL",
            name="Full Body Tracking Pack",
            category="Accesorios",
            brand="TrackMotion",
            description="Paquete de sensores para rastreo corporal completo en experiencias VR sociales, fitness y simuladores.",
            price=3299.00,
            old_price=3899.00,
            stock=14,
            rating=4.6,
            sold_count=97,
            featured=True,
            image_url="https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=900&q=80",
            tags="tracking,sensores,full body,VR",
            specs_json=json.dumps({
                "Sensores": "3 trackers",
                "Uso": "Cuerpo completo",
                "Conexión": "Inalámbrica",
                "Ideal para": "VRChat / simuladores"
            })
        ),
        StoreProduct(
            sku="GAME-BEAT-SABER",
            name="Beat Saber VR",
            category="Juegos VR",
            brand="Beat Games",
            description="Juego musical de realidad virtual basado en ritmo, precisión y movimiento físico.",
            price=699.00,
            old_price=None,
            stock=100,
            rating=4.9,
            sold_count=540,
            featured=True,
            image_url="https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=900&q=80",
            tags="juego,VR,musica,bestseller",
            specs_json=json.dumps({
                "Género": "Ritmo",
                "Modo": "Un jugador",
                "Edad": "Todo público",
                "Formato": "Código digital"
            })
        ),
        StoreProduct(
            sku="GAME-HLA-VR",
            name="Half-Life Alyx",
            category="Juegos VR",
            brand="Valve",
            description="Aventura VR de acción, exploración y narrativa considerada referencia en experiencias inmersivas.",
            price=899.00,
            old_price=1199.00,
            stock=80,
            rating=4.9,
            sold_count=430,
            featured=True,
            image_url="https://images.unsplash.com/photo-1552820728-8b83bb6b773f?auto=format&fit=crop&w=900&q=80",
            tags="juego,VR,accion,narrativa",
            specs_json=json.dumps({
                "Género": "Acción / aventura",
                "Formato": "Digital",
                "Requiere": "PC VR",
                "Modo": "Un jugador"
            })
        ),
        StoreProduct(
            sku="AUD-71-GAMING",
            name="Audífonos Gaming 7.1",
            category="Audio Gaming",
            brand="SoundMax",
            description="Audífonos con audio envolvente, micrófono desmontable y baja latencia para partidas competitivas.",
            price=1499.00,
            old_price=1899.00,
            stock=24,
            rating=4.4,
            sold_count=190,
            featured=False,
            image_url="https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?auto=format&fit=crop&w=900&q=80",
            tags="audio,gaming,headset,7.1",
            specs_json=json.dumps({
                "Audio": "7.1 virtual",
                "Micrófono": "Desmontable",
                "Conexión": "USB / 3.5mm",
                "Ideal para": "Competitivo"
            })
        ),
        StoreProduct(
            sku="CHAIR-IMMERSIVE",
            name="Silla Gamer Inmersiva",
            category="Setup Gaming",
            brand="ErgoPlay",
            description="Silla ergonómica con soporte lumbar y diseño pensado para sesiones largas de VR, simulación y streaming.",
            price=4999.00,
            old_price=5999.00,
            stock=10,
            rating=4.3,
            sold_count=76,
            featured=False,
            image_url="https://images.unsplash.com/photo-1598550476439-6847785fcea6?auto=format&fit=crop&w=900&q=80",
            tags="silla,gaming,ergonomia,setup",
            specs_json=json.dumps({
                "Material": "Piel sintética",
                "Reclinación": "Ajustable",
                "Soporte": "Lumbar y cervical",
                "Peso máximo": "120 kg"
            })
        ),
        StoreProduct(
            sku="GPU-RTX-GAMING",
            name="GPU Gaming RTX Ready",
            category="Setup Gaming",
            brand="NovaGPU",
            description="Tarjeta gráfica orientada a gaming, experiencias VR y renderizado de escenas 3D.",
            price=12999.00,
            old_price=14999.00,
            stock=6,
            rating=4.7,
            sold_count=54,
            featured=True,
            image_url="https://images.unsplash.com/photo-1587202372775-e229f172b9d7?auto=format&fit=crop&w=900&q=80",
            tags="GPU,VR ready,gaming,hardware",
            specs_json=json.dumps({
                "Memoria": "12GB",
                "Uso": "VR / gaming",
                "Salida": "HDMI / DisplayPort",
                "Ideal para": "PC gamer"
            })
        ),
        StoreProduct(
            sku="KEY-RGB-MECH",
            name="Teclado Mecánico RGB",
            category="Setup Gaming",
            brand="KeyForge",
            description="Teclado mecánico con iluminación RGB, switches táctiles y construcción resistente.",
            price=1299.00,
            old_price=1599.00,
            stock=30,
            rating=4.5,
            sold_count=230,
            featured=False,
            image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80",
            tags="teclado,mecanico,RGB,gaming",
            specs_json=json.dumps({
                "Switches": "Táctiles",
                "Iluminación": "RGB",
                "Distribución": "Full size",
                "Conexión": "USB-C"
            })
        ),
        StoreProduct(
            sku="MON-ULTRAWIDE",
            name="Monitor UltraWide Gaming",
            category="Setup Gaming",
            brand="WideVision",
            description="Monitor panorámico para simuladores, multitarea, gaming competitivo y edición de contenido.",
            price=6999.00,
            old_price=8499.00,
            stock=11,
            rating=4.6,
            sold_count=68,
            featured=False,
            image_url="https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80",
            tags="monitor,ultrawide,gaming,setup",
            specs_json=json.dumps({
                "Tamaño": "34 pulgadas",
                "Resolución": "UltraWide",
                "Frecuencia": "144Hz",
                "Ideal para": "Simuladores"
            })
        ),
        StoreProduct(
            sku="CAM-STREAM-4K",
            name="Cámara Streaming 4K",
            category="Streaming",
            brand="StreamLab",
            description="Cámara 4K para creadores de contenido, streamers, clases virtuales y demos de videojuegos.",
            price=2199.00,
            old_price=2699.00,
            stock=19,
            rating=4.4,
            sold_count=115,
            featured=False,
            image_url="https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80",
            tags="streaming,camara,4K,contenido",
            specs_json=json.dumps({
                "Resolución": "4K",
                "Micrófono": "Integrado",
                "Conexión": "USB",
                "Uso": "Streaming"
            })
        ),
        StoreProduct(
            sku="MIC-CAST-PRO",
            name="Micrófono Podcast Pro",
            category="Streaming",
            brand="CastPro",
            description="Micrófono de condensador para streaming, podcast, clases y grabación de voz con calidad profesional.",
            price=1699.00,
            old_price=1999.00,
            stock=21,
            rating=4.6,
            sold_count=130,
            featured=False,
            image_url="https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=900&q=80",
            tags="microfono,podcast,streaming,audio",
            specs_json=json.dumps({
                "Tipo": "Condensador",
                "Conexión": "USB",
                "Patrón": "Cardioide",
                "Uso": "Streaming / podcast"
            })
        ),
        StoreProduct(
            sku="BUNDLE-VR-STARTER",
            name="Bundle VR Starter Pack",
            category="Bundles",
            brand="RealidadStore",
            description="Paquete inicial con visor VR, controles, audífonos y juego digital para comenzar en realidad virtual.",
            price=12499.00,
            old_price=14999.00,
            stock=8,
            rating=4.8,
            sold_count=61,
            featured=True,
            image_url="https://images.unsplash.com/photo-1560253023-3ec5d502959f?auto=format&fit=crop&w=900&q=80",
            tags="bundle,VR,starter,oferta",
            specs_json=json.dumps({
                "Incluye": "Visor, controles, audífonos, juego",
                "Ahorro": "Paquete promocional",
                "Uso": "Inicio en VR",
                "Garantía": "12 meses"
            })
        ),
    ]

    db.add_all(products)
    db.commit()

    reviews = [
        StoreReview(product_id=1, username="cliente_vr", rating=5, comment="Excelente visor, muy buena experiencia inmersiva."),
        StoreReview(product_id=1, username="gamer_mx", rating=5, comment="El catálogo y la respuesta de la app se sienten rápidos."),
        StoreReview(product_id=7, username="rhythm_player", rating=5, comment="Ideal para demo en clase, se entiende perfecto el caso de negocio."),
        StoreReview(product_id=11, username="pc_builder", rating=4, comment="Buen producto para mostrar ecommerce gaming."),
    ]

    db.add_all(reviews)
    db.commit()

    logger.info("SEED_PRODUCTS_COMPLETED inserted_products=%s", len(products))


def refresh_business_gauges(db: Session) -> None:
    active_carts = db.query(StoreCartItem.session_id).distinct().count()
    total_orders = db.query(StoreOrder).count()

    ACTIVE_CARTS_GAUGE.set(active_carts)
    ORDERS_GAUGE.set(total_orders)


@app.on_event("startup")
def startup_event() -> None:
    logger.info("STARTUP_BEGIN service=realidadstore-backend version=2.0.0")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_products(db)
        refresh_business_gauges(db)
    finally:
        db.close()

    logger.info("STARTUP_COMPLETED service=realidadstore-backend version=2.0.0")


# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

    return response


# -----------------------------------------------------------------------------
# Core endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "RealidadStore API",
        "version": "2.0.0",
        "description": "Ecommerce VR, AR & Gaming sobre Kubernetes"
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "UP",
            "database": "UP",
            "version": "2.0.0"
        }
    except Exception as exc:
        logger.error("HEALTHCHECK_FAILED error=%s", str(exc))
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/store/summary")
def store_summary(db: Session = Depends(get_db)):
    products = db.query(StoreProduct).count()
    categories = db.query(StoreProduct.category).distinct().count()
    stock = db.query(func.coalesce(func.sum(StoreProduct.stock), 0)).scalar()
    orders = db.query(StoreOrder).count()

    return {
        "products": products,
        "categories": categories,
        "stock_units": int(stock or 0),
        "orders": orders,
        "store_name": "RealidadStore",
        "tagline": "VR, AR & Gaming Gear"
    }


@app.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = (
        db.query(StoreProduct.category, func.count(StoreProduct.id))
        .group_by(StoreProduct.category)
        .order_by(StoreProduct.category)
        .all()
    )

    return [
        {
            "name": row[0],
            "count": row[1]
        }
        for row in rows
    ]


@app.get("/products")
def list_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort: Optional[str] = "featured",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    query = db.query(StoreProduct)

    if search:
        like = f"%{search}%"
        query = query.filter(
            StoreProduct.name.ilike(like)
            | StoreProduct.brand.ilike(like)
            | StoreProduct.description.ilike(like)
            | StoreProduct.tags.ilike(like)
        )

    if category:
        query = query.filter(StoreProduct.category == category)
        metric_category = category
    else:
        metric_category = "all"

    if min_price is not None:
        query = query.filter(StoreProduct.price >= min_price)

    if max_price is not None:
        query = query.filter(StoreProduct.price <= max_price)

    if featured is not None:
        query = query.filter(StoreProduct.featured == featured)

    if in_stock:
        query = query.filter(StoreProduct.stock > 0)

    if sort == "price_asc":
        query = query.order_by(StoreProduct.price.asc())
    elif sort == "price_desc":
        query = query.order_by(StoreProduct.price.desc())
    elif sort == "rating":
        query = query.order_by(StoreProduct.rating.desc())
    elif sort == "sold":
        query = query.order_by(StoreProduct.sold_count.desc())
    elif sort == "newest":
        query = query.order_by(StoreProduct.id.desc())
    else:
        query = query.order_by(StoreProduct.featured.desc(), StoreProduct.rating.desc(), StoreProduct.id.asc())

    products = query.all()

    favorite_ids = {
        item.product_id
        for item in db.query(StoreWishlistItem).filter(StoreWishlistItem.session_id == session_id).all()
    }

    PRODUCT_SEARCH_TOTAL.labels(category=metric_category).inc()

    logger.info(
        "PRODUCT_LIST session_id=%s search=%s category=%s sort=%s results=%s",
        session_id,
        search,
        category,
        sort,
        len(products)
    )

    return {
        "items": [
            product_to_dict(product, favorite=product.id in favorite_ids)
            for product in products
        ],
        "count": len(products)
    }


@app.get("/products/{product_id}")
def product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    product = db.query(StoreProduct).filter(StoreProduct.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    favorite = (
        db.query(StoreWishlistItem)
        .filter(
            StoreWishlistItem.session_id == session_id,
            StoreWishlistItem.product_id == product_id
        )
        .first()
        is not None
    )

    reviews = (
        db.query(StoreReview)
        .filter(StoreReview.product_id == product_id)
        .order_by(StoreReview.id.desc())
        .all()
    )

    payload = product_to_dict(product, favorite=favorite)
    payload["reviews"] = [
        {
            "id": review.id,
            "username": review.username,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": str(review.created_at)
        }
        for review in reviews
    ]

    logger.info("PRODUCT_DETAIL session_id=%s product_id=%s", session_id, product_id)

    return payload


# -----------------------------------------------------------------------------
# Cart
# -----------------------------------------------------------------------------
@app.get("/cart")
def get_cart(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)):
    payload = get_cart_payload(db, session_id)
    logger.info("GET_CART session_id=%s items=%s total=%s", session_id, payload["items_count"], payload["total"])
    return payload


@app.post("/cart/items")
def add_cart_item(
    item: CartItemRequest,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    product = db.query(StoreProduct).filter(StoreProduct.id == item.product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="Product out of stock")

    existing = (
        db.query(StoreCartItem)
        .filter(
            StoreCartItem.session_id == session_id,
            StoreCartItem.product_id == item.product_id
        )
        .first()
    )

    new_quantity = item.quantity

    if existing:
        new_quantity = existing.quantity + item.quantity

    if new_quantity > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock")

    if existing:
        existing.quantity = new_quantity
    else:
        db.add(
            StoreCartItem(
                session_id=session_id,
                product_id=item.product_id,
                quantity=item.quantity
            )
        )

    db.commit()
    refresh_business_gauges(db)
    CART_ADD_TOTAL.inc()

    logger.info(
        "ADD_TO_CART session_id=%s product_id=%s product_name=%s quantity=%s",
        session_id,
        product.id,
        product.name,
        item.quantity
    )

    return get_cart_payload(db, session_id)


@app.patch("/cart/items/{cart_item_id}")
def update_cart_item(
    cart_item_id: int,
    item: CartUpdateRequest,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    cart_item = (
        db.query(StoreCartItem)
        .filter(
            StoreCartItem.id == cart_item_id,
            StoreCartItem.session_id == session_id
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    product = db.query(StoreProduct).filter(StoreProduct.id == cart_item.product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if item.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock")

    cart_item.quantity = item.quantity
    db.commit()

    logger.info("UPDATE_CART session_id=%s cart_item_id=%s quantity=%s", session_id, cart_item_id, item.quantity)

    return get_cart_payload(db, session_id)


@app.delete("/cart/items/{cart_item_id}")
def delete_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    cart_item = (
        db.query(StoreCartItem)
        .filter(
            StoreCartItem.id == cart_item_id,
            StoreCartItem.session_id == session_id
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()
    refresh_business_gauges(db)

    logger.info("DELETE_CART_ITEM session_id=%s cart_item_id=%s", session_id, cart_item_id)

    return get_cart_payload(db, session_id)


@app.delete("/cart")
def clear_cart(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)):
    deleted = db.query(StoreCartItem).filter(StoreCartItem.session_id == session_id).delete()
    db.commit()
    refresh_business_gauges(db)

    logger.info("CLEAR_CART session_id=%s deleted=%s", session_id, deleted)

    return get_cart_payload(db, session_id)


# -----------------------------------------------------------------------------
# Wishlist
# -----------------------------------------------------------------------------
@app.get("/wishlist")
def get_wishlist(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)):
    rows = (
        db.query(StoreWishlistItem)
        .filter(StoreWishlistItem.session_id == session_id)
        .order_by(StoreWishlistItem.id.desc())
        .all()
    )

    product_ids = [row.product_id for row in rows]

    products = []
    if product_ids:
        products = db.query(StoreProduct).filter(StoreProduct.id.in_(product_ids)).all()

    return {
        "items": [product_to_dict(product, favorite=True) for product in products],
        "count": len(products)
    }


@app.post("/wishlist/{product_id}")
def add_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    product = db.query(StoreProduct).filter(StoreProduct.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(StoreWishlistItem)
        .filter(
            StoreWishlistItem.session_id == session_id,
            StoreWishlistItem.product_id == product_id
        )
        .first()
    )

    if not existing:
        db.add(StoreWishlistItem(session_id=session_id, product_id=product_id))
        db.commit()

    logger.info("ADD_WISHLIST session_id=%s product_id=%s", session_id, product_id)

    return {"ok": True}


@app.delete("/wishlist/{product_id}")
def remove_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    deleted = (
        db.query(StoreWishlistItem)
        .filter(
            StoreWishlistItem.session_id == session_id,
            StoreWishlistItem.product_id == product_id
        )
        .delete()
    )

    db.commit()

    logger.info("REMOVE_WISHLIST session_id=%s product_id=%s deleted=%s", session_id, product_id, deleted)

    return {"ok": True}


# -----------------------------------------------------------------------------
# Reviews
# -----------------------------------------------------------------------------
@app.post("/reviews")
def create_review(review: ReviewRequest, db: Session = Depends(get_db)):
    product = db.query(StoreProduct).filter(StoreProduct.id == review.product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_review = StoreReview(
        product_id=review.product_id,
        username=review.username,
        rating=review.rating,
        comment=review.comment
    )

    db.add(new_review)

    avg_rating = (
        db.query(func.avg(StoreReview.rating))
        .filter(StoreReview.product_id == review.product_id)
        .scalar()
    )

    if avg_rating:
        product.rating = avg_rating

    db.commit()
    db.refresh(new_review)

    logger.info(
        "CREATE_REVIEW product_id=%s username=%s rating=%s",
        review.product_id,
        review.username,
        review.rating
    )

    return {
        "id": new_review.id,
        "product_id": new_review.product_id,
        "username": new_review.username,
        "rating": new_review.rating,
        "comment": new_review.comment
    }


# -----------------------------------------------------------------------------
# Checkout / Orders
# -----------------------------------------------------------------------------
@app.post("/orders/checkout")
def checkout(
    checkout_request: CheckoutRequest,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    cart = get_cart_payload(db, session_id)

    if cart["items_count"] == 0:
        CHECKOUT_TOTAL.labels(status="empty_cart").inc()
        raise HTTPException(status_code=400, detail="Cart is empty")

    try:
        total = Decimal("0.00")

        for item in cart["items"]:
            product = db.query(StoreProduct).filter(StoreProduct.id == item["product_id"]).first()

            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item['product_id']} not found")

            if product.stock < item["quantity"]:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

            total += Decimal(str(item["subtotal"]))

        order = StoreOrder(
            session_id=session_id,
            customer_name=checkout_request.customer_name,
            customer_email=checkout_request.customer_email,
            shipping_address=checkout_request.shipping_address,
            total=total,
            status="PAID"
        )

        db.add(order)
        db.flush()

        for item in cart["items"]:
            product = db.query(StoreProduct).filter(StoreProduct.id == item["product_id"]).first()

            product.stock -= item["quantity"]
            product.sold_count += item["quantity"]

            db.add(
                StoreOrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=Decimal(str(item["unit_price"])),
                    quantity=item["quantity"],
                    subtotal=Decimal(str(item["subtotal"]))
                )
            )

        db.query(StoreCartItem).filter(StoreCartItem.session_id == session_id).delete()
        db.commit()

        refresh_business_gauges(db)
        CHECKOUT_TOTAL.labels(status="success").inc()

        logger.info(
            "CHECKOUT_SUCCESS session_id=%s order_id=%s total=%s customer=%s",
            session_id,
            order.id,
            total,
            checkout_request.customer_email
        )

        return {
            "order_id": order.id,
            "status": order.status,
            "total": money(order.total),
            "message": "Compra procesada correctamente"
        }

    except HTTPException:
        db.rollback()
        CHECKOUT_TOTAL.labels(status="business_error").inc()
        raise
    except Exception as exc:
        db.rollback()
        CHECKOUT_TOTAL.labels(status="error").inc()
        logger.error("CHECKOUT_FAILED session_id=%s error=%s", session_id, str(exc))
        raise HTTPException(status_code=500, detail="Checkout failed")


@app.get("/orders")
def list_orders(db: Session = Depends(get_db), session_id: str = Depends(get_session_id)):
    orders = (
        db.query(StoreOrder)
        .filter(StoreOrder.session_id == session_id)
        .order_by(StoreOrder.id.desc())
        .all()
    )

    payload = []

    for order in orders:
        items = (
            db.query(StoreOrderItem)
            .filter(StoreOrderItem.order_id == order.id)
            .order_by(StoreOrderItem.id)
            .all()
        )

        payload.append({
            "id": order.id,
            "status": order.status,
            "total": money(order.total),
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "created_at": str(order.created_at),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": money(item.unit_price),
                    "subtotal": money(item.subtotal)
                }
                for item in items
            ]
        })

    return {
        "items": payload,
        "count": len(payload)
    }



# -----------------------------------------------------------------------------
# Load test endpoint for HPA demo
# -----------------------------------------------------------------------------
@app.get("/load/cpu")
def cpu_load(seconds: int = 2):
    safe_seconds = max(1, min(seconds, 10))
    end_time = time.time() + safe_seconds
    operations = 0
    checksum = 0

    while time.time() < end_time:
        for number in range(1, 25000):
            checksum += (number * number) % 97
            operations += 1

    logger.info(
        "CPU_LOAD_TEST seconds=%s operations=%s checksum=%s",
        safe_seconds,
        operations,
        checksum
    )

    return {
        "status": "completed",
        "seconds": safe_seconds,
        "operations": operations,
        "checksum": checksum
    }


# -----------------------------------------------------------------------------
# Metrics
# -----------------------------------------------------------------------------
@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    refresh_business_gauges(db)
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

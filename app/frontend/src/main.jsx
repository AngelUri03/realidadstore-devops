import React from 'react';
import { createRoot } from 'react-dom/client';
import {
  BadgeCheck,
  Boxes,
  ChevronDown,
  CreditCard,
  Filter,
  Gamepad2,
  Heart,
  Minus,
  PackageCheck,
  Plus,
  Search,
  ShoppingBag,
  ShoppingCart,
  SlidersHorizontal,
  Sparkles,
  Star,
  Trash2,
  Truck,
  X,
  Zap
} from 'lucide-react';
import './index.css';

const API_BASE = '/api';

function createClientId() {
  if (window.crypto && typeof window.crypto.randomUUID === 'function') {
    return window.crypto.randomUUID();
  }

  if (window.crypto && typeof window.crypto.getRandomValues === 'function') {
    const values = new Uint32Array(4);
    window.crypto.getRandomValues(values);

    return Array.from(values)
      .map((value) => value.toString(16).padStart(8, '0'))
      .join('-');
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getSessionId() {
  const existing = localStorage.getItem('realidadstore_session_id');

  if (existing) {
    return existing;
  }

  const generated = `client-${createClientId()}`;
  localStorage.setItem('realidadstore_session_id', generated);
  return generated;
}

const SESSION_ID = getSessionId();

const apiHeaders = {
  'Content-Type': 'application/json',
  'X-Session-Id': SESSION_ID
};

function currency(value) {
  return Number(value || 0).toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN'
  });
}

function App() {
  const [summary, setSummary] = React.useState(null);
  const [categories, setCategories] = React.useState([]);
  const [products, setProducts] = React.useState([]);
  const [cart, setCart] = React.useState({ items: [], total: 0, items_count: 0 });
  const [orders, setOrders] = React.useState([]);
  const [selectedProduct, setSelectedProduct] = React.useState(null);
  const [cartOpen, setCartOpen] = React.useState(false);
  const [checkoutOpen, setCheckoutOpen] = React.useState(false);
  const [orderSuccess, setOrderSuccess] = React.useState(null);
  const [toast, setToast] = React.useState('Bienvenido a RealidadStore');
  const [loading, setLoading] = React.useState(false);

  const [filters, setFilters] = React.useState({
    search: '',
    category: '',
    sort: 'featured',
    minPrice: '',
    maxPrice: '',
    inStock: false,
    featured: false
  });

  React.useEffect(() => {
    loadInitialData();
  }, []);

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...apiHeaders,
        ...(options.headers || {})
      }
    });

    if (!response.ok) {
      let message = 'Error de comunicación con la tienda';

      try {
        const error = await response.json();
        message = error.detail || message;
      } catch {
        // ignore
      }

      throw new Error(message);
    }

    return response.json();
  }

  async function loadInitialData() {
    setLoading(true);

    try {
      const [summaryData, categoryData, productsData, cartData, ordersData] = await Promise.all([
        request('/store/summary'),
        request('/categories'),
        request('/products'),
        request('/cart'),
        request('/orders')
      ]);

      setSummary(summaryData);
      setCategories(categoryData);
      setProducts(productsData.items);
      setCart(cartData);
      setOrders(ordersData.items);
      setToast('Catálogo cargado desde FastAPI + PostgreSQL');
    } catch (error) {
      setToast(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadCart() {
    const data = await request('/cart');
    setCart(data);
  }

  async function loadOrders() {
    const data = await request('/orders');
    setOrders(data.items);
  }

  async function applyFilters(nextFilters = filters) {
    setLoading(true);

    try {
      const params = new URLSearchParams();

      if (nextFilters.search) {
        params.append('search', nextFilters.search);
      }

      if (nextFilters.category) {
        params.append('category', nextFilters.category);
      }

      if (nextFilters.sort) {
        params.append('sort', nextFilters.sort);
      }

      if (nextFilters.minPrice) {
        params.append('min_price', nextFilters.minPrice);
      }

      if (nextFilters.maxPrice) {
        params.append('max_price', nextFilters.maxPrice);
      }

      if (nextFilters.inStock) {
        params.append('in_stock', 'true');
      }

      if (nextFilters.featured) {
        params.append('featured', 'true');
      }

      const data = await request(`/products?${params.toString()}`);
      setProducts(data.items);
      setToast(`${data.count} producto(s) encontrados`);
    } catch (error) {
      setToast(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function resetFilters() {
    const clean = {
      search: '',
      category: '',
      sort: 'featured',
      minPrice: '',
      maxPrice: '',
      inStock: false,
      featured: false
    };

    setFilters(clean);
    await applyFilters(clean);
  }

  async function openProduct(productId) {
    try {
      const data = await request(`/products/${productId}`);
      setSelectedProduct(data);
    } catch (error) {
      setToast(error.message);
    }
  }

  async function addToCart(productId, quantity = 1) {
    try {
      const data = await request('/cart/items', {
        method: 'POST',
        body: JSON.stringify({
          product_id: productId,
          quantity
        })
      });

      setCart(data);
      setCartOpen(true);
      setToast('Producto agregado al carrito');
    } catch (error) {
      setToast(error.message);
    }
  }

  async function updateCartItem(cartItemId, quantity) {
    if (quantity < 1) {
      return;
    }

    try {
      const data = await request(`/cart/items/${cartItemId}`, {
        method: 'PATCH',
        body: JSON.stringify({ quantity })
      });

      setCart(data);
    } catch (error) {
      setToast(error.message);
    }
  }

  async function removeCartItem(cartItemId) {
    try {
      const data = await request(`/cart/items/${cartItemId}`, {
        method: 'DELETE'
      });

      setCart(data);
      setToast('Producto removido del carrito');
    } catch (error) {
      setToast(error.message);
    }
  }

  async function clearCart() {
    try {
      const data = await request('/cart', {
        method: 'DELETE'
      });

      setCart(data);
      setToast('Carrito limpiado');
    } catch (error) {
      setToast(error.message);
    }
  }

  async function toggleFavorite(product) {
    try {
      if (product.favorite) {
        await request(`/wishlist/${product.id}`, { method: 'DELETE' });
      } else {
        await request(`/wishlist/${product.id}`, { method: 'POST' });
      }

      const updatedProducts = products.map((item) => {
        if (item.id === product.id) {
          return { ...item, favorite: !item.favorite };
        }

        return item;
      });

      setProducts(updatedProducts);

      if (selectedProduct?.id === product.id) {
        setSelectedProduct({
          ...selectedProduct,
          favorite: !selectedProduct.favorite
        });
      }

      setToast(product.favorite ? 'Removido de favoritos' : 'Agregado a favoritos');
    } catch (error) {
      setToast(error.message);
    }
  }

  async function checkout(event) {
    event.preventDefault();

    const form = new FormData(event.currentTarget);

    try {
      const data = await request('/orders/checkout', {
        method: 'POST',
        body: JSON.stringify({
          customer_name: form.get('customer_name'),
          customer_email: form.get('customer_email'),
          shipping_address: form.get('shipping_address')
        })
      });

      setOrderSuccess(data);
      setCheckoutOpen(false);
      setCartOpen(false);
      await loadCart();
      await loadOrders();
      await applyFilters();
      setToast(`Compra completada. Orden #${data.order_id}`);
    } catch (error) {
      setToast(error.message);
    }
  }

  const totalItems = cart.items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <main className="min-h-screen">
      <TopBar
        totalItems={totalItems}
        onCart={() => setCartOpen(true)}
      />

      <Hero
        summary={summary}
        filters={filters}
        setFilters={setFilters}
        applyFilters={applyFilters}
      />

      <section className="mx-auto grid w-[min(1420px,calc(100%-32px))] grid-cols-1 gap-6 py-8 lg:grid-cols-[290px_1fr]">
        <FiltersPanel
          categories={categories}
          filters={filters}
          setFilters={setFilters}
          applyFilters={applyFilters}
          resetFilters={resetFilters}
        />

        <section>
          <CatalogHeader
            count={products.length}
            loading={loading}
            filters={filters}
            setFilters={setFilters}
            applyFilters={applyFilters}
          />

          <div className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onOpen={openProduct}
                onAdd={addToCart}
                onFavorite={toggleFavorite}
              />
            ))}
          </div>

          {products.length === 0 && (
            <div className="glass mt-8 rounded-3xl p-10 text-center">
              <PackageCheck className="mx-auto text-cyan-300" size={42} />
              <h3 className="mt-4 text-2xl font-black">No encontramos productos</h3>
              <p className="mt-2 text-slate-400">
                Prueba cambiando los filtros o buscando otra categoría.
              </p>
            </div>
          )}
        </section>
      </section>

      <OrdersSection orders={orders} />

      <CartDrawer
        open={cartOpen}
        cart={cart}
        onClose={() => setCartOpen(false)}
        onUpdate={updateCartItem}
        onRemove={removeCartItem}
        onClear={clearCart}
        onCheckout={() => setCheckoutOpen(true)}
      />

      <ProductModal
        product={selectedProduct}
        onClose={() => setSelectedProduct(null)}
        onAdd={addToCart}
        onFavorite={toggleFavorite}
      />

      <CheckoutModal
        open={checkoutOpen}
        cart={cart}
        onClose={() => setCheckoutOpen(false)}
        onCheckout={checkout}
      />

      <OrderSuccessModal
        order={orderSuccess}
        onClose={() => setOrderSuccess(null)}
      />

      <Toast message={toast} />
    </main>
  );
}

function TopBar({ totalItems, onCart }) {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex w-[min(1420px,calc(100%-32px))] items-center justify-between py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-violet-600 to-cyan-400 shadow-glow">
            <Gamepad2 />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight">RealidadStore2</h1>
            <p className="text-xs font-semibold text-cyan-300">VR · AR · Gaming Ecommerce</p>
          </div>
        </div>

        <nav className="hidden items-center gap-7 text-sm font-bold text-slate-300 md:flex">
          <a href="#catalogo" className="hover:text-cyan-300">Catálogo</a>
          <a href="#ofertas" className="hover:text-cyan-300">Ofertas</a>
          <a href="#ordenes" className="hover:text-cyan-300">Mis órdenes</a>
        </nav>

        <button
          onClick={onCart}
          className="relative flex items-center gap-2 rounded-2xl bg-white px-5 py-3 font-black text-slate-950 transition hover:scale-[1.02]"
        >
          <ShoppingCart size={19} />
          Carrito
          {totalItems > 0 && (
            <span className="absolute -right-2 -top-2 grid h-7 w-7 place-items-center rounded-full bg-cyan-400 text-xs font-black text-slate-950">
              {totalItems}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}

function Hero({ summary, filters, setFilters, applyFilters }) {
  return (
    <section className="mx-auto grid w-[min(1420px,calc(100%-32px))] grid-cols-1 gap-6 pt-10 lg:grid-cols-[1.1fr_.9fr]">
      <div className="glass overflow-hidden rounded-[2.2rem] p-8 shadow-2xl lg:p-12">
        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-sm font-black text-cyan-200">
          <Sparkles size={17} />
          Gaming Week · Envío gratis desde $5,000
        </div>

        <h2 className="mt-8 max-w-3xl text-5xl font-black leading-[0.95] tracking-[-0.06em] md:text-7xl">
          Equipa tu mundo inmersivo.
        </h2>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          Visores VR, lentes AR, accesorios hápticos, juegos digitales y hardware gaming
          en una tienda desplegada sobre Kubernetes con backend real y base persistente.
        </p>

        <div className="mt-8 flex flex-col gap-3 rounded-3xl bg-slate-950/60 p-3 md:flex-row">
          <div className="flex flex-1 items-center gap-3 rounded-2xl bg-white/5 px-4">
            <Search className="text-cyan-300" size={21} />
            <input
              value={filters.search}
              onChange={(event) => setFilters({ ...filters, search: event.target.value })}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  applyFilters();
                }
              }}
              placeholder="Buscar Meta Quest, GPU, audífonos..."
              className="w-full bg-transparent py-4 text-white outline-none placeholder:text-slate-500"
            />
          </div>

          <button
            onClick={() => applyFilters()}
            className="rounded-2xl bg-cyan-300 px-6 py-4 font-black text-slate-950 transition hover:bg-cyan-200"
          >
            Buscar
          </button>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4">
          <HeroMetric icon={<Boxes />} label="Productos" value={summary?.products ?? '--'} />
          <HeroMetric icon={<SlidersHorizontal />} label="Categorías" value={summary?.categories ?? '--'} />
          <HeroMetric icon={<Zap />} label="Stock" value={summary?.stock_units ?? '--'} />
          <HeroMetric icon={<PackageCheck />} label="Órdenes" value={summary?.orders ?? '--'} />
        </div>
      </div>

      <div id="ofertas" className="glass relative overflow-hidden rounded-[2.2rem] p-6">
        <div className="absolute inset-0 bg-gradient-to-br from-violet-600/20 via-transparent to-cyan-400/20" />
        <div className="relative">
          <div className="rounded-[1.8rem] bg-slate-950/60 p-5">
            <img
              src="https://images.unsplash.com/photo-1593508512255-86ab42a8e620?auto=format&fit=crop&w=1000&q=80"
              alt="Oferta VR"
              className="h-80 w-full rounded-[1.4rem] object-cover"
            />
          </div>

          <div className="mt-6">
            <p className="text-sm font-black uppercase tracking-[0.25em] text-cyan-300">
              Oferta destacada
            </p>
            <h3 className="mt-3 text-3xl font-black">Bundle VR Starter Pack</h3>
            <p className="mt-3 text-slate-300">
              Paquete con visor, controles, audio y juego digital. Ideal para demo y usuarios nuevos.
            </p>

            <button
              onClick={() => {
                setFilters({ ...filters, featured: true });
                applyFilters({ ...filters, featured: true });
              }}
              className="mt-6 rounded-2xl bg-white px-5 py-3 font-black text-slate-950"
            >
              Ver destacados
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function HeroMetric({ icon, label, value }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-4">
      <div className="text-cyan-300">{icon}</div>
      <p className="mt-3 text-xs font-bold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <strong className="mt-1 block text-2xl font-black">{value}</strong>
    </div>
  );
}

function FiltersPanel({ categories, filters, setFilters, applyFilters, resetFilters }) {
  return (
    <aside className="glass sticky top-24 h-max rounded-[2rem] p-5">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-black">
          <Filter size={19} className="text-cyan-300" />
          Filtros
        </h2>
        <button
          onClick={resetFilters}
          className="rounded-xl bg-white/10 px-3 py-2 text-xs font-black text-white hover:bg-white/20"
        >
          Limpiar
        </button>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <label className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">
            Categoría
          </label>
          <div className="mt-3 grid gap-2">
            <button
              onClick={() => {
                const next = { ...filters, category: '' };
                setFilters(next);
                applyFilters(next);
              }}
              className={`rounded-2xl px-4 py-3 text-left font-bold ${
                filters.category === '' ? 'bg-cyan-300 text-slate-950' : 'bg-white/5 text-slate-300'
              }`}
            >
              Todas
            </button>

            {categories.map((category) => (
              <button
                key={category.name}
                onClick={() => {
                  const next = { ...filters, category: category.name };
                  setFilters(next);
                  applyFilters(next);
                }}
                className={`flex items-center justify-between rounded-2xl px-4 py-3 text-left font-bold ${
                  filters.category === category.name ? 'bg-cyan-300 text-slate-950' : 'bg-white/5 text-slate-300'
                }`}
              >
                {category.name}
                <span className="text-xs opacity-70">{category.count}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">
            Precio
          </label>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <input
              type="number"
              placeholder="Mín"
              value={filters.minPrice}
              onChange={(event) => setFilters({ ...filters, minPrice: event.target.value })}
              className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
            />
            <input
              type="number"
              placeholder="Máx"
              value={filters.maxPrice}
              onChange={(event) => setFilters({ ...filters, maxPrice: event.target.value })}
              className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
            />
          </div>
        </div>

        <label className="flex cursor-pointer items-center gap-3 rounded-2xl bg-white/5 p-4 font-bold text-slate-300">
          <input
            type="checkbox"
            checked={filters.inStock}
            onChange={(event) => setFilters({ ...filters, inStock: event.target.checked })}
          />
          Solo con stock
        </label>

        <label className="flex cursor-pointer items-center gap-3 rounded-2xl bg-white/5 p-4 font-bold text-slate-300">
          <input
            type="checkbox"
            checked={filters.featured}
            onChange={(event) => setFilters({ ...filters, featured: event.target.checked })}
          />
          Solo destacados
        </label>

        <button
          onClick={() => applyFilters()}
          className="w-full rounded-2xl bg-cyan-300 px-5 py-4 font-black text-slate-950"
        >
          Aplicar filtros
        </button>
      </div>
    </aside>
  );
}

function CatalogHeader({ count, loading, filters, setFilters, applyFilters }) {
  return (
    <div id="catalogo" className="glass rounded-[2rem] p-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-black uppercase tracking-[0.2em] text-cyan-300">
            Catálogo
          </p>
          <h2 className="mt-1 text-3xl font-black">
            {loading ? 'Cargando productos...' : `${count} producto(s) disponibles`}
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <ChevronDown className="text-slate-500" />
          <select
            value={filters.sort}
            onChange={(event) => {
              const next = { ...filters, sort: event.target.value };
              setFilters(next);
              applyFilters(next);
            }}
            className="rounded-2xl border border-white/10 bg-slate-950 px-4 py-3 font-bold outline-none"
          >
            <option value="featured">Destacados</option>
            <option value="price_asc">Precio menor a mayor</option>
            <option value="price_desc">Precio mayor a menor</option>
            <option value="rating">Mejor calificados</option>
            <option value="sold">Más vendidos</option>
            <option value="newest">Más recientes</option>
          </select>
        </div>
      </div>
    </div>
  );
}

function ProductCard({ product, onOpen, onAdd, onFavorite }) {
  return (
    <article className="glass group overflow-hidden rounded-[2rem] transition duration-300 hover:-translate-y-1 hover:shadow-glow">
      <div className="relative h-60 overflow-hidden product-image">
        <img
          src={product.image_url}
          alt={product.name}
          className="h-full w-full object-cover transition duration-500 group-hover:scale-110"
        />

        <div className="absolute left-4 top-4 rounded-full bg-slate-950/80 px-3 py-1 text-xs font-black text-cyan-200 backdrop-blur">
          {product.category}
        </div>

        {product.featured && (
          <div className="absolute bottom-4 left-4 rounded-full bg-cyan-300 px-3 py-1 text-xs font-black text-slate-950">
            Destacado
          </div>
        )}

        <button
          onClick={() => onFavorite(product)}
          className={`absolute right-4 top-4 grid h-11 w-11 place-items-center rounded-full backdrop-blur ${
            product.favorite ? 'bg-pink-500 text-white' : 'bg-slate-950/70 text-white'
          }`}
        >
          <Heart size={19} fill={product.favorite ? 'currentColor' : 'none'} />
        </button>
      </div>

      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-black text-violet-300">{product.brand}</p>
            <h3 className="mt-1 text-xl font-black leading-tight">{product.name}</h3>
          </div>

          <div className="flex items-center gap-1 rounded-full bg-amber-400/10 px-2 py-1 text-sm font-black text-amber-300">
            <Star size={15} fill="currentColor" />
            {product.rating}
          </div>
        </div>

        <p className="mt-3 line-clamp-2 min-h-12 text-sm leading-6 text-slate-400">
          {product.description}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {product.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="rounded-full bg-white/5 px-3 py-1 text-xs font-bold text-slate-300">
              {tag}
            </span>
          ))}
        </div>

        <div className="mt-5 flex items-end justify-between gap-4">
          <div>
            {product.old_price && (
              <p className="text-sm font-bold text-slate-500 line-through">
                {currency(product.old_price)}
              </p>
            )}
            <p className="text-2xl font-black text-white">{currency(product.price)}</p>
            <p className="text-xs font-bold text-slate-500">Stock: {product.stock}</p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onOpen(product.id)}
              className="rounded-2xl bg-white/10 px-4 py-3 font-black text-white hover:bg-white/20"
            >
              Ver
            </button>
            <button
              onClick={() => onAdd(product.id)}
              className="rounded-2xl bg-cyan-300 px-4 py-3 font-black text-slate-950 hover:bg-cyan-200"
            >
              Agregar
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function CartDrawer({ open, cart, onClose, onUpdate, onRemove, onClear, onCheckout }) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50">
      <button className="absolute inset-0 bg-slate-950/70" onClick={onClose} />

      <aside className="absolute right-0 top-0 h-full w-full max-w-[480px] overflow-auto bg-slate-950 p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-black">Carrito</h2>
          <button onClick={onClose} className="rounded-2xl bg-white/10 p-3">
            <X />
          </button>
        </div>

        <div className="mt-6 space-y-4">
          {cart.items.length === 0 && (
            <div className="rounded-3xl border border-dashed border-white/15 p-8 text-center text-slate-400">
              Tu carrito está vacío.
            </div>
          )}

          {cart.items.map((item) => (
            <div key={item.id} className="rounded-3xl bg-white/[0.04] p-4">
              <div className="flex gap-4">
                <img src={item.image_url} alt={item.name} className="h-24 w-24 rounded-2xl object-cover" />

                <div className="flex-1">
                  <h3 className="font-black">{item.name}</h3>
                  <p className="text-sm text-slate-400">{item.brand}</p>
                  <p className="mt-2 font-black text-cyan-300">{currency(item.subtotal)}</p>

                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center rounded-2xl bg-slate-900">
                      <button
                        onClick={() => onUpdate(item.id, item.quantity - 1)}
                        className="bg-transparent p-2"
                      >
                        <Minus size={16} />
                      </button>
                      <span className="px-3 font-black">{item.quantity}</span>
                      <button
                        onClick={() => onUpdate(item.id, item.quantity + 1)}
                        className="bg-transparent p-2"
                      >
                        <Plus size={16} />
                      </button>
                    </div>

                    <button onClick={() => onRemove(item.id)} className="bg-red-500/10 p-2 text-red-300">
                      <Trash2 size={17} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 rounded-3xl bg-white/[0.04] p-5">
          <div className="flex items-center justify-between text-lg">
            <span className="text-slate-400">Total</span>
            <strong className="text-3xl">{currency(cart.total)}</strong>
          </div>

          <button
            onClick={onCheckout}
            disabled={cart.items.length === 0}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 py-4 font-black text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <CreditCard size={19} />
            Finalizar compra
          </button>

          {cart.items.length > 0 && (
            <button
              onClick={onClear}
              className="mt-3 w-full rounded-2xl bg-white/10 px-5 py-3 font-black text-white"
            >
              Vaciar carrito
            </button>
          )}
        </div>
      </aside>
    </div>
  );
}

function ProductModal({ product, onClose, onAdd, onFavorite }) {
  if (!product) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <button className="absolute inset-0 bg-slate-950/80" onClick={onClose} />

      <section className="glass relative max-h-[90vh] w-full max-w-5xl overflow-auto rounded-[2rem] p-5">
        <button onClick={onClose} className="absolute right-5 top-5 z-10 rounded-2xl bg-slate-950/70 p-3">
          <X />
        </button>

        <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
          <img src={product.image_url} alt={product.name} className="h-full min-h-[420px] rounded-[1.5rem] object-cover" />

          <div className="p-2">
            <p className="font-black text-cyan-300">{product.category}</p>
            <h2 className="mt-2 text-4xl font-black leading-tight">{product.name}</h2>
            <p className="mt-2 text-violet-300 font-black">{product.brand}</p>

            <div className="mt-4 flex items-center gap-3">
              <span className="flex items-center gap-1 rounded-full bg-amber-400/10 px-3 py-1 font-black text-amber-300">
                <Star size={16} fill="currentColor" />
                {product.rating}
              </span>
              <span className="text-slate-400">{product.sold_count} vendidos</span>
            </div>

            <p className="mt-5 leading-8 text-slate-300">{product.description}</p>

            <div className="mt-6 grid grid-cols-2 gap-3">
              {Object.entries(product.specs || {}).map(([key, value]) => (
                <div key={key} className="rounded-2xl bg-white/[0.04] p-4">
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">{key}</p>
                  <p className="mt-1 font-bold">{value}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 flex items-end justify-between">
              <div>
                {product.old_price && (
                  <p className="text-lg font-bold text-slate-500 line-through">{currency(product.old_price)}</p>
                )}
                <p className="text-4xl font-black">{currency(product.price)}</p>
                <p className="mt-1 font-bold text-slate-400">Stock disponible: {product.stock}</p>
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => onAdd(product.id)}
                className="flex-1 rounded-2xl bg-cyan-300 px-5 py-4 font-black text-slate-950"
              >
                Agregar al carrito
              </button>

              <button
                onClick={() => onFavorite(product)}
                className={`rounded-2xl px-5 py-4 font-black ${
                  product.favorite ? 'bg-pink-500 text-white' : 'bg-white/10 text-white'
                }`}
              >
                <Heart fill={product.favorite ? 'currentColor' : 'none'} />
              </button>
            </div>

            <div className="mt-8">
              <h3 className="text-xl font-black">Reseñas</h3>

              <div className="mt-3 space-y-3">
                {product.reviews?.length === 0 && (
                  <p className="text-slate-400">Este producto aún no tiene reseñas.</p>
                )}

                {product.reviews?.map((review) => (
                  <div key={review.id} className="rounded-2xl bg-white/[0.04] p-4">
                    <div className="flex items-center justify-between">
                      <strong>{review.username}</strong>
                      <span className="text-amber-300">{'★'.repeat(review.rating)}</span>
                    </div>
                    <p className="mt-2 text-slate-300">{review.comment}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function CheckoutModal({ open, cart, onClose, onCheckout }) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <button className="absolute inset-0 bg-slate-950/80" onClick={onClose} />

      <form onSubmit={onCheckout} className="glass relative w-full max-w-xl rounded-[2rem] p-6">
        <button type="button" onClick={onClose} className="absolute right-5 top-5 rounded-2xl bg-white/10 p-3">
          <X />
        </button>

        <h2 className="text-3xl font-black">Finalizar compra</h2>
        <p className="mt-2 text-slate-400">
          Simulación de checkout. La orden se guarda en PostgreSQL y descuenta stock.
        </p>

        <div className="mt-6 space-y-4">
          <input
            name="customer_name"
            required
            placeholder="Nombre completo"
            className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-4 outline-none"
          />
          <input
            name="customer_email"
            required
            type="email"
            placeholder="Correo electrónico"
            className="w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-4 outline-none"
          />
          <textarea
            name="shipping_address"
            required
            placeholder="Dirección de envío"
            className="min-h-28 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-4 outline-none"
          />
        </div>

        <div className="mt-6 rounded-2xl bg-white/[0.04] p-4">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Total a pagar</span>
            <strong className="text-3xl">{currency(cart.total)}</strong>
          </div>
        </div>

        <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 py-4 font-black text-slate-950">
          <CreditCard size={19} />
          Pagar orden
        </button>
      </form>
    </div>
  );
}

function OrderSuccessModal({ order, onClose }) {
  if (!order) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4">
      <button className="absolute inset-0 bg-slate-950/80" onClick={onClose} />

      <section className="glass relative w-full max-w-md rounded-[2rem] p-8 text-center">
        <div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-cyan-300 text-slate-950">
          <BadgeCheck size={42} />
        </div>

        <h2 className="mt-6 text-3xl font-black">Orden creada</h2>
        <p className="mt-2 text-slate-400">Tu compra fue registrada correctamente.</p>

        <div className="mt-6 rounded-3xl bg-white/[0.04] p-5">
          <p className="text-slate-400">Orden</p>
          <strong className="text-2xl">#{order.order_id}</strong>
          <p className="mt-3 text-slate-400">Total</p>
          <strong className="text-2xl text-cyan-300">{currency(order.total)}</strong>
        </div>

        <button onClick={onClose} className="mt-6 w-full rounded-2xl bg-white px-5 py-4 font-black text-slate-950">
          Continuar
        </button>
      </section>
    </div>
  );
}

function OrdersSection({ orders }) {
  return (
    <section id="ordenes" className="mx-auto w-[min(1420px,calc(100%-32px))] pb-16">
      <div className="glass rounded-[2rem] p-6">
        <div className="flex items-center gap-3">
          <Truck className="text-cyan-300" />
          <div>
            <p className="text-sm font-black uppercase tracking-[0.2em] text-cyan-300">Cliente actual</p>
            <h2 className="text-2xl font-black">Órdenes recientes</h2>
          </div>
        </div>

        {orders.length === 0 ? (
          <p className="mt-5 text-slate-400">Todavía no hay órdenes registradas para este cliente.</p>
        ) : (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {orders.slice(0, 4).map((order) => (
              <div key={order.id} className="rounded-3xl bg-white/[0.04] p-5">
                <div className="flex items-center justify-between">
                  <strong>Orden #{order.id}</strong>
                  <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs font-black text-cyan-300">
                    {order.status}
                  </span>
                </div>
                <p className="mt-2 text-slate-400">{order.customer_name}</p>
                <p className="mt-3 text-2xl font-black">{currency(order.total)}</p>
                <p className="mt-2 text-sm text-slate-500">{order.items.length} producto(s)</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function Toast({ message }) {
  return (
    <div className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2 rounded-full border border-white/10 bg-slate-950/90 px-5 py-3 text-sm font-bold text-white shadow-2xl backdrop-blur">
      {message}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);

const header = document.querySelector(".site-header");
const progress = document.querySelector(".scroll-progress");
const revealItems = document.querySelectorAll("[data-reveal]");
const productGrid = document.querySelector("[data-product-grid]");
const filterButtons = document.querySelectorAll("[data-filter]");
const cartPanel = document.querySelector("[data-cart-panel]");
const cartItemsEl = document.querySelector("[data-cart-items]");
const cartTotalEl = document.querySelector("[data-cart-total]");
const cartCountEls = document.querySelectorAll("[data-cart-count]");
const cartStatus = document.querySelector("[data-cart-status]");
const checkoutForm = document.querySelector("[data-checkout-form]");
const motionAllowed = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const products = [
  {
    id: "bolo-cambuci",
    category: "doce",
    name: "Bolo de cambuci",
    description: "Bolo caseiro com massa fofinha e calda azedinha de cambuci. Serve 6 fatias.",
    price: 42.9,
    image: "assets/bolo-verde.svg",
  },
  {
    id: "cachaca-cambuci",
    category: "bebida",
    name: "Cachaça de cambuci",
    description: "Garrafa 500ml infusionada com cambuci, aroma cítrico e final macio.",
    price: 59.9,
    image: "assets/cachaca-sem-rotulo.svg",
  },
  {
    id: "cambuci-congelado",
    category: "fruta",
    name: "Cambuci congelado kg",
    description: "Cambuci limpo e congelado em pacote de 1kg para sucos, molhos e sobremesas.",
    price: 34.9,
    image: "https://commons.wikimedia.org/wiki/Special:Redirect/file/Cambuci.jpg",
  },
  {
    id: "musse-cambuci",
    category: "doce",
    name: "Musse de cambuci",
    description: "Pote 250ml, cremoso, leve e com acidez equilibrada da fruta.",
    price: 18.9,
    image: "assets/musse-verde.svg",
  },
  {
    id: "sorvete-cambuci",
    category: "gelado",
    name: "Sorvete de cambuci",
    description: "Pote 500ml artesanal, refrescante e perfumado, feito em pequenas levas.",
    price: 36.9,
    image: "assets/sorvete-verde.svg",
  },
  {
    id: "licor-cambuci",
    category: "bebida",
    name: "Licor de cambuci",
    description: "Garrafa 375ml, doce aromático para servir gelado depois do almoço.",
    price: 49.9,
    image: "https://images.unsplash.com/photo-1547595628-c61a29f496f0?auto=format&fit=crop&w=900&q=82",
  },
];

const cart = new Map();
const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const syncHeader = () => {
  header.dataset.elevated = window.scrollY > 8 ? "true" : "false";
};

const syncProgress = () => {
  if (!progress || CSS.supports("animation-timeline: scroll(root block)")) return;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const value = scrollable > 0 ? window.scrollY / scrollable : 0;
  progress.style.setProperty("--progress", value.toFixed(4));
};

window.addEventListener("scroll", syncHeader, { passive: true });
window.addEventListener("scroll", syncProgress, { passive: true });
window.addEventListener("resize", syncProgress);
syncHeader();
syncProgress();

if (motionAllowed && revealItems.length > 0) {
  document.documentElement.classList.add("reveal-ready");
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.16 }
  );
  revealItems.forEach((item) => observer.observe(item));
}

const renderProducts = (category = "all") => {
  const items = category === "all" ? products : products.filter((product) => product.category === category);
  productGrid.innerHTML = items
    .map(
      (product) => `
        <article class="product-card" data-reveal>
          <img src="${product.image}" alt="${product.name}" />
          <div class="product-body">
            <div class="product-top">
              <h3>${product.name}</h3>
              <strong class="price">${currency.format(product.price)}</strong>
            </div>
            <p>${product.description}</p>
            <button class="add-button" type="button" data-add="${product.id}">Colocar na cestinha</button>
          </div>
        </article>
      `
    )
    .join("");
};

const cartTotal = () => {
  let total = 0;
  for (const [id, quantity] of cart) {
    const product = products.find((item) => item.id === id);
    total += product.price * quantity;
  }
  return total;
};

const cartCount = () => Array.from(cart.values()).reduce((sum, quantity) => sum + quantity, 0);

const updateCart = () => {
  cartCountEls.forEach((el) => {
    el.textContent = cartCount();
  });
  cartTotalEl.textContent = currency.format(cartTotal());

  if (cart.size === 0) {
    cartItemsEl.innerHTML = '<p class="cart-empty">Sua cestinha está vazia.</p>';
    return;
  }

  cartItemsEl.innerHTML = Array.from(cart.entries())
    .map(([id, quantity]) => {
      const product = products.find((item) => item.id === id);
      return `
        <article class="cart-item">
          <div>
            <strong>${product.name}</strong>
            <p>${currency.format(product.price)} cada</p>
          </div>
          <div class="qty-controls">
            <button type="button" data-dec="${product.id}" aria-label="Diminuir ${product.name}">−</button>
            <span>${quantity}</span>
            <button type="button" data-inc="${product.id}" aria-label="Aumentar ${product.name}">+</button>
          </div>
        </article>
      `;
    })
    .join("");
};

const addToCart = (id) => {
  cart.set(id, (cart.get(id) || 0) + 1);
  cartStatus.textContent = "";
  updateCart();
};

const openCart = () => {
  cartPanel.classList.add("is-open");
  cartPanel.setAttribute("aria-hidden", "false");
};

const closeCart = () => {
  cartPanel.classList.remove("is-open");
  cartPanel.setAttribute("aria-hidden", "true");
};

document.addEventListener("click", (event) => {
  const add = event.target.closest("[data-add]");
  const inc = event.target.closest("[data-inc]");
  const dec = event.target.closest("[data-dec]");
  const open = event.target.closest("[data-cart-open]");
  const close = event.target.closest("[data-cart-close]");

  if (add) {
    addToCart(add.dataset.add);
    openCart();
  }
  if (inc) addToCart(inc.dataset.inc);
  if (dec) {
    const id = dec.dataset.dec;
    const quantity = (cart.get(id) || 0) - 1;
    if (quantity <= 0) cart.delete(id);
    else cart.set(id, quantity);
    updateCart();
  }
  if (open) openCart();
  if (close) closeCart();
});

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    renderProducts(button.dataset.filter);
  });
});

checkoutForm.addEventListener("submit", (event) => {
  event.preventDefault();

  if (cart.size === 0) {
    cartStatus.textContent = "Coloque pelo menos um item na cestinha.";
    return;
  }

  const data = new FormData(checkoutForm);
  const customer = String(data.get("customer") || "").trim();
  const delivery = String(data.get("delivery") || "").trim();
  const address = String(data.get("address") || "").trim();
  const notes = String(data.get("notes") || "").trim();

  const lines = Array.from(cart.entries()).map(([id, quantity]) => {
    const product = products.find((item) => item.id === id);
    return `• ${quantity}x ${product.name} - ${currency.format(product.price * quantity)}`;
  });

  const message = [
    `Olá, Lili do Cambuci! Meu nome é ${customer}.`,
    "",
    "Quero fazer este pedido:",
    ...lines,
    "",
    `Total: ${currency.format(cartTotal())}`,
    `Forma: ${delivery}`,
    address ? `Endereço: ${address}` : "",
    notes ? `Recado: ${notes}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  const url = `https://wa.me/5511999999999?text=${encodeURIComponent(message)}`;
  cartStatus.textContent = "Pedido pronto. Abrindo WhatsApp.";
  window.open(url, "_blank", "noopener,noreferrer");
});

renderProducts();
updateCart();

if (new URLSearchParams(window.location.search).get("demoCart") === "1") {
  addToCart("bolo-cambuci");
  addToCart("cambuci-congelado");
  openCart();
}

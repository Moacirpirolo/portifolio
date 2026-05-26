const header = document.querySelector(".site-header");
const progress = document.querySelector(".scroll-progress");
const revealItems = document.querySelectorAll("[data-reveal]");
const menuGrid = document.querySelector("[data-menu-grid]");
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
    id: "gael-classic",
    category: "burger",
    name: "Gael Classic",
    description: "Blend 160g, cheddar, alface, tomate, picles e molho Gael no brioche.",
    price: 29.9,
    image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "smash-duplo",
    category: "burger",
    name: "Smash Duplo",
    description: "Dois smashs crocantes, cheddar duplo, cebola roxa e maionese da casa.",
    price: 34.9,
    image: "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "bbq-bacon",
    category: "burger",
    name: "BBQ Bacon",
    description: "Blend 180g, bacon caramelizado, queijo prato, crispy onion e barbecue.",
    price: 37.9,
    image: "https://images.unsplash.com/photo-1553979459-d2229ba7433b?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "brasa-picante",
    category: "burger",
    name: "Brasa Picante",
    description: "Blend 160g, pepper jack, jalapeno, rúcula e molho chipotle.",
    price: 35.9,
    image: "https://images.unsplash.com/photo-1606755962773-d324e2a13086?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "combo-gael",
    category: "combo",
    name: "Combo Gael Duplo",
    description: "Smash duplo, batata rústica e refrigerante lata.",
    price: 49.9,
    image: "https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "combo-familia",
    category: "combo",
    name: "Combo Família",
    description: "4 burgers classic, 2 batatas grandes e 4 refrigerantes lata.",
    price: 139.9,
    image: "https://images.unsplash.com/photo-1610614819513-58e34989848b?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "batata-rustica",
    category: "side",
    name: "Batata Rústica",
    description: "Batata temperada, páprica defumada e maionese verde.",
    price: 18.9,
    image: "https://images.unsplash.com/photo-1630384060421-cb20d0e0649d?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "onion-rings",
    category: "side",
    name: "Onion Rings",
    description: "Anéis de cebola empanados, crocantes e molho barbecue.",
    price: 21.9,
    image: "https://images.unsplash.com/photo-1639024471283-03518883512d?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "refri",
    category: "drink",
    name: "Refrigerante Lata",
    description: "Coca-Cola, Guaraná ou Sprite. Escolha nas observações.",
    price: 7.9,
    image: "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&w=900&q=84",
  },
  {
    id: "milkshake",
    category: "drink",
    name: "Milkshake",
    description: "Chocolate, morango ou baunilha, 400ml.",
    price: 19.9,
    image: "https://images.unsplash.com/photo-1572490122747-3968b75cc699?auto=format&fit=crop&w=900&q=84",
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

const renderMenu = (category = "all") => {
  const items = category === "all" ? products : products.filter((product) => product.category === category);
  menuGrid.innerHTML = items
    .map(
      (product) => `
        <article class="menu-card" data-reveal>
          <img src="${product.image}" alt="${product.name}" />
          <div class="menu-card-body">
            <div class="menu-card-top">
              <h3>${product.name}</h3>
              <strong class="price">${currency.format(product.price)}</strong>
            </div>
            <p>${product.description}</p>
            <button class="add-button" type="button" data-add="${product.id}">Adicionar</button>
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
    cartItemsEl.innerHTML = '<p class="cart-empty">Seu carrinho está vazio.</p>';
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
  if (inc) {
    addToCart(inc.dataset.inc);
  }
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
    renderMenu(button.dataset.filter);
  });
});

document.querySelector("[data-featured-add]").addEventListener("click", () => {
  addToCart("combo-gael");
  openCart();
});

checkoutForm.addEventListener("submit", (event) => {
  event.preventDefault();

  if (cart.size === 0) {
    cartStatus.textContent = "Adicione pelo menos um item ao carrinho.";
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
    `Olá, Gael Burger! Meu nome é ${customer}.`,
    "",
    "Quero fazer este pedido:",
    ...lines,
    "",
    `Total: ${currency.format(cartTotal())}`,
    `Forma: ${delivery}`,
    address ? `Endereço: ${address}` : "",
    notes ? `Observações: ${notes}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  const url = `https://wa.me/5511999999999?text=${encodeURIComponent(message)}`;
  cartStatus.textContent = "Pedido pronto. Abrindo WhatsApp.";
  window.open(url, "_blank", "noopener,noreferrer");
});

renderMenu();
updateCart();

if (new URLSearchParams(window.location.search).get("demoCart") === "1") {
  addToCart("smash-duplo");
  addToCart("batata-rustica");
  openCart();
}

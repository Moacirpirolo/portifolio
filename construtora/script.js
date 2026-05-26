const header = document.querySelector(".site-header");
const progress = document.querySelector(".scroll-progress");
const revealItems = document.querySelectorAll("[data-reveal]");
const form = document.querySelector("#contact-form");
const statusEl = document.querySelector("#form-status");
const motionAllowed = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const carousel = document.querySelector("[data-carousel]");

const syncHeader = () => {
  header.dataset.elevated = window.scrollY > 8 ? "true" : "false";
};

const syncProgress = () => {
  if (!progress || CSS.supports("animation-timeline: scroll(root block)")) {
    return;
  }

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

if (carousel) {
  const track = carousel.querySelector(".carousel-track");
  const cards = Array.from(carousel.querySelectorAll(".work-card"));
  const prev = carousel.querySelector("[data-prev]");
  const next = carousel.querySelector("[data-next]");
  const current = carousel.querySelector("[data-current]");
  const total = carousel.querySelector("[data-total]");
  const dots = carousel.querySelector(".carousel-dots");
  let index = 0;

  const perView = () => {
    if (window.matchMedia("(max-width: 680px)").matches) return 1;
    if (window.matchMedia("(max-width: 1040px)").matches) return 2;
    return 3;
  };

  const maxIndex = () => Math.max(cards.length - perView(), 0);
  const formatNumber = (value) => String(value).padStart(2, "0");

  const renderDots = () => {
    dots.innerHTML = "";
    for (let dotIndex = 0; dotIndex <= maxIndex(); dotIndex += 1) {
      const button = document.createElement("button");
      button.type = "button";
      button.setAttribute("aria-label", `Ir para obra ${dotIndex + 1}`);
      button.addEventListener("click", () => {
        index = dotIndex;
        updateCarousel();
      });
      dots.append(button);
    }
  };

  function updateCarousel() {
    index = Math.min(Math.max(index, 0), maxIndex());
    const card = cards[0];
    const gap = Number.parseFloat(getComputedStyle(track).columnGap) || 0;
    const step = card.getBoundingClientRect().width + gap;
    track.style.transform = `translateX(${-index * step}px)`;
    current.textContent = formatNumber(index + 1);
    total.textContent = formatNumber(cards.length);
    Array.from(dots.children).forEach((dot, dotIndex) => {
      dot.setAttribute("aria-current", dotIndex === index ? "true" : "false");
    });
  }

  prev.addEventListener("click", () => {
    index = index <= 0 ? maxIndex() : index - 1;
    updateCarousel();
  });

  next.addEventListener("click", () => {
    index = index >= maxIndex() ? 0 : index + 1;
    updateCarousel();
  });

  window.addEventListener("resize", () => {
    renderDots();
    updateCarousel();
  });

  renderDots();
  updateCarousel();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const name = String(data.get("name") || "").trim();
  const phone = String(data.get("phone") || "").trim();
  const project = String(data.get("project") || "").trim();
  const messageText = String(data.get("message") || "").trim();

  if (!name || !phone || !project) {
    statusEl.textContent = "Preencha nome, WhatsApp e tipo de projeto para solicitar retorno.";
    return;
  }

  const message = `Olá, sou ${name}. Quero falar sobre ${project}. Meu WhatsApp é ${phone}.${messageText ? ` Observações: ${messageText}` : ""}`;
  const url = `https://wa.me/5511999999999?text=${encodeURIComponent(message)}`;

  statusEl.textContent = "Solicitação pronta. Abrindo WhatsApp para confirmação.";
  window.open(url, "_blank", "noopener,noreferrer");
  form.reset();
});

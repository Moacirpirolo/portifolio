const header = document.querySelector(".site-header");
const form = document.querySelector("#booking-form");
const statusEl = document.querySelector("#form-status");
const progress = document.querySelector(".scroll-progress");
const revealItems = document.querySelectorAll("[data-reveal]");
const motionAllowed = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const syncHeader = () => {
  header.dataset.elevated = window.scrollY > 8 ? "true" : "false";
};

window.addEventListener("scroll", syncHeader, { passive: true });
syncHeader();

const syncProgress = () => {
  if (!progress || CSS.supports("animation-timeline: scroll(root block)")) {
    return;
  }

  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const value = scrollable > 0 ? window.scrollY / scrollable : 0;
  progress.style.setProperty("--progress", value.toFixed(4));
};

window.addEventListener("scroll", syncProgress, { passive: true });
window.addEventListener("resize", syncProgress);
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
    { threshold: 0.18 }
  );

  revealItems.forEach((item) => observer.observe(item));
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const data = new FormData(form);
  const name = String(data.get("name") || "").trim();
  const phone = String(data.get("phone") || "").trim();
  const service = String(data.get("service") || "").trim();
  const period = String(data.get("period") || "").trim();

  if (!name || !phone || !service || !period) {
    statusEl.textContent = "Preencha todos os campos para solicitar o agendamento.";
    return;
  }

  const message = `Olá, sou ${name}. Quero agendar ${service} no período da ${period}. Meu WhatsApp é ${phone}.`;
  const url = `https://wa.me/5511999999999?text=${encodeURIComponent(message)}`;

  statusEl.textContent = "Solicitação pronta. Abrindo WhatsApp para confirmação.";
  window.open(url, "_blank", "noopener,noreferrer");
  form.reset();
});

const header = document.querySelector(".site-header");
const progress = document.querySelector(".scroll-progress");
const revealItems = document.querySelectorAll("[data-reveal]");
const motionAllowed = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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

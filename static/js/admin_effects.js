/**
 * Digsell.uz Django Admin — Animated starfield & UI polish
 */
(function () {
  'use strict';

  function createStarfield(target) {
    const canvas = document.createElement('canvas');
    canvas.id = 'digsell-admin-stars';
    canvas.setAttribute('aria-hidden', 'true');
    target.insertBefore(canvas, target.firstChild);

    const ctx = canvas.getContext('2d');
    let w, h, stars, meteors, raf;
    const STAR_COUNT = 180;
    const METEOR_COUNT = 4;

    function resize() {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    }

    function initStars() {
      stars = Array.from({ length: STAR_COUNT }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.4 + 0.3,
        a: Math.random(),
        speed: Math.random() * 0.015 + 0.004,
        twinkle: Math.random() * Math.PI * 2,
      }));
      meteors = Array.from({ length: METEOR_COUNT }, () => ({
        x: Math.random() * w,
        y: Math.random() * h * 0.5,
        len: Math.random() * 60 + 40,
        speed: Math.random() * 6 + 4,
        opacity: 0,
        delay: Math.random() * 300,
        tick: 0,
      }));
    }

    function drawGrid() {
      ctx.strokeStyle = 'rgba(255, 23, 68, 0.03)';
      ctx.lineWidth = 1;
      const gap = 60;
      for (let x = 0; x < w; x += gap) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gap) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
    }

    function drawNebula() {
      const g1 = ctx.createRadialGradient(w * 0.15, h * 0.1, 0, w * 0.15, h * 0.1, w * 0.45);
      g1.addColorStop(0, 'rgba(255, 23, 68, 0.07)');
      g1.addColorStop(1, 'transparent');
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, w, h);

      const g2 = ctx.createRadialGradient(w * 0.85, h * 0.85, 0, w * 0.85, h * 0.85, w * 0.35);
      g2.addColorStop(0, 'rgba(180, 0, 40, 0.05)');
      g2.addColorStop(1, 'transparent');
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, w, h);
    }

    function frame() {
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, w, h);
      drawNebula();
      drawGrid();

      stars.forEach((s) => {
        s.twinkle += s.speed;
        const alpha = 0.25 + Math.abs(Math.sin(s.twinkle)) * 0.75;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, ${120 + Math.floor(s.a * 80)}, ${140 + Math.floor(s.a * 60)}, ${alpha})`;
        ctx.fill();
        if (s.r > 1) {
          ctx.shadowBlur = 8;
          ctx.shadowColor = 'rgba(255, 23, 68, 0.6)';
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      });

      meteors.forEach((m) => {
        m.tick++;
        if (m.tick < m.delay) return;
        m.opacity = Math.min(m.opacity + 0.02, 0.9);
        m.x += m.speed * 2.2;
        m.y += m.speed;
        const grad = ctx.createLinearGradient(m.x, m.y, m.x - m.len, m.y - m.len * 0.4);
        grad.addColorStop(0, `rgba(255, 80, 100, ${m.opacity})`);
        grad.addColorStop(1, 'transparent');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(m.x, m.y);
        ctx.lineTo(m.x - m.len, m.y - m.len * 0.4);
        ctx.stroke();
        if (m.x > w + 100 || m.y > h + 100) {
          m.x = Math.random() * w * 0.3;
          m.y = Math.random() * h * 0.3;
          m.opacity = 0;
          m.tick = 0;
          m.delay = Math.random() * 400 + 100;
        }
      });

      raf = requestAnimationFrame(frame);
    }

    resize();
    initStars();
    frame();
    window.addEventListener('resize', () => { resize(); initStars(); });

    return () => { cancelAnimationFrame(raf); canvas.remove(); };
  }

  function animateOnScroll() {
    const els = document.querySelectorAll('.card, .info-box, .model-card, #result_list tbody tr, .module');
    els.forEach((el, i) => {
      if (!el.classList.contains('digsell-fade-up')) {
        el.classList.add('digsell-fade-up');
        el.style.animationDelay = `${Math.min(i * 0.04, 0.6)}s`;
      }
    });
  }

  function polishSidebar() {
    document.querySelectorAll('.nav-sidebar .nav-link').forEach((link) => {
      link.addEventListener('mouseenter', () => link.classList.add('digsell-nav-glow'));
      link.addEventListener('mouseleave', () => link.classList.remove('digsell-nav-glow'));
    });
  }

  function init() {
    createStarfield(document.body);
    document.body.classList.add('digsell-admin-ready');
    animateOnScroll();
    polishSidebar();

    const main = document.querySelector('.content-wrapper') || document.body;
    const observer = new MutationObserver(() => {
      observer.disconnect();
      animateOnScroll();
      observer.observe(main, { childList: true, subtree: true });
    });
    observer.observe(main, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

/* ==========================================================================
   SkillGuard — animations.js
   Procedural hero background animations per theme.
   Each theme has a unique canvas-based or CSS-based effect.
   Respects prefers-reduced-motion.
   ========================================================================== */

(function () {
  'use strict';

  var canvas = document.getElementById('hero-bg');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var animId = null;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function resize() {
    var hero = canvas.parentElement;
    canvas.width = hero.offsetWidth;
    canvas.height = hero.offsetHeight;
  }

  window.addEventListener('resize', resize);
  resize();

  // --- Shared: Orb class ---
  function Orb(x, y, r, color, speed) {
    this.x = x;
    this.y = y;
    this.baseX = x;
    this.baseY = y;
    this.r = r;
    this.color = color;
    this.speed = speed;
    this.angle = Math.random() * Math.PI * 2;
    this.drift = 30 + Math.random() * 40;
  }

  Orb.prototype.update = function (t) {
    this.x = this.baseX + Math.sin(this.angle + t * this.speed) * this.drift;
    this.y = this.baseY + Math.cos(this.angle + t * this.speed * 0.7) * this.drift * 0.6;
  };

  Orb.prototype.draw = function (ctx) {
    var gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.r);
    gradient.addColorStop(0, this.color);
    gradient.addColorStop(1, 'transparent');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fill();
  };

  // --- KAZE: Aurora orbs ---
  function initKaze() {
    var orbs = [];
    var w = canvas.width;
    var h = canvas.height;

    orbs.push(new Orb(w * 0.2, h * 0.3, w * 0.3, 'rgba(255, 168, 247, 0.12)', 0.0003));
    orbs.push(new Orb(w * 0.7, h * 0.5, w * 0.25, 'rgba(9, 125, 255, 0.1)', 0.0004));
    orbs.push(new Orb(w * 0.5, h * 0.2, w * 0.2, 'rgba(203, 128, 255, 0.08)', 0.0002));
    orbs.push(new Orb(w * 0.8, h * 0.8, w * 0.2, 'rgba(255, 168, 247, 0.06)', 0.00035));

    return function (t) {
      ctx.clearRect(0, 0, w, h);
      orbs.forEach(function (orb) {
        orb.update(t);
        orb.draw(ctx);
      });
    };
  }

  // --- KAGAMI: Metallic grid shimmer ---
  function initKagami() {
    var w = canvas.width;
    var h = canvas.height;
    var cellSize = 60;

    return function (t) {
      ctx.clearRect(0, 0, w, h);
      var cols = Math.ceil(w / cellSize);
      var rows = Math.ceil(h / cellSize);

      for (var i = 0; i < cols; i++) {
        for (var j = 0; j < rows; j++) {
          var x = i * cellSize;
          var y = j * cellSize;
          var dist = Math.sqrt(Math.pow(x - w / 2, 2) + Math.pow(y - h / 2, 2));
          var wave = Math.sin(dist * 0.005 - t * 0.0008) * 0.5 + 0.5;
          var alpha = wave * 0.04;
          ctx.fillStyle = 'rgba(192, 192, 220, ' + alpha + ')';
          ctx.fillRect(x, y, cellSize - 1, cellSize - 1);
        }
      }
    };
  }

  // --- KURAGE: Floating jellyfish circles ---
  function initKurage() {
    var w = canvas.width;
    var h = canvas.height;
    var jellies = [];

    for (var i = 0; i < 8; i++) {
      jellies.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: 20 + Math.random() * 60,
        speed: 0.2 + Math.random() * 0.5,
        phase: Math.random() * Math.PI * 2,
        opacity: 0.03 + Math.random() * 0.06
      });
    }

    return function (t) {
      ctx.clearRect(0, 0, w, h);
      jellies.forEach(function (j) {
        var y = j.y - (t * j.speed * 0.02) % (h + j.r * 2);
        if (y < -j.r) y += h + j.r * 2;

        var pulse = Math.sin(t * 0.001 + j.phase) * 0.5 + 0.5;
        var alpha = j.opacity + pulse * 0.03;
        var r = j.r + pulse * 5;

        var gradient = ctx.createRadialGradient(j.x, y, 0, j.x, y, r);
        gradient.addColorStop(0, 'rgba(0, 255, 200, ' + (alpha * 1.5) + ')');
        gradient.addColorStop(0.5, 'rgba(139, 92, 246, ' + alpha + ')');
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(j.x, y, r, 0, Math.PI * 2);
        ctx.fill();
      });
    };
  }

  // --- MYAKU: Golden vein branches ---
  function initMyaku() {
    var w = canvas.width;
    var h = canvas.height;
    var branches = [];

    // Generate branch paths
    function addBranch(x, y, angle, len, depth) {
      if (depth > 6 || len < 5) return;
      var endX = x + Math.cos(angle) * len;
      var endY = y + Math.sin(angle) * len;
      branches.push({ x1: x, y1: y, x2: endX, y2: endY, depth: depth });

      // Branch out
      addBranch(endX, endY, angle + 0.3 + Math.random() * 0.3, len * 0.7, depth + 1);
      addBranch(endX, endY, angle - 0.3 - Math.random() * 0.3, len * 0.7, depth + 1);
    }

    addBranch(w * 0.5, h * 0.9, -Math.PI / 2, h * 0.18, 0);
    addBranch(w * 0.3, h * 0.7, -Math.PI / 2.5, h * 0.12, 1);
    addBranch(w * 0.7, h * 0.7, -Math.PI / 1.7, h * 0.12, 1);

    return function (t) {
      ctx.clearRect(0, 0, w, h);
      branches.forEach(function (b, i) {
        var progress = ((t * 0.0003 + i * 0.05) % 2);
        if (progress > 1) progress = 2 - progress;
        var alpha = 0.05 + progress * 0.12;
        var lineWidth = Math.max(0.5, 3 - b.depth * 0.4);

        ctx.strokeStyle = 'rgba(201, 168, 76, ' + alpha + ')';
        ctx.lineWidth = lineWidth;
        ctx.beginPath();
        ctx.moveTo(b.x1, b.y1);
        ctx.lineTo(b.x2, b.y2);
        ctx.stroke();
      });
    };
  }

  // --- SUMI: Minimal (no canvas, CSS-only) ---
  function initSumi() {
    return function () {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }

  // --- Engine ---
  var renderers = {
    kaze: initKaze,
    kagami: initKagami,
    kurage: initKurage,
    myaku: initMyaku,
    sumi: initSumi
  };

  var currentRender = null;
  var lastFrame = 0;
  var FPS_INTERVAL = 1000 / 30; // Cap at 30fps

  function loop(timestamp) {
    animId = requestAnimationFrame(loop);
    var elapsed = timestamp - lastFrame;
    if (elapsed < FPS_INTERVAL) return;
    lastFrame = timestamp - (elapsed % FPS_INTERVAL);

    if (currentRender) {
      currentRender(timestamp);
    }
  }

  function init(themeName) {
    // Cancel previous animation
    if (animId) {
      cancelAnimationFrame(animId);
      animId = null;
    }

    resize();

    if (reducedMotion) {
      // Static fallback: just clear the canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    var factory = renderers[themeName] || renderers.kaze;
    currentRender = factory();
    lastFrame = 0;
    animId = requestAnimationFrame(loop);
  }

  // Expose for main.js theme switching
  window.SGAnimations = { init: init };

  // Initialize with current theme
  var currentTheme = document.documentElement.getAttribute('data-theme') || 'kaze';
  init(currentTheme);

})();

/* ==========================================================================
   SkillGuard — main.js
   Core: theme switching, dark/light mode, scroll observer, clipboard, nav.
   Zero dependencies.
   ========================================================================== */

(function () {
  'use strict';

  // --- Theme Switching ---
  var THEMES = ['kaze', 'kagami', 'kurage', 'myaku', 'sumi'];
  var themeLink = document.getElementById('theme-css');
  var themePanel = document.getElementById('theme-panel');
  var themeToggleBtn = document.getElementById('theme-toggle-btn');
  var themeOptions = document.querySelectorAll('.sg-theme-option');

  function setTheme(name) {
    if (THEMES.indexOf(name) === -1) name = 'kaze';
    themeLink.href = './css/themes/' + name + '.css';
    document.documentElement.setAttribute('data-theme', name);
    localStorage.setItem('sg-theme', name);

    // Update active state in panel
    themeOptions.forEach(function (opt) {
      opt.classList.toggle('active', opt.getAttribute('data-theme') === name);
    });

    // Re-init background animation
    if (window.SGAnimations && window.SGAnimations.init) {
      window.SGAnimations.init(name);
    }
  }

  // Theme panel toggle
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
      var isHidden = themePanel.hasAttribute('hidden');
      if (isHidden) {
        themePanel.removeAttribute('hidden');
      } else {
        themePanel.setAttribute('hidden', '');
      }
    });
  }

  // Theme option clicks
  themeOptions.forEach(function (opt) {
    opt.addEventListener('click', function () {
      setTheme(this.getAttribute('data-theme'));
    });
  });

  // Close panel when clicking outside
  document.addEventListener('click', function (e) {
    if (themePanel && !themePanel.contains(e.target) && e.target !== themeToggleBtn && !themeToggleBtn.contains(e.target)) {
      themePanel.setAttribute('hidden', '');
    }
  });

  // Apply saved theme on load
  var savedTheme = localStorage.getItem('sg-theme') || 'kaze';
  setTheme(savedTheme);

  // --- Dark/Light Mode ---
  var modeBtn = document.getElementById('mode-toggle-btn');
  var modeLabel = document.getElementById('mode-label');

  function setMode(mode) {
    document.documentElement.setAttribute('data-mode', mode);
    localStorage.setItem('sg-mode', mode);
    if (modeLabel) modeLabel.textContent = mode === 'dark' ? 'Dark' : 'Light';
  }

  if (modeBtn) {
    modeBtn.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-mode') || 'dark';
      setMode(current === 'dark' ? 'light' : 'dark');
    });
  }

  // Apply saved mode
  var savedMode = localStorage.getItem('sg-mode');
  if (!savedMode) {
    // Detect system preference on first visit
    savedMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  setMode(savedMode);

  // --- Scroll Animation Observer ---
  var scrollElements = document.querySelectorAll('.sg-animate-on-scroll');

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('sg-visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -40px 0px'
    });

    scrollElements.forEach(function (el) {
      observer.observe(el);
    });
  } else {
    // Fallback: show all immediately
    scrollElements.forEach(function (el) {
      el.classList.add('sg-visible');
    });
  }

  // --- Copy to Clipboard ---
  document.querySelectorAll('.sg-terminal__copy').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = this.getAttribute('data-copy');
      if (!text) return;

      var self = this;
      navigator.clipboard.writeText(text).then(function () {
        self.classList.add('copied');
        var orig = self.textContent;
        self.textContent = 'Copied!';
        setTimeout(function () {
          self.classList.remove('copied');
          self.textContent = orig;
        }, 2000);
      }).catch(function () {
        // Fallback for older browsers
        var textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        self.classList.add('copied');
        var orig = self.textContent;
        self.textContent = 'Copied!';
        setTimeout(function () {
          self.classList.remove('copied');
          self.textContent = orig;
        }, 2000);
      });
    });
  });

  // --- Smooth Scroll for Nav Links ---
  document.querySelectorAll('.sg-nav__link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = this.getAttribute('href');
      if (href && href.startsWith('#')) {
        e.preventDefault();
        var target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Close mobile menu
          var navLinks = document.getElementById('nav-links');
          if (navLinks) navLinks.classList.remove('active');
        }
      }
    });
  });

  // --- Mobile Hamburger Menu ---
  var hamburger = document.getElementById('hamburger-btn');
  var navLinks = document.getElementById('nav-links');

  if (hamburger && navLinks) {
    hamburger.addEventListener('click', function () {
      navLinks.classList.toggle('active');
    });
  }

  // --- Nav Background on Scroll ---
  var nav = document.querySelector('.sg-nav');
  if (nav) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        nav.style.borderBottomColor = 'var(--sg-border)';
      } else {
        nav.style.borderBottomColor = 'transparent';
      }
    }, { passive: true });
  }

})();

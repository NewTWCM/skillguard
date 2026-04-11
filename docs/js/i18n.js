/* ==========================================================================
   SkillGuard — i18n.js
   EN/ZH language toggle. Content sourced from README.md and README_zh.md.
   ========================================================================== */

(function () {
  'use strict';

  var translations = {
    en: {
      // Nav
      'nav.defense': 'Defense',
      'nav.threats': 'Threats',
      'nav.install': 'Install',
      'nav.research': 'Research',
      'nav.support': 'Support',
      'nav.theme': 'Theme',

      // Theme panel
      'theme.title': 'Select Theme',

      // Hero
      'hero.title1': 'Three-Layer Runtime Defense',
      'hero.title2': 'for AI Agent Plugins',
      'hero.subtitle': 'Protect your Claude Code, Cursor, and MCP environments from malicious third-party skills with cryptographic runtime validation.',
      'hero.cta1': 'Get Started',
      'hero.cta2': 'View on GitHub',

      // Defense
      'defense.label': 'Architecture',
      'defense.title': 'Multi-Link Defense Architecture',
      'defense.desc': 'Three deterministic layers form a zero-trust runtime environment that no malicious plugin can bypass.',
      'defense.l3.title': 'Environment & Integrity',
      'defense.l3.desc': 'PATH sanitization, absolute path locking for security tools, and multi-link SHA256 cryptographic sealing to prevent tampering.',
      'defense.l2.title': 'Advanced Behavioral Scan',
      'defense.l2.desc': 'Multi-vector engine detecting time-bombs, environment hijacking (PYTHONPATH, LD_PRELOAD), and out-of-band variable injection.',
      'defense.l1.title': 'Honeypot Decoys',
      'defense.l1.desc': 'Immutable sentinel files deployed at known malware write targets. Any modification triggers an immediate alert.',
      'defense.footer': 'Zero-Trust Runtime \u2014 cryptographic, not semantic.',

      // Threats
      'threats.label': 'Threat Intelligence',
      'threats.title': 'Why SkillGuard?',
      'threats.desc': 'Real-world incidents that drove our three-layer defense design.',
      'threats.case1.title': 'The gstack Telemetry Backdoor',
      'threats.case1.body': 'In early 2026, a popular Claude Code skill named gstack was found silently exfiltrating user insights and business data. SkillGuard detected this bypass using Layer 1 (Honeypot) and Layer 2 (Behavioral Scan).',
      'threats.case2.title': 'Tool & Environment Hijacking',
      'threats.case2.body': 'Advanced attackers attempt to override system binaries like shasum or grep. SkillGuard v2.3 uses Absolute Path Locking and $PATH sanity checks to ensure security tools remain untampered.',

      // Install
      'install.label': 'Quick Start',
      'install.title': 'Get Protected in 3 Steps',
      'install.s1.title': 'Install & Seal',
      'install.s1.desc': 'Deploy honeypots and compute the Layer 3 checksum to prevent tampering.',
      'install.s2.title': 'Full Security Scan',
      'install.s2.desc': 'Run on any plugin or skill directory before use.',
      'install.s3.title': 'Routine Check',
      'install.s3.desc': 'Check honeypot integrity and self-integrity regularly.',

      // Research
      'research.label': 'Publication',
      'research.title': 'Research & Citation',
      'research.abstract.title': 'Abstract',
      'research.abstract.body': 'The rapid evolution of LLM-based agentic ecosystems has introduced a critical attack surface: third-party plugins that execute with elevated privileges. We present SkillGuard, a lightweight, three-layer runtime defense system. Our evaluation demonstrates high detection rates with minimal performance overhead (<1s).',

      // Support
      'support.label': 'Open Source',
      'support.title': 'Support This Research',
      'support.desc': 'If SkillGuard has helped secure your AI environment, consider supporting further development.',
      'support.gh.desc': 'The recommended way to support ongoing security research and development.',
      'support.gh.btn': 'Sponsor on GitHub',
      'support.bmc.desc': 'A quick way to show appreciation for the project.',
      'support.bmc.btn': 'Buy a Coffee',

      // Footer
      'footer.built': 'Built with purpose.'
    },

    zh: {
      // Nav
      'nav.defense': '\u9632\u79a6',
      'nav.threats': '\u5a01\u8105',
      'nav.install': '\u5b89\u88dd',
      'nav.research': '\u7814\u7a76',
      'nav.support': '\u8d0a\u52a9',
      'nav.theme': '\u4e3b\u984c',

      // Theme panel
      'theme.title': '\u9078\u64c7\u4e3b\u984c',

      // Hero
      'hero.title1': '\u4e09\u5c64\u57f7\u884c\u671f\u9632\u79a6\u5354\u8b70',
      'hero.title2': 'AI \u4ee3\u7406\u7a0b\u5f0f\u63d2\u4ef6\u5b89\u5168',
      'hero.subtitle': '\u4fdd\u8b77\u60a8\u7684 Claude Code\u3001Cursor \u548c MCP \u74b0\u5883\uff0c\u4ee5\u5bc6\u78bc\u5b78\u57f7\u884c\u671f\u9a57\u8b49\u62b5\u79a6\u60e1\u610f\u7b2c\u4e09\u65b9\u63d2\u4ef6\u3002',
      'hero.cta1': '\u958b\u59cb\u4f7f\u7528',
      'hero.cta2': '\u5728 GitHub \u67e5\u770b',

      // Defense
      'defense.label': '\u67b6\u69cb',
      'defense.title': '\u591a\u93c8\u9023\u52d5\u9632\u79a6\u67b6\u69cb',
      'defense.desc': '\u4e09\u5c64\u78ba\u5b9a\u6027\u9632\u79a6\u5c64\u69cb\u6210\u96f6\u4fe1\u4efb\u57f7\u884c\u74b0\u5883\uff0c\u4efb\u4f55\u60e1\u610f\u63d2\u4ef6\u7686\u7121\u6cd5\u7e5e\u904e\u3002',
      'defense.l3.title': '\u74b0\u5883\u8207\u5b8c\u6574\u6027\u6821\u9a57',
      'defense.l3.desc': '\u8def\u5f91\u6de8\u5316\u3001\u5b89\u5168\u5de5\u5177\u7d55\u5c0d\u8def\u5f91\u9396\u5b9a\uff0c\u4ee5\u53ca\u591a\u93c8 SHA256 \u5bc6\u78bc\u5b78\u5c01\u88dd\u4ee5\u9632\u6b62\u7be1\u6539\u3002',
      'defense.l2.title': '\u9032\u968e\u884c\u70ba\u5411\u91cf\u6383\u63cf',
      'defense.l2.desc': '\u591a\u5411\u91cf\u5f15\u64ce\u5075\u6e2c\u5b9a\u6642\u70b8\u5f48\u3001\u74b0\u5883\u52ab\u6301\uff08PYTHONPATH\u3001LD_PRELOAD\uff09\u53ca\u5e36\u5916\u8b8a\u6578\u6ce8\u5165\u3002',
      'defense.l1.title': '\u8a98\u990c\u5f0f\u871c\u7f50\u76e3\u6e2c',
      'defense.l1.desc': '\u5728\u5df2\u77e5\u60e1\u610f\u8edf\u9ad4\u5beb\u5165\u76ee\u6a19\u90e8\u7f72\u4e0d\u53ef\u8b8a\u54e8\u5175\u6a94\u3002\u4efb\u4f55\u4fee\u6539\u7686\u89f8\u767c\u5373\u6642\u8b66\u5831\u3002',
      'defense.footer': '\u96f6\u4fe1\u4efb\u57f7\u884c\u74b0\u5883 \u2014 \u5bc6\u78bc\u5b78\u7d1a\uff0c\u975e\u8a9e\u7fa9\u5c64\u3002',

      // Threats
      'threats.label': '\u5a01\u8105\u60c5\u5831',
      'threats.title': '\u70ba\u4ec0\u9ebc\u9700\u8981 SkillGuard\uff1f',
      'threats.desc': '\u63a8\u52d5\u6211\u5011\u4e09\u5c64\u9632\u79a6\u8a2d\u8a08\u7684\u771f\u5be6\u4e8b\u4ef6\u3002',
      'threats.case1.title': 'gstack \u9059\u6e2c\u80cc\u9580\u4e8b\u4ef6',
      'threats.case1.body': '2026 \u5e74\u521d\uff0c\u4e00\u500b\u71b1\u9580\u7684 Claude Code \u63d2\u4ef6 gstack \u88ab\u767c\u73fe\u6b63\u79d8\u5bc6\u7aca\u53d6\u4f7f\u7528\u8005\u7684\u5546\u696d\u6a5f\u5bc6\u8207\u6578\u64da\u3002SkillGuard \u900f\u904e\u7b2c 1 \u5c64\uff08\u871c\u7f50\uff09\u8207\u7b2c 2 \u5c64\uff08\u884c\u70ba\u6383\u63cf\uff09\u5373\u6642\u5075\u6e2c\u4e26\u4e2d\u65b7\u3002',
      'threats.case2.title': '\u5de5\u5177\u8207\u74b0\u5883\u52ab\u6301',
      'threats.case2.body': '\u9ad8\u7d1a\u99ed\u5ba2\u5617\u8a66\u6389\u5305\u7cfb\u7d71\u7684 shasum \u6216 grep \u6307\u4ee4\u3002SkillGuard v2.3 \u900f\u904e\u7d55\u5c0d\u8def\u5f91\u9396\u5b9a\u8207 $PATH \u6aa2\u67e5\u78ba\u4fdd\u5b89\u5168\u5de5\u5177\u672a\u88ab\u7be1\u6539\u3002',

      // Install
      'install.label': '\u5feb\u901f\u958b\u59cb',
      'install.title': '\u4e09\u6b65\u9a5f\u5373\u53ef\u9632\u8b77',
      'install.s1.title': '\u5b89\u88dd\u8207\u5c01\u88dd',
      'install.s1.desc': '\u90e8\u7f72\u871c\u7f50\u4e26\u5c0d\u8173\u672c\u9032\u884c SHA256 \u7c3d\u7f72\uff0c\u9632\u6b62\u88ab\u53cd\u5411\u52ab\u6301\u3002',
      'install.s2.title': '\u9032\u968e\u5b89\u5168\u6383\u63cf',
      'install.s2.desc': '\u5728\u4f7f\u7528\u4efb\u4f55\u65b0\u63d2\u4ef6\u524d\uff0c\u57f7\u884c\u6df1\u5ea6\u591a\u5411\u91cf\u6383\u63cf\u3002',
      'install.s3.title': '\u5b9a\u671f\u5b8c\u6574\u6027\u6aa2\u67e5',
      'install.s3.desc': '\u6aa2\u67e5\u74b0\u5883\u8b8a\u6578\u3001\u871c\u7f50\u6a94\u6848\u8207\u8173\u672c Hash \u662f\u5426\u5b8c\u597d\u3002',

      // Research
      'research.label': '\u5b78\u8853\u8207\u7814\u7a76',
      'research.title': '\u7814\u7a76\u8207\u5f15\u7528',
      'research.abstract.title': '\u6458\u8981',
      'research.abstract.body': 'LLM \u57fa\u790e\u7684\u4ee3\u7406\u751f\u614b\u7cfb\u7d71\u5feb\u901f\u6f14\u5316\uff0c\u5e36\u4f86\u4e86\u65b0\u7684\u95dc\u9375\u653b\u64ca\u9762\uff1a\u4ee5\u9ad8\u6b0a\u9650\u57f7\u884c\u7684\u7b2c\u4e09\u65b9\u63d2\u4ef6\u3002\u6211\u5011\u63d0\u51fa SkillGuard\uff0c\u4e00\u5957\u8f15\u91cf\u7d1a\u4e09\u5c64\u57f7\u884c\u671f\u9632\u79a6\u7cfb\u7d71\u3002\u8a55\u4f30\u8b49\u5be6\u5176\u5177\u6709\u9ad8\u5075\u6e2c\u7387\u4e14\u6548\u80fd\u958b\u92b7\u6975\u4f4e\uff08<1s\uff09\u3002',

      // Support
      'support.label': '\u958b\u6e90\u5c08\u6848',
      'support.title': '\u652f\u6301\u672c\u7814\u7a76',
      'support.desc': '\u5982\u679c SkillGuard \u5e6b\u52a9\u60a8\u63d0\u5347\u4e86 AI \u74b0\u5883\u7684\u5b89\u5168\u6027\uff0c\u6b61\u8fce\u8003\u616e\u652f\u6301\u6301\u7e8c\u7814\u767c\u3002',
      'support.gh.desc': '\u63a8\u85a6\u7684\u652f\u6301\u65b9\u5f0f\uff0c\u6301\u7e8c\u652f\u6301\u5b89\u5168\u7814\u7a76\u8207\u958b\u767c\u3002',
      'support.gh.btn': '\u5728 GitHub \u8d0a\u52a9',
      'support.bmc.desc': '\u5feb\u901f\u8868\u9054\u5c0d\u5c08\u6848\u7684\u652f\u6301\u3002',
      'support.bmc.btn': '\u8d0a\u52a9\u4e00\u676f\u5496\u5561',

      // Footer
      'footer.built': '\u7528\u5fc3\u6253\u9020\u3002'
    }
  };

  var langBtn = document.getElementById('lang-toggle-btn');
  var langLabel = document.getElementById('lang-label');

  function setLang(lang) {
    var strings = translations[lang];
    if (!strings) return;

    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (strings[key] !== undefined) {
        el.textContent = strings[key];
      }
    });

    document.documentElement.lang = lang;
    localStorage.setItem('sg-lang', lang);
    if (langLabel) langLabel.textContent = lang.toUpperCase();
  }

  if (langBtn) {
    langBtn.addEventListener('click', function () {
      var current = localStorage.getItem('sg-lang') || 'en';
      setLang(current === 'en' ? 'zh' : 'en');
    });
  }

  // Apply saved language
  var savedLang = localStorage.getItem('sg-lang') || 'en';
  if (savedLang !== 'en') {
    setLang(savedLang);
  }

})();

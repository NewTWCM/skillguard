# SkillGuard Design Prompt Templates

Pre-written prompts for AI assistants. Copy a prompt and paste it to generate or modify designs.

---

## Quick Reference: Theme Codenames

| Code | Name | Aesthetic | Palette |
|------|------|-----------|---------|
| `kaze` | KAZE (風) | Pink-blue aurora glass, neon glow edges | `#ffa8f7` → `#097dff` |
| `kagami` | KAGAMI (鏡) | Chrome metallic, liquid mirror | Silver → Violet |
| `kurage` | KURAGE (海月) | Bioluminescent deep ocean, organic pulse | `#00ffc8` + `#8b5cf6` |
| `myaku` | MYAKU (脈) | Golden neural veins, organic data-flow | Gold `#c9a84c` |
| `sumi` | SUMI (墨) | High-contrast minimal, ink-wash monochrome | Black/White + red `#d4002a` |

---

## Prompt 1: Apply a Theme

```
Apply the [CODENAME] theme to the SkillGuard website.
Set data-theme="[CODENAME]" on the <html> element and load css/themes/[CODENAME].css.
```

## Prompt 2: Switch to Dark/Light Mode

```
Switch the SkillGuard website to [dark/light] mode.
Set data-mode="[dark/light]" on the <html> element.
```

## Prompt 3: Create a New Theme

```
Create a new SkillGuard theme CSS file. Follow the pattern in css/themes/kaze.css.

Requirements:
- Override ALL --sg-* custom properties from base.css
- Define both dark mode (html[data-theme="NEWNAME"]) and light mode (html[data-theme="NEWNAME"][data-mode="light"]) variants
- Include theme-specific styles for: .sg-nav, .sg-glass-card, .sg-glass-card--glow::before, .sg-hero::before, .sg-terminal, .sg-theme-switcher, ::selection, ::-webkit-scrollbar-thumb

Theme aesthetic: [DESCRIBE YOUR DESIRED LOOK]
Primary accent: [COLOR]
Secondary accent: [COLOR]
Dark background: [COLOR]
Light background: [COLOR]

Save as docs/css/themes/[NEWNAME].css
```

## Prompt 4: Modify Hero Background Animation

```
Modify the hero background animation for the [CODENAME] theme in docs/js/animations.js.

The animation is in the init[Codename]() function. It uses a canvas element for procedural backgrounds.

Change the animation to: [DESCRIBE DESIRED EFFECT]
Keep it performance-friendly: cap at 30fps, respect prefers-reduced-motion.
```

## Prompt 5: Add a New Section

```
Add a new section to SkillGuard's docs/index.html.
Place it between the [SECTION_A] and [SECTION_B] sections.

Use these component classes:
- .sg-section for the outer container
- .sg-section--alt for alternate background
- .sg-section__header, .sg-section__label, .sg-section__title for headings
- .sg-glass-card for content cards
- .sg-terminal for code blocks
- .sg-animate-on-scroll for entrance animations

Add data-i18n attributes and corresponding translations in docs/js/i18n.js.

Section content: [DESCRIBE CONTENT]
```

## Prompt 6: Modify Glass Card Style

```
Modify the glass card component (.sg-glass-card) in docs/css/components.css.

Current style uses:
- backdrop-filter: blur(var(--sg-glass-blur))
- border: 1px solid var(--sg-glass-border)
- border-radius: var(--sg-radius-lg)

Change to: [DESCRIBE DESIRED CARD STYLE]
Ensure it works with all 5 themes by using --sg-* CSS custom properties.
```

## Prompt 7: Add Language Support

```
Add [LANGUAGE] support to SkillGuard's i18n system in docs/js/i18n.js.

The translation system uses a 'translations' object with language keys (currently 'en' and 'zh').
Each key maps to an object of data-i18n keys and their translated strings.

Add a new '[LANG_CODE]' key with all translations from the 'en' object translated to [LANGUAGE].
Update the lang toggle button to cycle through: EN → ZH → [LANG_CODE].
```

---

## CSS Quick Reference

### Glass Card
```css
background: rgba(255, 255, 255, 0.06);
backdrop-filter: blur(16px);
border: 1px solid rgba(255, 255, 255, 0.12);
border-radius: 16px;
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
```

### Gradient Glow Border
```css
@property --sg-angle {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: false;
}
.element::before {
  background: linear-gradient(var(--sg-angle), #ffa8f7, #097dff) border-box;
  animation: sg-rotate-gradient 8s linear infinite;
}
```

### Neon Glow
```css
box-shadow:
  0 0 5px rgba(255, 168, 247, 0.4),
  0 0 20px rgba(255, 168, 247, 0.2),
  0 0 60px rgba(9, 125, 255, 0.1);
```

### Aurora Background
```css
background:
  radial-gradient(at 20% 20%, rgba(255, 168, 247, 0.25), transparent 60%),
  radial-gradient(at 80% 80%, rgba(9, 125, 255, 0.20), transparent 60%);
```

### Dark/Light Mode Tokens
```css
html[data-theme="name"][data-mode="dark"] {
  --sg-bg-primary: #0a0a1a;
  --sg-text-primary: #f0f0f5;
}
html[data-theme="name"][data-mode="light"] {
  --sg-bg-primary: #f8f6ff;
  --sg-text-primary: #1a1a2e;
}
```

### Responsive Grid
```css
display: grid;
grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
gap: 1.5rem;
```

---

## File Map

| File | Purpose |
|------|---------|
| `docs/css/base.css` | Design tokens, reset, typography, grid, utilities |
| `docs/css/components.css` | Glass cards, terminal, buttons, nav, hero, layers |
| `docs/css/animations.css` | All @keyframes definitions |
| `docs/css/themes/*.css` | Theme-specific token overrides |
| `docs/js/main.js` | Theme/mode switching, scroll observer, clipboard |
| `docs/js/animations.js` | Canvas hero background animations |
| `docs/js/i18n.js` | EN/ZH translation system |
| `docs/index.html` | Single-page HTML structure |

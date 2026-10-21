/**
 * MSK-Therapy-OS Client-Side i18n Engine
 * High-performance, zero-dependency localization engine supporting
 * English (en), Simplified Chinese (zh), and Vietnamese (vi).
 */
(function() {
  'use strict';

  const SUPPORTED_LANGS = ['en', 'zh', 'vi'];
  const STORAGE_KEY = 'msk_app_language';
  let currentLang = localStorage.getItem(STORAGE_KEY) || 'en';
  if (!SUPPORTED_LANGS.includes(currentLang)) currentLang = 'en';

  const dictionaries = {
    en: null,
    zh: null,
    vi: null
  };

  let terminologyRegistry = null;

  async function loadDictionaries() {
    try {
      const [resEn, resZh, resVi, resTerm] = await Promise.all([
        fetch('/i18n/en.json'),
        fetch('/i18n/zh.json'),
        fetch('/i18n/vi.json'),
        fetch('/api/terminology').catch(() => null)
      ]);

      dictionaries.en = await resEn.json();
      dictionaries.zh = await resZh.json();
      dictionaries.vi = await resVi.json();

      if (resTerm && resTerm.ok) {
        terminologyRegistry = await resTerm.json();
      }
    } catch (err) {
      console.warn('[i18n] Failed to load one or more dictionaries, using fallback:', err);
    }
  }

  function getNestedValue(obj, keyPath) {
    if (!obj) return null;
    const parts = keyPath.split('.');
    let curr = obj;
    for (const part of parts) {
      if (curr && typeof curr === 'object' && part in curr) {
        curr = curr[part];
      } else {
        return null;
      }
    }
    return curr;
  }

  function t(key, fallback = '') {
    if (!key) return fallback;

    // 1. Try current language dictionary
    let val = getNestedValue(dictionaries[currentLang], key);
    if (val !== null && val !== undefined) return val;

    // 2. Fallback to English dictionary
    if (currentLang !== 'en') {
      val = getNestedValue(dictionaries.en, key);
      if (val !== null && val !== undefined) return val;
    }

    return fallback || key;
  }

  function applyTranslations() {
    document.documentElement.lang = currentLang === 'zh' ? 'zh-Hans' : currentLang;

    // Update active class on language switcher buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
      const l = btn.getAttribute('data-lang');
      if (l === currentLang) {
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');
      } else {
        btn.classList.remove('active');
        btn.setAttribute('aria-pressed', 'false');
      }
    });

    // Translate all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const translation = t(key);
      if (translation) {
        // If element contains icons or child tags, replace only text or full HTML if intentional
        if (el.children.length === 0 || el.getAttribute('data-i18n-html') === 'true') {
          el.innerHTML = translation;
        } else {
          // Replace only text content without destroying child icons
          const icon = el.querySelector('i, svg, span.icon');
          if (icon) {
            el.innerHTML = '';
            el.appendChild(icon);
            el.appendChild(document.createTextNode(' ' + translation));
          } else {
            el.textContent = translation;
          }
        }
      }
    });

    // Translate title tooltips
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const translation = t(key);
      if (translation) el.setAttribute('title', translation);
    });

    // Translate input placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const translation = t(key);
      if (translation) el.setAttribute('placeholder', translation);
    });
  }

  function syncToAtlas(lang) {
    const iframe = document.getElementById('atlasFrame');
    if (iframe && iframe.contentWindow) {
      iframe.contentWindow.postMessage({ type: 'MSK_SET_LANGUAGE', lang }, '*');
    }
  }

  function setLanguage(lang, syncIframe = true) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    currentLang = lang;
    localStorage.setItem(STORAGE_KEY, lang);
    applyTranslations();

    if (syncIframe) {
      syncToAtlas(lang);
    }

    // Dispatch global event for application components to re-render dynamic content
    window.dispatchEvent(new CustomEvent('msk:lang-changed', {
      detail: { lang, t, terminology: terminologyRegistry }
    }));
  }

  // Listen for language messages from embedded Atlas iframe
  window.addEventListener('message', (ev) => {
    if (ev.data && ev.data.type === 'ATLAS_SET_LANGUAGE') {
      if (ev.data.lang && ev.data.lang !== currentLang) {
        setLanguage(ev.data.lang, false);
      }
    }
  });

  async function init() {
    await loadDictionaries();
    applyTranslations();
    window.dispatchEvent(new CustomEvent('msk:lang-changed', {
      detail: { lang: currentLang, t, terminology: terminologyRegistry }
    }));
    // Sync initial language to iframe when iframe finishes loading
    const iframe = document.getElementById('atlasFrame');
    if (iframe) {
      iframe.addEventListener('load', () => {
        syncToAtlas(currentLang);
      });
    }
  }

  // Export to global window object
  window.__msk_i18n = {
    SUPPORTED_LANGS,
    getLang: () => currentLang,
    setLanguage,
    t,
    applyTranslations,
    getTerminology: () => terminologyRegistry,
    init
  };

  // Auto-initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

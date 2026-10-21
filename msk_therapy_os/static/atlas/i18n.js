/**
 * Open Anatomy Atlas i18n Engine
 * Synchronizes with MSK-Therapy-OS Host application via postMessage.
 * Supports EN / 中文（简体） / Tiếng Việt.
 */
(function() {
  'use strict';

  const SUPPORTED_LANGS = ['en', 'zh', 'vi'];
  const STORAGE_KEY = 'msk_atlas_language';

  // Read URL query param ?lang= or localStorage or default to 'en'
  const urlParams = new URLSearchParams(window.location.search);
  let currentLang = urlParams.get('lang') || localStorage.getItem(STORAGE_KEY) || 'en';
  if (!SUPPORTED_LANGS.includes(currentLang)) currentLang = 'en';

  const dictionaries = {
    en: null,
    zh: null,
    vi: null
  };

  async function loadDictionaries() {
    try {
      const [resEn, resZh, resVi] = await Promise.all([
        fetch('i18n/en.json'),
        fetch('i18n/zh.json'),
        fetch('i18n/vi.json')
      ]);
      dictionaries.en = await resEn.json();
      dictionaries.zh = await resZh.json();
      dictionaries.vi = await resVi.json();
    } catch (err) {
      console.warn('[Atlas i18n] Failed to load dictionaries:', err);
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

    let val = getNestedValue(dictionaries[currentLang], key);
    if (val !== null && val !== undefined) return val;

    if (currentLang !== 'en') {
      val = getNestedValue(dictionaries.en, key);
      if (val !== null && val !== undefined) return val;
    }

    return fallback || key;
  }

  function applyTranslations() {
    document.documentElement.lang = currentLang === 'zh' ? 'zh-Hans' : currentLang;

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const translation = t(key);
      if (translation) {
        if (el.children.length === 0 || el.getAttribute('data-i18n-html') === 'true') {
          el.innerHTML = translation;
        } else {
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

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const translation = t(key);
      if (translation) el.setAttribute('title', translation);
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const translation = t(key);
      if (translation) el.setAttribute('placeholder', translation);
    });
  }

  function setLanguage(lang, notifyParent = true) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    currentLang = lang;
    localStorage.setItem(STORAGE_KEY, lang);
    applyTranslations();

    if (notifyParent && window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'ATLAS_SET_LANGUAGE', lang }, '*');
    }

    window.dispatchEvent(new CustomEvent('atlas:lang-changed', {
      detail: { lang, t }
    }));
  }

  // Listen for language change message from host app
  window.addEventListener('message', (ev) => {
    if (ev.data && ev.data.type === 'MSK_SET_LANGUAGE') {
      if (ev.data.lang && ev.data.lang !== currentLang) {
        setLanguage(ev.data.lang, false);
      }
    }
  });

  async function init() {
    await loadDictionaries();
    applyTranslations();
  }

  window.__atlas_i18n = {
    SUPPORTED_LANGS,
    getLang: () => currentLang,
    setLanguage,
    t,
    applyTranslations,
    init
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

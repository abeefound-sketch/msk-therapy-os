# MSK-Therapy-OS Multilingual Internationalization (i18n) Architecture

**Document Version:** 1.0.0  
**Effective Date:** 2026-10-21  
**Target Repository:** `msk-therapy-os`  
**Target Branch:** `feature/multilingual-i18n`  
**Classification:** Software Architecture & Systems Engineering Specification

---

## 1. Architectural Overview & Design Constraints

MSK-Therapy-OS requires seamless, client-side multilingual localization across three linguistic domains:
1. **English (`en`)**: International Clinical & Rehabilitation Medicine.
2. **Simplified Chinese (`zh`)**: Traditional Chinese Medicine (TCM) & Classical Acupuncture.
3. **Vietnamese (`vi`)**: Vietnamese Traditional Medicine (Đông Y / Y học Cổ truyền) & Ministry of Health Anatomical Designations.

### Architectural Constraints
- **Zero Heavy External Dependencies**: No heavyweight bloat or runtime bundles. Zero overhead, deterministic pure JavaScript localization engines.
- **No Page Reloads**: Instant UI updates via DOM mutation events and reactive attributes.
- **Cross-Frame Synchronization**: Strict isolation maintained between the host rehabilitation shell and the embedded Open Anatomy Atlas iframe, coordinated via deterministic `postMessage` protocol.
- **Clinical Data Integrity**: Absolute immutability of underlying clinical databases (SQLite, FHIR JSON-LD, patient case UUIDs). Localization operates exclusively as an interpretive projection layer.
- **Offline Reliability**: Dictionaries and terminology registry are served locally without reliance on external CDN networks.

---

## 2. Component Topology & Data Flow

```mermaid
flowchart TD
    User([User / Clinician]) -->|Clicks Language Switcher| Switcher[Language Switcher UI\nEN | 中文 | Tiếng Việt]
    
    subgraph Host Application Shell
        Switcher -->|setLanguage| HostEngine[Host i18n Engine\nmsk_therapy_os/static/i18n.js]
        HostEngine -->|Persists| LocalStorage[(localStorage\n'msk_app_language')]
        HostEngine -->|Loads| DictionariesHost[Local JSON Dictionaries\n/static/i18n/{en,zh,vi}.json]
        HostEngine -->|Fetches| TermRegistryAPI[/api/terminology\nMedicalTerminologyRegistry]
        HostEngine -->|DOM Walk| DOMNodes[DOM Nodes with\ndata-i18n, data-i18n-title, data-i18n-placeholder]
        HostEngine -->|Dispatches Event| CustomEvent[Event: 'msk:lang-changed']
        CustomEvent -->|Dynamic Renderers| SOAPCards[SOAP Records, Anatomical Structure Cards,\nAcupoint Detail Cards]
    end

    subgraph Iframe Boundary Cross-Talk
        HostEngine -->|postMessage: MSK_SET_LANGUAGE| AtlasIframe[Open Anatomy Atlas Iframe\n#atlasFrame]
        AtlasIframe -->|postMessage: ATLAS_LANGUAGE_READY| HostEngine
    end

    subgraph Atlas Viewer Engine
        AtlasIframe --> AtlasEngine[Atlas i18n Engine\nstatic/atlas/i18n.js]
        AtlasEngine --> DictionariesAtlas[Atlas JSON Dictionaries\nstatic/atlas/i18n/{en,zh,vi}.json]
        AtlasEngine --> DynamicAtlas[Atlas 3D Canvas, Layer Sidebar,\nAcupoint 3D Pins & Tooltips]
    end
```

---

## 3. Host Localization Engine (`i18n.js`)

The host localization engine [`msk_therapy_os/static/i18n.js`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/i18n.js) provides a reactive singleton `window.I18n`:

### Core Capabilities
1. **Language Detection & Persistence**:
   - Checks `localStorage.getItem('msk_app_language')`.
   - Falls back to browser navigator language (`navigator.language`).
   - Defaults to `'en'`.
2. **Translation Lookup (`t(key, fallback)`)**:
   - Dot-notated key traversal (e.g. `t('modes.surface')`).
   - Deterministic fallback chain: `activeLang` -> `'en'` -> `raw key`.
3. **Reactive DOM Translation (`applyTranslations()`)**:
   - Queries `[data-i18n]`: updates `textContent` or `innerHTML`.
   - Queries `[data-i18n-title]`: updates HTML `title` tooltip.
   - Queries `[data-i18n-placeholder]`: updates form input placeholder.
4. **Dynamic Medical Terminology Resolution (`resolveLocalizedStructureName(name)`)**:
   - Matches English or anatomical identifiers (e.g. `Cervical Vertebrae (C1-C7)`) against the loaded `MedicalTerminologyRegistry`.
   - Dynamically renders `Đốt sống cổ (C1-C7)` in Vietnamese or `颈椎骨 (C1-C7)` in Chinese.
5. **Cross-Frame Synchronization**:
   - Dispatches `postMessage({ action: 'MSK_SET_LANGUAGE', lang: '...' }, '*')` to `#atlasFrame`.
   - Listens for `ATLAS_READY` and synchronizes language state immediately upon iframe initialization.

---

## 4. Atlas Viewer Localization Engine (`static/atlas/i18n.js`)

The 3D Atlas viewer operates inside an isolated sandbox iframe. Its localization engine [`msk_therapy_os/static/atlas/i18n.js`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/static/atlas/i18n.js) fulfills:

1. **Independent Lifecycle**:
   - Parses `?lang=` parameter from iframe query string or accepts `MSK_SET_LANGUAGE` postMessage.
   - Dispatches `atlas:lang-changed` window event.
2. **3D Acupoint Pin Localization (`static/atlas/meridians.js`)**:
   - When hovering over or inspecting 3D pins on the WebGL canvas, point names dynamically resolve:
     ```javascript
     const lang = (window.AtlasI18n && window.AtlasI18n.getCurrentLanguage()) || 'en';
     if (lang === 'vi' && pt.name_vi) {
         nameDisplay = `${pt.name_vi} (${pt.code}${pt.name_zh ? ' / ' + pt.name_zh : ''})`;
     } else if (lang === 'zh' && pt.name_zh) {
         nameDisplay = `${pt.name_zh} (${pt.code} - ${pt.pinyin || ''})`;
     } else {
         nameDisplay = `${pt.name_en || pt.name} (${pt.code})`;
     }
     ```
3. **Layer Tree & Sidebar Localization**:
   - Tabs (`Layers` -> `解剖图层` / `Lớp Giải Phẫu`), Presets, Search inputs, and Action buttons update synchronously.

---

## 5. Backend Medical Terminology API (`/api/terminology`)

Implemented in [`msk_therapy_os/terminology.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/terminology.py) and registered in [`msk_therapy_os/server.py`](file:///D:/5Projects/msk-therapy-os/msk_therapy_os/server.py#L438-L455):

### API Specification
- **Endpoint**: `GET /api/terminology`
- **Query Parameters**:
  * `category` (optional): Filter by category (`meridians`, `acupoints`, `musculoskeletal`, `regions`, `rom`, `dien_chan`, `thai_sen_sib`, `safety`).
  * `lang` (optional): Format dictionary tailored to target language (`en`, `zh`, `vi`).
- **Response Format**:
  ```json
  {
    "version": "1.0.0",
    "categories": { ... },
    "structures": [
      {
        "id": "FMA:7111",
        "code": "C1-C7",
        "name_en": "Cervical Vertebrae (C1-C7)",
        "name_zh": "颈椎骨 (C1-C7)",
        "name_vi": "Đốt sống cổ (C1-C7)",
        "fma_id": "7111",
        "bodyparts3d_id": "FJ000001",
        "provenance": {
          "standard_body": "FMA / BodyParts3D",
          "review_status": "OFFICIAL_STANDARD"
        }
      }
    ]
  }
  ```

---

## 6. Verification & Automated Quality Assurance

Quality assurance is verified by automated Playwright suite [`prototype/test_multilingual_i18n.py`](file:///D:/5Projects/msk-therapy-os/prototype/test_multilingual_i18n.py):

1. **Instant Switching**: Asserts UI transforms across all 3 locales without HTTP reload.
2. **Persistence**: Asserts `localStorage` retention across subsequent reloads.
3. **Iframe Sync**: Asserts Atlas iframe DOM nodes update immediately upon parent toggle.
4. **Unicode Integrity**: Scans rendered DOM text across all viewports to guarantee absence of Unicode replacement character (`\ufffd`).
5. **Responsive Typography**: Tests `1280px` (desktop), `768px` (tablet), and `375px` (mobile), verifying `scrollWidth === clientWidth` (zero horizontal layout overflows).
6. **Console Audit**: Guarantees zero JavaScript unhandled exceptions or network 4xx/5xx errors during language transitions.

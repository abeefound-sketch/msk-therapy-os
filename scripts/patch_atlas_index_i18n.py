with open('msk_therapy_os/static/atlas/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add script tag for i18n.js
script_tag = '<script src="i18n.js"></script>'
if script_tag not in html:
    html = html.replace('<script src="app.js"></script>', f'{script_tag}\n<script src="app.js"></script>')

# 2. Add data-i18n attributes
replacements = [
    # Search placeholder
    ('id="search" type="search" placeholder="Find a structure (press /)"', 'id="search" type="search" placeholder="Find a structure (press /)" data-i18n-placeholder="search_placeholder"'),
    # Mode tabs
    ('<button id="modeExplore" role="tab" aria-selected="true" class="on">Explore</button>', '<button id="modeExplore" role="tab" aria-selected="true" class="on" data-i18n="modes.explore">Explore</button>'),
    ('<button id="modeQuiz" role="tab" aria-selected="false">Quiz</button>', '<button id="modeQuiz" role="tab" aria-selected="false" data-i18n="modes.quiz">Quiz</button>'),
    # Vis modes
    ('<button data-mode="surface" class="on" title="Surface Meridian Mode: Skin mesh with surface-anchored meridians">🌐 Surface</button>', '<button data-mode="surface" class="on" title="Surface Meridian Mode: Skin mesh with surface-anchored meridians" data-i18n="modes.surface" data-i18n-title="modes.surface_title">🌐 Surface</button>'),
    ('<button data-mode="musculoskeletal" title="Musculoskeletal Anatomy Mode: Deep bones, muscles, joints">🦴 Anatomy</button>', '<button data-mode="musculoskeletal" title="Musculoskeletal Anatomy Mode: Deep bones, muscles, joints" data-i18n="modes.anatomy" data-i18n-title="modes.anatomy_title">🦴 Anatomy</button>'),
    ('<button data-mode="comparative" title="Comparative Research Mode: Synchronized dual split-view">⚖ Compare</button>', '<button data-mode="comparative" title="Comparative Research Mode: Synchronized dual split-view" data-i18n="modes.compare" data-i18n-title="modes.compare_title">⚖ Compare</button>'),
    # Camera views
    ('<button data-view="front" title="Front view (1)">Front</button>', '<button data-view="front" title="Front view (1)" data-i18n="camera.front" data-i18n-title="camera.front_title">Front</button>'),
    ('<button data-view="back" title="Back view (2)">Back</button>', '<button data-view="back" title="Back view (2)" data-i18n="camera.back" data-i18n-title="camera.back_title">Back</button>'),
    ('<button data-view="left" title="Patient\'s left side (3)">Left</button>', '<button data-view="left" title="Patient\'s left side (3)" data-i18n="camera.left" data-i18n-title="camera.left_title">Left</button>'),
    ('<button data-view="right" title="Patient\'s right side (4)">Right</button>', '<button data-view="right" title="Patient\'s right side (4)" data-i18n="camera.right" data-i18n-title="camera.right_title">Right</button>'),
    # Tool buttons
    ('<button id="btnFullBody" class="icon-btn" title="Full body framing (Home)">Full Body</button>', '<button id="btnFullBody" class="icon-btn" title="Full body framing (Home)" data-i18n="camera.full_body" data-i18n-title="camera.full_body_title">Full Body</button>'),
    ('<button id="btnFocusSelected" class="icon-btn" title="Focus on selected structure or acupoint (F)">Focus</button>', '<button id="btnFocusSelected" class="icon-btn" title="Focus on selected structure or acupoint (F)" data-i18n="camera.focus" data-i18n-title="camera.focus_title">Focus</button>'),
    ('<button id="btnReset" class="icon-btn" title="Show everything and reset the view (A)">Reset</button>', '<button id="btnReset" class="icon-btn" title="Show everything and reset the view (A)" data-i18n="camera.reset" data-i18n-title="camera.reset_title">Reset</button>'),
    ('<button id="btnXray" class="icon-btn" aria-pressed="false" title="X-ray: see through everything except the selection (X)">X-ray</button>', '<button id="btnXray" class="icon-btn" aria-pressed="false" title="X-ray: see through everything except the selection (X)" data-i18n="camera.xray" data-i18n-title="camera.xray_title">X-ray</button>'),
    ('<button id="btnShot" class="icon-btn" title="Save a picture of the current view">Save image</button>', '<button id="btnShot" class="icon-btn" title="Save a picture of the current view" data-i18n="camera.shot" data-i18n-title="camera.shot_title">Save image</button>'),
    ('<button id="btnData" class="icon-btn" title="Atlas data">Atlas data</button>', '<button id="btnData" class="icon-btn" title="Atlas data" data-i18n="camera.data" data-i18n-title="camera.data_title">Atlas data</button>'),
    ('<button id="btnAbout" class="icon-btn" title="About this atlas and who made it">About</button>', '<button id="btnAbout" class="icon-btn" title="About this atlas and who made it" data-i18n="camera.about" data-i18n-title="camera.about_title">About</button>'),
    ('<button id="btnHelp" class="icon-btn" title="Keyboard shortcuts (?)" aria-label="Keyboard shortcuts">?</button>', '<button id="btnHelp" class="icon-btn" title="Keyboard shortcuts (?)" aria-label="Keyboard shortcuts" data-i18n="camera.help" data-i18n-title="camera.help_title">?</button>'),
    # Sidebar tabs
    ('<button class="tab on" data-tab="layers" role="tab">Layers</button>', '<button class="tab on" data-tab="layers" role="tab" data-i18n="tabs.layers">Layers</button>'),
    ('<button class="tab" data-tab="tree" role="tab">Structures</button>', '<button class="tab" data-tab="tree" role="tab" data-i18n="tabs.structures">Structures</button>'),
    ('<button class="tab" data-tab="sections" role="tab">Sections</button>', '<button class="tab" data-tab="sections" role="tab" data-i18n="tabs.sections">Sections</button>'),
    ('<button class="tab" data-tab="meridians" role="tab">Meridians</button>', '<button class="tab" data-tab="meridians" role="tab" data-i18n="tabs.meridians">Meridians</button>'),
    # Structure actions
    ('<button id="actFocus" title="Zoom to it (F)">Focus</button>', '<button id="actFocus" title="Zoom to it (F)" data-i18n="actions.focus" data-i18n-title="actions.focus_title">Focus</button>'),
    ('<button id="actIsolate" title="Hide everything else (I)">Isolate</button>', '<button id="actIsolate" title="Hide everything else (I)" data-i18n="actions.isolate" data-i18n-title="actions.isolate_title">Isolate</button>'),
    ('<button id="actHide" title="Hide it (H)">Hide</button>', '<button id="actHide" title="Hide it (H)" data-i18n="actions.hide" data-i18n-title="actions.hide_title">Hide</button>'),
    # Hint
    ('<p class="stage-hint">Drag to rotate, right-drag or shift-drag to pan, scroll to zoom, click to identify, double-click to focus</p>', '<p class="stage-hint" data-i18n="hints.orbit_hint">Drag to rotate, right-drag or shift-drag to pan, scroll to zoom, click to identify, double-click to focus</p>')
]

for old, new in replacements:
    if old in html:
        html = html.replace(old, new)
    else:
        print(f"Warning: pattern not matched: {old[:40]}")

with open('msk_therapy_os/static/atlas/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("atlas/index.html patched with i18n script and attributes successfully.")

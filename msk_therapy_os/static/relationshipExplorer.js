/* M2.9: conservative, read-only educational knowledge explorer.
 * DOM uses textContent throughout; no untrusted knowledge text enters HTML. */
(() => {
  "use strict";
  const query = document.getElementById("exploreQuery");
  const kind = document.getElementById("exploreKind");
  const results = document.getElementById("exploreResults");
  const relations = document.getElementById("exploreRelations");
  if (!query || !kind || !results || !relations) return;

  const text = (tag, value) => { const el = document.createElement(tag); el.textContent = String(value); return el; };
  const clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); };
  async function readJson(path) {
    const response = await fetch(path, {credentials:"same-origin", headers:{Accept:"application/json"}});
    const data = await response.json();
    if (!response.ok) throw Error(data.error || `HTTP ${response.status}`);
    return data;
  }
  async function showRelations(entity) {
    clear(relations);
    relations.appendChild(text("h3", `${entity.name} | ${entity.kind} | ${entity.namespace}`));
    relations.appendChild(text("p", `Status: ${entity.review_status}. ${entity.notes || ""}`));
    if (!entity.atlas_focus_available) {
      relations.appendChild(text("p", "Atlas 3D Focus UNAVAILABLE: verified FMA concept, mesh ID and atlas version are required."));
    }
    const data = await readJson(`/api/explore/relations?entity_id=${encodeURIComponent(entity.entity_id)}`);
    if (!data.relations.length) relations.appendChild(text("p", "No documented relations in this source. This does not establish that no relationship exists."));
    for (const rel of data.relations) {
      const item = document.createElement("div"); item.className = "card";
      item.appendChild(text("strong", `${rel.relation_class}: ${rel.predicate} → ${rel.other_entity?.name || rel.other_entity_id}`));
      item.appendChild(text("p", `${rel.status} | source: ${rel.source_title} | ${rel.assertion_note}`));
      if (rel.relation_class === "traditional_association") item.appendChild(text("small", "Traditional theory, not a physical or causally established anatomical link."));
      relations.appendChild(item);
    }
  }
  async function search() {
    clear(results); clear(relations); results.appendChild(text("p", "Searching reference catalog..."));
    try {
      const params = new URLSearchParams({q:query.value.trim()});
      if (kind.value) params.set("type", kind.value);
      const payload = await readJson(`/api/explore/search?${params}`);
      clear(results);
      if (!payload.results.length) { results.appendChild(text("p", "Not documented in this source.")); return; }
      for (const entity of payload.results) {
        const button = document.createElement("button"); button.type = "button";
        button.className = "btn-secondary";
        button.style.margin = "4px";
        button.textContent = `${entity.name} [${entity.kind} | ${entity.review_status}]`;
        button.addEventListener("click", () => showRelations(entity).catch(err => { clear(relations); relations.appendChild(text("p", err.message)); }));
        results.appendChild(button);
      }
    } catch (err) { clear(results); results.appendChild(text("p", `Search unavailable: ${err.message}`)); }
  }
  document.getElementById("exploreSubmit").addEventListener("click", search);
  query.addEventListener("keydown", ev => {if (ev.key === "Enter") search();});
  search();
})();

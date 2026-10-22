/* M2.10: small, dependency-free, 2D-only point/zone studio. No clinical map claims. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('rsSetSelect')) return;
  const state = {sets:[], selected:null, diagram:null, points:[], finished:false, definitions:[], mode:'point'};
  const E = (tag,textValue) => {const el=document.createElement(tag);el.textContent=String(textValue);return el;};
  const clear = el => el.replaceChildren();
  function status(msg) {$('rsStatus').textContent=msg;}
  async function req(url,body) {
    const options = body===undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};
    const response=await apiFetch(url,options); const payload=await response.json();
    if (!response.ok) throw Error(payload.error || `HTTP ${response.status}`);
    return payload;
  }
  function svgNode(name,attrs) {
    const el=document.createElementNS('http://www.w3.org/2000/svg',name);
    for (const [key,value] of Object.entries(attrs)) el.setAttribute(key,String(value));
    return el;
  }
  function drawGeometry(geometry,draft=false,label='') {
    if (!geometry) return;
    const svg=$('rsOverlay'); const c=geometry.coordinates;
    const attrs={stroke:draft?'#eab308':'#0f766e','stroke-width':3,fill:'none'};
    if (geometry.type==='point') {
      const el=svgNode('circle',{cx:c[0]*400,cy:c[1]*500,r:6,...attrs,fill:draft?'#eab308':'#14b8a6'});
      svg.appendChild(el);
      if (label) {const t=svgNode('text',{x:c[0]*400+9,y:c[1]*500-7,fill:'#0f172a','font-size':12});t.textContent=label;svg.appendChild(t);}
    } else {
      const points=c.map(p=>`${p[0]*400},${p[1]*500}`).join(' ');
      svg.appendChild(svgNode(geometry.type==='polygon'?'polygon':'polyline',{
        points,...attrs,fill:geometry.type==='polygon'?'#14b8a633':'none'}));
    }
  }
  function draftGeometry() {
    const coords=state.points.map(p=>p.slice());
    if (!coords.length) return null;
    return {space:'image_normalized_v1',type:state.mode,coordinates:state.mode==='point'?coords[0]:coords};
  }
  function redraw() {
    const svg=$('rsOverlay');clear(svg);
    for(const def of state.definitions) drawGeometry(def.geometry,false,def.local_code);
    const geometry=draftGeometry();if(geometry) drawGeometry(geometry,true);
    status(state.diagram ? `${state.diagram.view} · ${state.points.length} draft vertices · annotations are illustrative` : 'Select a diagram');
  }
  function resetDraft(){state.points=[];state.finished=false;state.mode=$('rsMode').value;redraw();}
  async function loadSets(preferred) {
    state.sets=await req('/api/research/sets');clear($('rsSetSelect'));
    for(const set of state.sets){const o=E('option',set.title);o.value=set.set_id;$('rsSetSelect').appendChild(o);}
    if (!state.sets.length) {state.selected=null;state.diagram=null;status('No sets available. Local login required to create a private set.');return;}
    $('rsSetSelect').value=preferred || state.sets[0].set_id;await loadSet();
  }
  async function loadSet(){
    state.selected=await req('/api/research/sets/'+encodeURIComponent($('rsSetSelect').value));
    await loadDiagram();
  }
  async function loadDiagram(){
    state.diagram=state.selected.diagrams.find(x=>x.view===$('rsView').value) || state.selected.diagrams[0];
    if(!state.diagram) {status('No diagram on this set');return;}
    if (!/^\/research_demo\/[a-z_]+\.svg$/.test(state.diagram.asset_path)) throw Error('Untrusted asset path');
    $('rsDiagram').src=state.diagram.asset_path;
    state.definitions=await req('/api/research/definitions?diagram_id='+encodeURIComponent(state.diagram.diagram_id));
    clear($('rsDefinitions'));
    const title=E('h4',`${state.definitions.length} definitions on this diagram`);$('rsDefinitions').appendChild(title);
    for(const item of state.definitions) {$('rsDefinitions').appendChild(E('p',`${item.local_code}: ${item.label} [${item.review_state}]`));}
    resetDraft();
  }
  $('rsOverlay').addEventListener('click', ev=>{
    if(!state.diagram || state.finished)return;
    const box=$('rsOverlay').getBoundingClientRect();
    const u=(ev.clientX-box.left)/box.width; const v=(ev.clientY-box.top)/box.height;
    if(u<0||u>1||v<0||v>1)return;
    if (state.mode==='point') {state.points=[[+u.toFixed(5),+v.toFixed(5)]];state.finished=true;}
    else if (state.points.length<100)state.points.push([+u.toFixed(5),+v.toFixed(5)]);
    redraw();
  });
  $('rsZoom').addEventListener('input',()=>{
    const scale=Number($('rsZoom').value)/100;
    $('rsCanvas').style.width=`${400*scale}px`;$('rsCanvas').style.height=`${500*scale}px`;
  });
  $('rsMode').addEventListener('change',resetDraft);
  $('rsClear').addEventListener('click',resetDraft);
  $('rsFinish').addEventListener('click',()=>{state.finished=true;redraw();});
  $('rsSetSelect').addEventListener('change',()=>loadSet().catch(e=>status(e.message)));
  $('rsView').addEventListener('change',()=>loadDiagram().catch(e=>status(e.message)));
  $('rsRefresh').addEventListener('click',()=>loadSets($('rsSetSelect').value).catch(e=>status(e.message)));
  $('rsCreate').addEventListener('click',async()=>{
    try {const response=await req('/api/research/sets',{title:$('rsNewTitle').value,framework:$('rsFramework').value});
      await loadSets(response.set.set_id);status('Private synthetic set created.');}
    catch(error){status(`Cannot create: ${error.message}`);}
  });
  $('rsSaveDefinition').addEventListener('click',async()=>{
    try{const geometry=draftGeometry();if(!geometry)throw Error('Place a marker on the diagram first');
      const c=geometry.type==='point'?1:geometry.coordinates.length;
      if(c<(geometry.type==='polygon'?3:geometry.type==='polyline'?2:1))throw Error('Finish with more vertices');
      await req('/api/research/definitions',{diagram_id:state.diagram.diagram_id,local_code:$('rsCode').value,
        label:$('rsLabel').value,source_note:$('rsSource').value,theory_namespace:'CUSTOM',geometry});
      await loadDiagram();status('Saved as DRAFT definition. No clinical validity implied.');}
    catch(error){status(`Cannot save: ${error.message}`);}
  });
  $('rsSaveObservation').addEventListener('click',async()=>{
    try{const geometry=draftGeometry();if(!geometry)throw Error('Place marker to locate observation');
      const stateValue=$('rsState').value;
      const data={case_id:$('rsCase').value,visit_id:Number($('rsVisit').value),diagram_id:state.diagram.diagram_id,
        geometry,finding_state:stateValue,method:$('rsMethod').value,
        tenderness:stateValue==='not_assessed'||!$('rsTenderness').value?null:Number($('rsTenderness').value)};
      await req('/api/research/observations',data); resetDraft();status('Synthetic finding saved; it does not update a fixed reference point.');}
    catch(error){status(`Cannot record: ${error.message}`);}
  });
  $('rsTimeline').addEventListener('click',async()=>{
    try{const rows=await req('/api/research/timeline?case_id='+encodeURIComponent($('rsCase').value));
      clear($('rsHistory'));$('rsHistory').appendChild(E('h4',`Research timeline (${rows.length})`));
      for(const row of rows)$('rsHistory').appendChild(E('p',`${row.visit_date}: ${row.view} · ${row.finding_state} · tenderness ${row.tenderness ?? 'not recorded'}`));}
    catch(error){status(error.message);}
  });
  loadSets().catch(error=>status(error.message));
})();

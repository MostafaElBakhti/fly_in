const project = window.PROJECT;
const $ = (id) => document.getElementById(id);
const steps = {
  dijkstra: [
    ['Set up the search', 'Resolve start and end; create the forbidden sets. Initialize distances to infinity, previous to None, and priority_score to zero. Set the start distance to zero. Blocked and forbidden nodes are excluded from unvisited.', 'distances[start] = 0\nunvisited = {usable zones}', 'distances[start] = 0'],
    ['Choose current', 'Select the unvisited zone with the smallest distance. Ties prefer a higher priority score, then the alphabetically smaller zone name. Stop if the smallest distance is infinity.', 'key = (distances[zone],\n       -priority_score[zone],\n       zone.name)', 'current = min('],
    ['Visit the zone', 'Remove current from unvisited. If it is the destination, stop the search before inspecting its neighbors.', 'unvisited.remove(current)\nif current == end:\n    break', 'unvisited.remove(current)'],
    ['Inspect neighbors', 'Iterate through current.neighbors. Skip visited neighbors, forbidden connections or nodes, and blocked zones.', 'for neighbor, connection in current.neighbors.items():\n    # skip unavailable neighbors', 'for neighbor, connection'],
    ['Calculate a proposal', 'Entering a restricted zone costs 2; other usable zones cost 1. Entering a priority zone adds one to the current priority score.', 'new_distance = distances[current] + cost\nnew_score = priority_score[current] + bonus', 'cost = 2 if neighbor'],
    ['Update the records', 'Accept a shorter route, or an equally short route with a higher priority score. Store its distance, score, and predecessor. Then continue with the next neighbor and repeat the search.', 'distances[neighbor] = new_distance\npriority_score[neighbor] = new_score\nprevious[neighbor] = current', 'if new_distance <'],
    ['Reconstruct the path', 'If end is unreachable, return None. Otherwise follow previous from end back to start, append each zone, and reverse the list to return the route in travel order.', 'current = end\n# follow previous until None\npath.reverse()\nreturn path', 'path = []'],
  ],
  paths: [
    ['Find the first route', 'Call Dijkstra for the initial route. If no route exists, return an empty list. Otherwise seed paths with first_path and initialize candidates.', 'first_path = self.dijkstra()\npaths = [first_path]\ncandidates = []', 'first_path = self.dijkstra()'],
    ['Choose a branch', 'For each position before the last zone in the most recently accepted route, choose branch_node and copy the prefix into root_path.', 'branch_node = previous_path[i]\nroot_path = previous_path[:i+1]', 'branch_node = previous_path[i]'],
    ['Exclude old choices', 'Forbid prefix nodes before the branch to avoid revisiting them. For every accepted path sharing this prefix, forbid its next connection so Dijkstra must explore another branch.', 'forbidden_nodes = set(root_path[:-1])\nforbidden_connections = set()', 'forbidden_nodes = set(root_path'],
    ['Search the branch', 'Run Dijkstra from branch_node to end with those exclusions. Skip unreachable branches. Join the prefix and branch route without duplicating the branch zone.', 'total_path = root_path[:-1] + branch_path', 'branch_path = self.dijkstra('],
    ['Collect candidates', 'Add total_path only if it is not already in paths or candidates. Candidates remain available across outer iterations. Stop if no candidates remain.', 'if total_path not in paths and total_path not in candidates:\n    candidates.append(total_path)', 'if total_path not in paths'],
    ['Accept the best route', 'Choose the candidate with lowest path_cost, then highest path_priority, then alphabetical route order. Move it from candidates to paths. Repeat until max_paths is reached or no candidate remains.', 'key = (self.path_cost(path),\n       -self.path_priority(path),\n       tuple(zone.name for zone in path))', 'best_path = min('],
  ],
};
let algorithm = 'dijkstra';
let activeStep = 0;
let selectedZone = project.start;
let traceIndex = -1;
let timer = null;
const colors = { normal: '#89aee6', priority: '#80e4bc', restricted: '#e7b877', blocked: '#657080' };
const svgNS = 'http://www.w3.org/2000/svg';
function svgElement(tag, attrs, text) {
  const el = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attrs)) el.setAttribute(key, value);
  if (text !== undefined) el.textContent = text;
  return el;
}
function drawGraph() {
  const xs = project.zones.map(z => z.x), ys = project.zones.map(z => z.y);
  const minX = Math.min(...xs), minY = Math.min(...ys);
  const width = Math.max(...xs) - minX || 1, height = Math.max(...ys) - minY || 1;
  const positions = Object.fromEntries(project.zones.map(z => [z.name, [65 + (z.x-minX)/width*630, 65 + (z.y-minY)/height*205]]));
  for (const c of project.connections) {
    const [x1,y1] = positions[c.a], [x2,y2] = positions[c.b];
    $('graph').append(svgElement('line', {x1,y1,x2,y2,class:'edge','data-a':c.a,'data-b':c.b}));
    const label = svgElement('text', {x:(x1+x2)/2+5,y:(y1+y2)/2-7,class:'edge-label'}, c.capacity);
    label.append(svgElement('title', {}, `${c.a} ↔ ${c.b}: link capacity ${c.capacity}`));
    $('graph').append(label);
  }
  for (const z of project.zones) {
    const [x,y] = positions[z.name];
    const node = svgElement('g', {class:'node', tabindex:0, role:'button', 'aria-label':`Inspect ${z.name}`, 'data-zone':z.name});
    node.append(svgElement('circle', {cx:x,cy:y,r:19,fill:colors[z.type]}), svgElement('text', {x,y:y+37,'text-anchor':'middle'}, z.name));
    const select = () => { selectedZone = z.name; inspectZone(); };
    node.addEventListener('click', select);
    node.addEventListener('keydown', e => { if(e.key === 'Enter' || e.key === ' ') {e.preventDefault();select();} });
    $('graph').append(node);
  }
}
function inspectZone() {
  const z = project.zones.find(z => z.name === selectedZone);
  const neighbors = project.connections.filter(c => c.a === z.name || c.b === z.name).map(c => c.a === z.name ? c.b : c.a);
  $('zone-details').replaceChildren();
  for (const value of [z.name, `type: ${z.type}`, `coordinates: (${z.x}, ${z.y})`, `max_drones: ${z.capacity}`, `color: ${z.color}`, `neighbors: ${neighbors.join(', ')}`]) {
    const el = document.createElement('span'); el.textContent = value; $('zone-details').append(el);
  }
  document.querySelectorAll('[data-zone]').forEach(el => {el.classList.toggle('selected', el.dataset.zone === selectedZone);if(el.classList.contains('node')) el.setAttribute('aria-pressed', el.dataset.zone === selectedZone);});
}
function showSource() {
  const file = $('source-file').value;
  const lines = project.sources[file].split('\n');
  const anchor = steps[algorithm][activeStep][3];
  const match = file === 'map.py' ? (traceIndex >= 0 ? project.traces[algorithm].events[traceIndex].line - 1 : lines.findIndex(line => line.includes(anchor))) : -1;
  $('source').replaceChildren();
  lines.forEach((line, i) => {
    const row = document.createElement('div'); row.className = 'code-line' + (i >= match && i < match + (traceIndex >= 0 ? 1 : 5) && match >= 0 ? ' highlight' : '');
    const number = document.createElement('span'); number.className = 'line-number'; number.textContent = i+1;
    const code = document.createElement('code'); code.textContent = line;
    row.append(number, code); $('source').append(row);
  });
  if(match >= 0) $('source').scrollTop = Math.max(0, match*19.8 - 35);
  else $('source').scrollTop = 0;
}
function showSteps() {
  $('steps').replaceChildren();
  steps[algorithm].forEach((step,i) => {
    const button = document.createElement('button'); button.textContent = `${String(i+1).padStart(2,'0')}  ${step[0]}`;
    button.classList.toggle('active',i === activeStep); button.setAttribute('aria-pressed',i === activeStep);
    button.onclick = () => {pause();activeStep=i; $('source-file').value='map.py'; showSteps();}; $('steps').append(button);
  });
  const [title, description, code] = steps[algorithm][activeStep];
  $('explanation').replaceChildren();
  for(const [tag,text] of [['h3',title],['p',description],['pre',code]]) {const el=document.createElement(tag);el.textContent=text;$('explanation').append(el);}
  showSource();
}
for(const [label,value] of [['Zones',project.zones.length],['Connections',project.connections.length],['Drones',project.nb_drones],['Route',`${project.start} → ${project.end}`]]) {
  const el=document.createElement('div');el.className='stat';const name=document.createElement('span');name.textContent=label;const count=document.createElement('strong');count.textContent=value;el.append(name,count);$('stats').append(el);
}
for(const [key,value] of Object.entries({start:project.start,end:project.end,current:'not selected',neighbor:'not selected',forbidden_nodes:'set()',forbidden_connections:'set()',unvisited:`{${project.zones.filter(z => z.type !== 'blocked').map(z => z.name).join(', ')}}`,max_paths:'5 (find_all_paths default)'})) {
  const el=document.createElement('div');const label=document.createElement('span');label.textContent=key+' = ';const val=document.createElement('b');val.textContent=value;el.append(label,val);$('locals').append(el);
}
for(const z of project.zones) {
  const row=document.createElement('tr');row.dataset.zone=z.name;
  for(const val of [z.name,z.name === project.start ? '0' : '∞','None','0']) {const cell=document.createElement('td');cell.textContent=val;row.append(cell);}
  $('variables').append(row);
}
for(const name of Object.keys(project.sources)) {const option=document.createElement('option');option.value=name;option.textContent=name;$('source-file').append(option);}
$('source-file').value='map.py';$('source-file').onchange=showSource;
document.querySelectorAll('[data-algorithm]').forEach(button => button.onclick = () => {
  resetTrace();
  algorithm=button.dataset.algorithm;activeStep=0;$('source-file').value='map.py';
  document.querySelectorAll('[data-algorithm]').forEach(b => {b.classList.toggle('active',b === button);b.setAttribute('aria-pressed',b === button);});showSteps();prepareTrace();traceIndex=0;renderTrace();
});
function pause() {
  clearInterval(timer);timer=null;$('run').textContent='▶ Run simulation';
}
function formatValue(value) {
  return value === null ? 'None' : typeof value === 'object' ? JSON.stringify(value) : String(value);
}
function prepareTrace() {
  $('timeline').max=project.traces[algorithm].events.length-1;
  $('timeline').value=0;$('back').disabled=true;$('next').disabled=false;
}
function renderTrace() {
  const trace=project.traces[algorithm];
  const event=trace.events[traceIndex];
  const state=event.frames[0].locals;
  $('locals').replaceChildren();
  for(const frame of event.frames) {
    const title=document.createElement('strong');title.textContent=frame.function+'()';title.className='frame-title';$('locals').append(title);
    for(const [key,value] of Object.entries(frame.locals)) {
      if(['distances','previous','priority_score'].includes(key)) continue;
      const el=document.createElement('div');const label=document.createElement('span');label.textContent=key+' = ';const val=document.createElement('b');val.textContent=formatValue(value);el.append(label,val);$('locals').append(el);
    }
  }
  $('variables').replaceChildren();
  for(const z of project.zones) {
    const row=document.createElement('tr');row.dataset.zone=z.name;
    for(const val of [z.name,state.distances?.[z.name] ?? '—',state.previous ? formatValue(state.previous[z.name] ?? null) : '—',state.priority_score?.[z.name] ?? '—']) {
      const cell=document.createElement('td');cell.textContent=val;row.append(cell);
    }
    $('variables').append(row);
  }
  const complete=traceIndex===trace.events.length-1;
  $('trace-caption').textContent=`Step ${traceIndex+1} / ${trace.events.length} · ${event.frames[0].function} · line ${event.line}${event.event==='return' ? ' · return' : ''}`;
  $('variable-caption').textContent=`${event.frames[0].function}() · ${event.event==='return' ? 'returning' : 'before line '+event.line}`;
  $('status').textContent=complete ? '● Pathfinding complete' : '● Exploring the execution trace';
  $('result').textContent=complete ? 'Result: '+formatValue(trace.result) : event.event==='return' ? 'Return: '+formatValue(event.result) : '';
  $('timeline').value=traceIndex;$('back').disabled=traceIndex===0;$('next').disabled=complete;
  document.querySelectorAll('.node').forEach(node => {
    node.classList.toggle('current',node.dataset.zone===state.current);
    node.classList.toggle('neighbor',node.dataset.zone===state.neighbor);
    node.classList.toggle('excluded',(state.forbidden_nodes || []).includes(node.dataset.zone));
  });
  const path=complete ? (algorithm==='dijkstra' ? trace.result : trace.result[0]) : state.path || [];
  document.querySelectorAll('.edge').forEach(edge => {
    const a=edge.dataset.a,b=edge.dataset.b;
    const inPath=Array.isArray(path) && path.some((name,i) => i>0 && ((name===b && path[i-1]===a) || (name===a && path[i-1]===b)));
    edge.classList.toggle('route',Boolean(inPath));
    edge.classList.toggle('forbidden',(state.forbidden_connections || []).some(c => c===`${a}-${b}` || c===`${b}-${a}`));
  });
  $('source-file').value='map.py';showSource();inspectZone();
  if(complete) pause();
}
function resetTrace() {
  pause();traceIndex=-1;$('result').textContent='';$('trace-caption').textContent='Ready to run';$('status').textContent='● Pathfinding ready';
  document.querySelectorAll('.node').forEach(n => n.classList.remove('current','neighbor','excluded'));
  document.querySelectorAll('.edge').forEach(e => e.classList.remove('route','forbidden'));
  prepareTrace();
}
function nextStep() {
  traceIndex=Math.min(traceIndex+1,project.traces[algorithm].events.length-1);renderTrace();
}
$('next').onclick=()=>{pause();nextStep();};
$('back').onclick=()=>{pause();traceIndex=Math.max(0,traceIndex-1);renderTrace();};
$('reset').onclick=()=>{resetTrace();traceIndex=0;renderTrace();};
$('run').onclick=()=>{
  if(timer){pause();return;}
  if(traceIndex===project.traces[algorithm].events.length-1) resetTrace();
  nextStep();
  if(traceIndex<project.traces[algorithm].events.length-1){$('run').textContent='Ⅱ Pause';timer=setInterval(nextStep,Number($('speed').value));}
};
$('speed').onchange=()=>{if(timer){pause();$('run').click();}};
$('timeline').oninput=()=>{pause();traceIndex=Number($('timeline').value);renderTrace();};
drawGraph();inspectZone();showSteps();prepareTrace();

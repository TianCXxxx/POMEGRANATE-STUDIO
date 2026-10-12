/* Temporary one-hop relationship preview; never stored in the graph or exports. */
'use strict';
(()=>{
const canvas=$('canvas');let active=null,interacting=false,needsPointerMove=false;
const style=document.createElement('style');style.textContent=`
#canvas[data-trace-active] .node[data-trace-state="muted"],#canvas[data-trace-active] .edge[data-trace-state="muted"]{opacity:.28}
#canvas[data-trace-active] [data-role-frame]{opacity:.55}
#canvas .node[data-trace-state="current"] .box{stroke-width:2.5;filter:drop-shadow(0 0 5px #5ca7f15c)}
#canvas .node[data-trace-state="neighbor"] .box{stroke-width:2}
#canvas .edge[data-trace-state="related"] .line{stroke:#719bc5;stroke-width:2.2}
#canvas [data-trace-overlay]{pointer-events:none;fill:none;stroke-linecap:round;vector-effect:non-scaling-stroke}
#canvas .trace-halo{stroke:#389cff;stroke-width:8;opacity:.18}
#canvas .trace-flow{stroke:#087bff;stroke-width:4;stroke-dasharray:18 90;animation:relationship-flow 1.2s linear infinite;filter:drop-shadow(0 0 3px #339aff99)}
#canvas .trace-core{stroke:#fff;stroke-width:1.5;stroke-dasharray:6 102;animation:relationship-flow 1.2s linear infinite}
@keyframes relationship-flow{from{stroke-dashoffset:0}to{stroke-dashoffset:-108}}
@media(prefers-reduced-motion:reduce){#canvas .trace-flow,#canvas .trace-core{animation:none;display:none}}
@media print{#canvas [data-trace-overlay]{display:none}}
`;document.body.append(style);
function clear(){active=null;canvas.removeAttribute('data-trace-active');canvas.querySelectorAll('[data-trace-overlay]').forEach(el=>el.remove());canvas.querySelectorAll('[data-trace-state]').forEach(el=>el.removeAttribute('data-trace-state'));}
function preview(id){
 if(interacting||document.hidden||canvas.classList.contains('connecting'))return;
 if(active===id)return;
 clear();if(!graph.nodes.some(n=>n.id===id))return;
 active=id;const neighbors=new Set([id]),edges=new Set();
 for(const edge of graph.edges)if(edge.source===id||edge.target===id){neighbors.add(edge.source);neighbors.add(edge.target);edges.add(edge.id);}
 canvas.setAttribute('data-trace-active',id);
 for(const node of canvas.querySelectorAll('[data-node]'))node.setAttribute('data-trace-state',node.dataset.node===id?'current':neighbors.has(node.dataset.node)?'neighbor':'muted');
 for(const group of canvas.querySelectorAll('.edge[data-edge]')){
  const related=edges.has(group.dataset.edge);group.setAttribute('data-trace-state',related?'related':'muted');if(!related)continue;
  const line=group.querySelector('.line');if(!line)continue;
  // Reuse the authored source-to-target route. Insert below labels and nodes.
  let previous=line;for(const name of ['trace-halo','trace-flow','trace-core']){const overlay=svg('path',{d:line.getAttribute('d'),class:name,'data-trace-overlay':'true','aria-hidden':'true'});previous.after(overlay);previous=overlay;}
 }
}
const nodeFrom=target=>target instanceof Element?target.closest('[data-node]'):null;
function pointer(event){if(event.pointerType==='touch'||event.buttons||interacting)return;if(needsPointerMove&&event.type!=='pointermove')return;needsPointerMove=false;const node=nodeFrom(event.target);if(node)preview(node.dataset.node);else clear();}
canvas.addEventListener('pointerover',pointer);
canvas.addEventListener('pointermove',pointer);
canvas.addEventListener('pointerout',event=>{if(nodeFrom(event.target)!==nodeFrom(event.relatedTarget))clear();});
canvas.addEventListener('pointerleave',clear);
canvas.addEventListener('focusin',event=>{const node=nodeFrom(event.target);if(node)preview(node.dataset.node);});
canvas.addEventListener('focusout',event=>{if(nodeFrom(event.target)!==nodeFrom(event.relatedTarget))clear();});
// Document capture runs before port handlers that stop event propagation.
document.addEventListener('pointerdown',()=>{interacting=true;clear();},true);
for(const name of ['pointerup','pointercancel'])document.addEventListener(name,()=>{interacting=false;clear();},true);
document.addEventListener('keydown',event=>{if(event.key==='Escape')clear();},true);
document.addEventListener('visibilitychange',()=>{interacting=false;clear();});
window.addEventListener('blur',()=>{interacting=false;clear();});
window.addEventListener('beforeprint',clear);
const previousRender=render;render=function(){needsPointerMove=true;clear();return previousRender();};
})();

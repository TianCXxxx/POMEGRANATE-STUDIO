/* Editor bridge for the vendored Archify engine (MIT). */
'use strict';
(()=>{
 Object.assign(semanticStyles.backend,{fill:'#daf6ec',stroke:'#059669'});Object.assign(semanticStyles.database,{fill:'#ece5fd',stroke:'#7c3aed'});Object.assign(semanticStyles.cloud,{fill:'#fff3da',stroke:'#d97706'});Object.assign(semanticStyles.security,{fill:'#fde9ef',stroke:'#e11d48'});Object.assign(semanticStyles.messagebus,{fill:'#fff0e7',stroke:'#ea580c'});Object.assign(semanticStyles.external,{fill:'#edf0f4',stroke:'#64748b'});
 let cachedKey='',engine=null,relations=[];
 function compile(){
  const key=JSON.stringify([graph.nodes.map(n=>[n.id,n.x,n.y]),graph.edges.map(e=>[e.id,e.source,e.target,e.sourceSide,e.targetSide])]);
  if(key!==cachedKey){cachedKey=key;relations=graph.edges.map(e=>({id:e.id,from:e.source,to:e.target,fromSide:e.sourceSide,toSide:e.targetSide}));engine=ArchifyCore.compile({components:graph.nodes.map(n=>({id:n.id,x:n.x,y:n.y,width:180,height:78})),connections:relations});}
  return engine;
 }
 const fallback=connectionGeometry;
 connectionGeometry=function(a,b,edge={}){
  if(a.id===b.id){const sourceSide=edge.sourceSide||'right',targetSide=edge.targetSide||'left';const box={x:a.x,y:a.y,width:180,height:78,cx:a.x+90,cy:a.y+39};const [sx,sy]=ArchifyCore.anchor(box,sourceSide),[tx,ty]=ArchifyCore.anchor(box,targetSide);return{sourceSide,targetSide,source:{x:sx,y:sy},target:{x:tx,y:ty},points:[{x:sx,y:sy},{x:tx,y:ty}],d:`M${sx},${sy} L${tx},${ty}`,x:sx,y:sy};}
  const core=compile(),relation=relations.find(r=>r.id===edge.id&&r.from===a.id&&r.to===b.id&&r.fromSide===edge.sourceSide&&r.toSide===edge.targetSide);
  if(!relation)return fallback(a,b,edge);
  const routed=core.pathFor(relation),sides=core.connectionSides(relation),points=routed.points.map(p=>({x:p[0],y:p[1]}));
  // Native Archify routes are used when they clear obstacles; retain the editor's
  // visibility-grid fallback for a dragged layout that needs an unbounded detour.
  if(graph.nodes.some(n=>n.id!==a.id&&n.id!==b.id&&routed.points.slice(1).some((p,i)=>ArchifyCore.segmentIntersectsRect({start:routed.points[i],end:p},{x:n.x,y:n.y,width:180,height:78},2)))){
   const other=fallback(a,b,edge);other.d=ArchifyCore.roundedPath(other.points.map(p=>[p.x,p.y]),8);return other;
  }
  let segment=points.slice(0,2),length=-1;for(let i=1;i<points.length;i++){const l=Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y);if(l>length){length=l;segment=[points[i-1],points[i]]}}
  return{sourceSide:sides.fromSide,targetSide:sides.toSide,source:points[0],target:points.at(-1),points,d:routed.d,x:(segment[0].x+segment[1].x)/2,y:(segment[0].y+segment[1].y)/2-12};
 };
 route=(a,b,e)=>connectionGeometry(a,b,e);
 // Collapse strongly connected components before ranking. Cycles are preserved
 // as edges rather than repeatedly pushing nodes into ever deeper columns.
 arrangeSemantic=function(nodes,edges){
  const ids=new Set(nodes.map(n=>n.id)),adj=new Map(nodes.map(n=>[n.id,[]]));for(const e of edges)if(ids.has(e.source)&&ids.has(e.target))adj.get(e.source).push(e.target);
  let counter=0;const index=new Map(),low=new Map(),stack=[],on=new Set(),components=[],component=new Map();
  function visit(id){index.set(id,counter);low.set(id,counter++);stack.push(id);on.add(id);for(const next of adj.get(id)){if(!index.has(next)){visit(next);low.set(id,Math.min(low.get(id),low.get(next)))}else if(on.has(next))low.set(id,Math.min(low.get(id),index.get(next)))}if(low.get(id)===index.get(id)){const group=[];let popped;do{popped=stack.pop();on.delete(popped);component.set(popped,components.length);group.push(popped)}while(popped!==id);components.push(group)}}
  for(const n of nodes)if(!index.has(n.id))visit(n.id);
  const ranks=components.map(()=>0);for(let pass=0;pass<components.length;pass++){let changed=false;for(const e of edges){const a=component.get(e.source),b=component.get(e.target);if(a!==undefined&&b!==undefined&&a!==b&&ranks[b]<ranks[a]+1){ranks[b]=ranks[a]+1;changed=true}}if(!changed)break}
  const columns=[];for(const n of nodes){const rank=ranks[component.get(n.id)];(columns[rank]??=[]).push(n)}
  const position=new Map();for(let col=0;col<columns.length;col++){const list=columns[col]||[];list.sort((a,b)=>{const earliest=id=>Math.min(col,...edges.filter(e=>e.target===id&&component.has(e.source)).map(e=>ranks[component.get(e.source)]));const average=id=>{const parents=edges.filter(e=>e.target===id&&position.has(e.source));return parents.length?parents.reduce((s,e)=>s+position.get(e.source),0)/parents.length:0};return earliest(a.id)-earliest(b.id)||average(a.id)-average(b.id)||a.name.localeCompare(b.name)});list.forEach((n,row)=>position.set(n.id,row));}
  const count=Math.max(1,...columns.map(c=>c?.length||0));columns.forEach((list,col)=>list?.forEach((n,row)=>{n.x=60+col*310;n.y=65+(count-list.length)*72+row*144}));return nodes;
 };
 const previousRender=render;
 render=function(){previousRender();const canvas=$('canvas');for(const group of canvas.querySelectorAll('[data-node]')){
  const node=graph.nodes.find(n=>n.id===group.dataset.node);if(!node)continue;
  group.querySelectorAll('g:not([data-semantic-sigil])').forEach(g=>g.remove());
  const icon=document.createElementNS(NS,'g');icon.innerHTML=ArchifyCore.renderSemanticSigil(semanticType(node)==='model'?'cloud':semanticType(node),{x:10,y:10,size:14});icon.setAttribute('fill','none');icon.setAttribute('stroke',semanticStyles[semanticType(node)].stroke);icon.setAttribute('stroke-width','1.35');icon.setAttribute('stroke-linecap','round');icon.setAttribute('stroke-linejoin','round');icon.querySelectorAll('.sigil-fill').forEach(n=>{n.setAttribute('fill',semanticStyles[semanticType(node)].stroke);n.setAttribute('stroke','none')});group.append(icon);
  const title=group.querySelector('title');if(title)title.textContent=node.name+'\n'+node.sub+'\n'+(node.evidence||[]).map(e=>e.file+':'+e.line).join('\n');
  const texts=[...group.querySelectorAll('text')];texts.filter(t=>t.getAttribute('text-anchor')==='middle').forEach(t=>t.remove());
  group.append(svg('text',{x:90,y:39,'text-anchor':'middle',fill:'#0f172a','font-family':'Segoe UI,Microsoft YaHei,sans-serif','font-size':ArchifyCore.fittedNodeFontSize(node.name,162,13,9.5),'font-weight':600},node.name));
  group.append(svg('text',{x:90,y:57,'text-anchor':'middle',fill:'#64748b','font-family':'Segoe UI,Microsoft YaHei,sans-serif','font-size':ArchifyCore.fittedNodeFontSize(node.sub,162,9,7)},node.sub));
  // Keep the four editor handles above authored node content.
  group.querySelectorAll('.port').forEach(p=>group.append(p));
 }
 if(graph.nodes.length){
  const columns=new Map();for(const node of graph.nodes){const key=Math.round(node.x/100)*100;(columns.get(key)||columns.set(key,[]).get(key)).push(node)}
  const frames=svg('g',{'data-layout-decoration':'roles','pointer-events':'none'});
  for(const list of columns.values()){const left=Math.min(...list.map(n=>n.x))-18,top=Math.min(...list.map(n=>n.y))-37,right=Math.max(...list.map(n=>n.x+180))+18,bottom=Math.max(...list.map(n=>n.y+78))+18;
   const types=new Set(list.map(semanticType));const label=types.has('frontend')?'前端界面':list.every(n=>n.type==='external'||n.type==='database')?'数据与外部依赖':list.some(n=>n.listen)?'接口入口':list.every(n=>/业务服务/.test(n.sub))?'业务逻辑':list.some(n=>/适配器|数据访问/.test(n.sub))?'数据访问与集成':'服务与组件';
   frames.append(svg('rect',{x:left,y:top,width:right-left,height:bottom-top,rx:10,fill:'#f8fafc',stroke:'#e2e8f0','stroke-width':.7}));frames.append(svg('text',{x:left+12,y:top+19,fill:'#64748b','font-size':10,'font-weight':500,'font-family':'Segoe UI,Microsoft YaHei,sans-serif'},label));
  }
  canvas.insertBefore(frames,canvas.querySelector('[data-edge]')||canvas.querySelector('[data-node]'));
 }
 const report=[];for(const edge of graph.edges){const a=graph.nodes.find(n=>n.id===edge.source),b=graph.nodes.find(n=>n.id===edge.target);if(!a||!b)continue;const geometry=connectionGeometry(a,b,edge);for(const node of graph.nodes){if(node.id===a.id||node.id===b.id)continue;const points=geometry.points; if(points.slice(1).some((p,i)=>ArchifyCore.segmentIntersectsRect({start:[points[i].x,points[i].y],end:[p.x,p.y]},{x:node.x,y:node.y,width:180,height:78},2)))report.push(edge.id+' 穿过 '+node.name)}
  const group=[...canvas.querySelectorAll('[data-edge]')].find(g=>g.dataset.edge===edge.id);if(group){const title=svg('title',{},edge.label+'\n'+(edge.evidence||[]).map(e=>e.file+':'+e.line).join('\n'));group.append(title)}
 }
 // Labels must stay clear of nodes, one another and unrelated connection paths.
 const placed=[];const routed=graph.edges.map(edge=>({edge,geometry:connectionGeometry(graph.nodes.find(n=>n.id===edge.source),graph.nodes.find(n=>n.id===edge.target),edge)}));
 const overlaps=(a,b)=>a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;
 const labelIssues=[];
 for(const {edge,geometry}of routed){const group=[...canvas.querySelectorAll('[data-edge]')].find(g=>g.dataset.edge===edge.id),texts=[...group.querySelectorAll('text')],mask=group.querySelector('rect');if(!mask||!texts.length)continue;
  // Preserve full labels in the project and inspector, abbreviate only the canvas.
  if(texts[1])texts[1].textContent=short(edge.label,30);
  const width=Math.max(44,...texts.map(t=>t.getComputedTextLength()+12)),height=texts.length>1?30:16,candidates=[];
  for(let i=1;i<geometry.points.length;i++){const p=geometry.points[i-1],q=geometry.points[i],length=Math.hypot(p.x-q.x,p.y-q.y);if(length<32)continue;const x=(p.x+q.x)/2,y=(p.y+q.y)/2;
   for(const offset of [-20,24,-40,44,-60,64])candidates.push(p.y===q.y?{x,y:y+offset}:{x:x+(offset<0?-width/2-10:width/2+10),y:y+offset/3});
  }
  let best,bestScore=Infinity;for(const candidate of candidates){const rect={x:candidate.x-width/2,y:candidate.y-10,width,height};let score=rect.x<5||rect.y<5?10000:0;score+=graph.nodes.filter(n=>overlaps(rect,{x:n.x-8,y:n.y-8,width:196,height:94})).length*10000;score+=placed.filter(r=>overlaps(rect,r)).length*2000;
   for(const other of routed){if(other.edge.id===edge.id)continue;const p=other.geometry.points;score+=p.slice(1).filter((end,i)=>ArchifyCore.segmentIntersectsRect({start:[p[i].x,p[i].y],end:[end.x,end.y]},rect,2)).length*200;}
   if(score<bestScore){best={...candidate,rect};bestScore=score}if(score===0)break;
  }
  if(best){mask.setAttribute('x',best.rect.x);mask.setAttribute('y',best.rect.y);mask.setAttribute('width',width);mask.setAttribute('height',height);texts.forEach((t,i)=>{t.setAttribute('x',best.x);t.setAttribute('y',best.y+i*13)});placed.push(best.rect);if(bestScore>=2000)labelIssues.push(edge.id+' 标签需要人工调整');}
 }
 const qualityRelations=routed.map(({edge,geometry})=>({id:edge.id,from:edge.source,to:edge.target,fromSide:geometry.sourceSide,toSide:geometry.targetSide,geometry})),pathFor=r=>({points:r.geometry.points.map(p=>[p.x,p.y])}),endpointIds=new Set(graph.nodes.map(n=>n.id));ArchifyCore.diagnostics.length=0;
 const endpointIssues=ArchifyCore.cleanEndpointSideProblems({relations:qualityRelations,endpointIds,pathFor,diagramType:'architecture',relationCollection:'connections'});
 const crossings=ArchifyCore.cleanCrossingProblems({relations:qualityRelations,endpointIds,pathFor,diagramType:'architecture',relationCollection:'connections',profile:'showcase',profileIsAuthoritative:true});
 window.architectureQuality={engine:'Archify geometry + editor bridge',edgeThroughNode:report,endpointIssues,crossings,labelIssues};
 };
 const oldInspect=inspect;inspect=function(){oldInspect();const item=selection?.kind==='node'?graph.nodes.find(n=>n.id===selection.id):selection?.kind==='edge'?graph.edges.find(e=>e.id===selection.id):null;if(item?.evidence)$('evidence').textContent='源码依据：'+item.evidence.map(e=>e.file+':'+e.line).join('、');};
 const exportButton=document.createElement('button');exportButton.id='archifyHtml';exportButton.className='small';exportButton.textContent='导出 Archify HTML';$('png').before(exportButton);
 exportButton.onclick=async()=>{if(!graph.nodes.length)return;exportButton.disabled=true;exportButton.textContent='Archify 正在校验…';try{
  const output={...graph,edges:graph.edges.map(edge=>{const group=[...$('canvas').querySelectorAll('[data-edge]')].find(g=>g.dataset.edge===edge.id),label=group?.querySelector('text'),a=graph.nodes.find(n=>n.id===edge.source),b=graph.nodes.find(n=>n.id===edge.target),actual=connectionGeometry(a,b,edge),native=compile().pathFor(relations.find(r=>r.id===edge.id)),detour=JSON.stringify(native.points)!==JSON.stringify(actual.points.map(p=>[p.x,p.y]));return{...edge,exportGeometry:{fromSide:detour?actual.sourceSide:edge.sourceSide,toSide:detour?actual.targetSide:edge.targetSide,points:detour?actual.points.map(p=>[p.x,p.y]):undefined,labelAt:label?[Number(label.getAttribute('x')),Number(label.getAttribute('y'))]:undefined}}})};
  const reply=await fetch('http://127.0.0.1:18767/export-archify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({graph:output}),signal:AbortSignal.timeout(20000)});const result=await reply.json();if(!reply.ok)throw Error(result.error);download(new Blob([result.html],{type:'text/html;charset=utf-8'}),'架构图-Archify.html');toast('已用 Archify 原生渲染器导出独立 HTML');
 }catch(error){toast(error.message||'Archify 导出失败')}finally{exportButton.disabled=false;exportButton.textContent='导出 Archify HTML'}};
 bounds=function(){const points=graph.edges.flatMap(e=>{const a=graph.nodes.find(n=>n.id===e.source),b=graph.nodes.find(n=>n.id===e.target);return a&&b?connectionGeometry(a,b,e).points:[]});return{x:0,y:0,w:Math.max(500,...graph.nodes.map(n=>n.x+220),...points.map(p=>p.x+80)),h:Math.max(320,...graph.nodes.map(n=>n.y+120),...points.map(p=>p.y+80))};};
 let camera={w:1000,h:690};
 updateZoom=function(){const w=camera.w/zoom,h=camera.h/zoom;$('canvas').setAttribute('viewBox',`${(camera.w-w)/2} ${(camera.h-h)/2} ${w} ${h}`);$('zoom').textContent=Math.round(zoom*100)+'%';};
 $('fit').onclick=()=>{zoom=1;camera=bounds();updateZoom();$('zoom').textContent='适应';};
 render();
})();

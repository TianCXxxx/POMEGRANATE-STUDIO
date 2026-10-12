/* Compact, evidence-preserving composition: core spine + dependency branches. */
'use strict';
(()=>{
const previous=arrangeSemantic;
let verticalGap=150;
arrangeSemantic=function(nodes,edges){
 previous(nodes,edges);const byId=new Map(nodes.map(n=>[n.id,n]));
 const serviceGroups=[...new Set(nodes.map(n=>n.architectureGroup).filter(g=>g&&g!=='__shared__'))].sort();
 if(serviceGroups.length>1){
  const groups=[...serviceGroups,'__shared__','__other__'];const panels=[];
  for(const group of groups){const list=nodes.filter(n=>(n.architectureGroup||'__other__')===group);if(!list.length)continue;
   const ids=new Set(list.map(n=>n.id)),remaining=new Set(ids),levels=[];
   while(remaining.size){let ready=[...remaining].filter(id=>!edges.some(e=>e.target===id&&remaining.has(e.source)&&e.source!==id));if(!ready.length)ready=[[...remaining].sort()[0]];ready.sort();levels.push(ready.map(id=>byId.get(id)));ready.forEach(id=>remaining.delete(id));}
   // Cyclic or deep dependency chains must not force an unbounded single column.
   // Keep topological order, but pack large groups into bounded source panels.
   if(list.length>24){const ordered=levels.flat();levels.length=0;for(let i=0;i<ordered.length;i+=4)levels.push(ordered.slice(i,i+4));}
   const width=Math.max(260,...list.map(n=>n.width)),gap=90,cols=Math.min(list.length>24?4:3,Math.max(1,...levels.map(l=>l.length)));let y=0;
   for(const level of levels)for(let begin=0;begin<level.length;begin+=cols){const row=level.slice(begin,begin+cols),height=Math.max(...row.map(n=>n.height));row.forEach((node,i)=>{node.x=i*(width+gap);node.y=y;node.layoutRow=levels.indexOf(level);});y+=Math.max(verticalGap,height+65);}
   panels.push({group,nodes:list,width:cols*width+(cols-1)*gap,height:y});
  }
  // Tile service panels in bounded rows instead of one unbounded horizontal strip.
  const maxWidth=2400;let x=65,y=85,rowHeight=0;
  for(const panel of panels){if(x>65&&x+panel.width>maxWidth){x=65;y+=rowHeight+150;rowHeight=0;}for(const node of panel.nodes){node.x+=x;node.y+=y;node.layoutColumn=panels.indexOf(panel);}x+=panel.width+160;rowHeight=Math.max(rowHeight,panel.height);}
  return nodes;
 }

 if(nodes.length>48){
  const order={frontend:0,entry:1,business:2,repository:3,integration:4,data:5};
  const list=[...nodes].sort((a,b)=>(order[a.architectureRole]??3)-(order[b.architectureRole]??3)||a.name.localeCompare(b.name));
  const cols=4,width=Math.max(260,...nodes.map(n=>n.width));let y=85;
  for(let i=0;i<list.length;i+=cols){const row=list.slice(i,i+cols);for(let col=0;col<row.length;col++){const n=row[col];n.x=65+col*(width+120);n.y=y;n.layoutRow=i/cols;n.layoutColumn=col;}y+=Math.max(verticalGap,Math.max(...row.map(n=>n.height))+65);}
  return nodes;
 }

 const frontend=nodes.filter(n=>semanticType(n)==='frontend'),apis=nodes.filter(n=>(n.architectureRole==='entry'||n.layoutRole==='后端接口')),stores=nodes.filter(n=>semanticType(n)==='database'),repositories=nodes.filter(n=>/仓储|repository|数据访问/i.test(n.name+' '+n.sub)&&semanticType(n)==='backend');
 const adapters=nodes.filter(n=>(n.architectureRole==='integration'||n.layoutRole==='后端集成')&&!repositories.includes(n));
 const inbound=nodes.filter(n=>semanticType(n)==='external'&&edges.some(e=>e.source===n.id&&apis.some(a=>a.id===e.target)));
 const assigned=new Set(),lanes=[[],[],[]];
 function put(node,col,row){if(assigned.has(node.id))return;assigned.add(node.id);lanes[col].push({node,row});}
 function topo(list){const result=[],remaining=new Set(list.map(n=>n.id));while(remaining.size){const id=[...remaining].find(id=>!edges.some(e=>e.target===id&&remaining.has(e.source)&&e.source!==id))||remaining.values().next().value;remaining.delete(id);result.push(byId.get(id));}return result;}
 let mainRow=0;const front=topo(frontend);for(let i=0;i<front.length;i++){put(front[i],i%2===0&&i+1<front.length?0:1,Math.floor(i/2));}mainRow=Math.ceil(front.length/2);
 const apiRow=mainRow;for(const node of apis)put(node,1,mainRow++);
 const serviceRow=mainRow;for(const node of topo(nodes.filter(n=>semanticType(n)==='backend'&&!assigned.has(n.id)&&!repositories.includes(n)&&!adapters.includes(n))))put(node,1,mainRow++);
 // Repository branches sit above the service, leaving a clear API/service/repository triangle.
 let leftRow=apiRow;for(const node of inbound)put(node,0,leftRow++);
 for(const node of repositories){put(node,0,leftRow++);const db=edges.filter(e=>e.source===node.id).map(e=>byId.get(e.target)).filter(n=>n&&stores.includes(n));for(const target of db)put(target,0,leftRow++);}
 let rightRow=apiRow;for(const node of adapters){put(node,2,rightRow++);const dependencies=edges.filter(e=>e.source===node.id).map(e=>byId.get(e.target)).filter(n=>n&&!assigned.has(n.id)&&semanticType(n)!=='backend'&&semanticType(n)!=='frontend');for(const target of dependencies)put(target,2,rightRow++);}
 for(const node of nodes.filter(n=>!assigned.has(n.id)))put(node,2,rightRow++);
 const rows=Math.max(1,...lanes.flatMap(list=>list.map(v=>v.row+1))),heights=Array.from({length:rows},(_,r)=>Math.max(112,...lanes.flatMap(list=>list.filter(v=>v.row===r).map(v=>v.node.height))));
 const tops=[85];for(let row=1;row<rows;row++)tops.push(tops[row-1]+Math.max(verticalGap,heights[row-1]+32));
 const active=lanes.map((list,index)=>list.length?index:null).filter(i=>i!==null);
 for(const col of active)for(const {node,row}of lanes[col]){node.x=65+active.indexOf(col)*510;node.y=tops[row];node.layoutColumn=active.indexOf(col);node.layoutRow=row;}
 return nodes;
};
})();
/* Evidence-preserving layered layout. Cycles are condensed, never deleted. */
'use strict';
(()=>{
 const previous=arrangeSemantic;
 arrangeSemantic=function(nodes,edges){
  previous(nodes,edges);if(!nodes.length)return nodes;
  const byId=new Map(nodes.map(n=>[n.id,n])),stable=(a,b)=>a.id.localeCompare(b.id);
  const structural=edges.filter(e=>byId.has(e.source)&&byId.has(e.target)&&e.architectureImportance!=='support'&&!['import','type-reference','dependency'].includes(e.relationKind));
  const adjacency=new Map(nodes.map(n=>[n.id,[]]));for(const e of structural)adjacency.get(e.source).push(e.target);
  // Tarjan SCC: mutually dependent components share a rank instead of forming an artificial chain.
  let clock=0;const index=new Map(),low=new Map(),stack=[],active=new Set(),components=[],owner=new Map();
  function visit(id){index.set(id,clock);low.set(id,clock++);stack.push(id);active.add(id);for(const target of adjacency.get(id)){if(!index.has(target)){visit(target);low.set(id,Math.min(low.get(id),low.get(target)));}else if(active.has(target))low.set(id,Math.min(low.get(id),index.get(target)));}if(low.get(id)===index.get(id)){const members=[];let member;do{member=stack.pop();active.delete(member);owner.set(member,components.length);members.push(byId.get(member));}while(member!==id);components.push(members.sort(stable));}}
  [...nodes].sort(stable).forEach(n=>{if(!index.has(n.id))visit(n.id);});
  const successors=components.map(()=>new Set()),incoming=components.map(()=>0),rank=components.map(()=>0);
  for(const e of structural){const a=owner.get(e.source),b=owner.get(e.target);if(a!==b&&!successors[a].has(b)){successors[a].add(b);incoming[b]++;}}
  const ready=incoming.map((v,i)=>v===0?i:-1).filter(i=>i>=0);while(ready.length){const a=ready.shift();for(const b of successors[a]){rank[b]=Math.max(rank[b],rank[a]+1);if(--incoming[b]===0)ready.push(b);}}
  const roleOrder={frontend:0,entry:1,business:2,helper:3,repository:4,integration:4,'data-model':5,data:6};
  const rows=new Map();for(const node of nodes){const r=Math.min(rank[owner.get(node.id)],5);node.layoutCycleSize=components[owner.get(node.id)].length;if(!rows.has(r))rows.set(r,[]);rows.get(r).push(node);}
  const layers=[...rows.entries()].sort((a,b)=>a[0]-b[0]).map(([_,list])=>list);layers.forEach(list=>list.sort((a,b)=>(roleOrder[a.architectureRole]??3)-(roleOrder[b.architectureRole]??3)||String(a.architectureGroup||'').localeCompare(String(b.architectureGroup||''))||stable(a,b)));
  // Alternating barycentric sweeps reduce crossings while preserving the DAG ranks.
  for(let pass=0;pass<6;pass++){const positions=new Map(layers.flatMap(list=>list.map((n,i)=>[n.id,i])));for(const list of pass%2?[...layers].reverse():layers){const center=n=>{const related=structural.filter(e=>pass%2?e.source===n.id:e.target===n.id).map(e=>positions.get(pass%2?e.target:e.source));return related.length?related.reduce((a,b)=>a+b,0)/related.length:positions.get(n.id);};list.sort((a,b)=>center(a)-center(b)||stable(a,b));}}
  const cols=4,pitch=400,totalWidth=cols*pitch-160;let y=85;
  layers.forEach((list,layer)=>{for(let start=0;start<list.length;start+=cols){const row=list.slice(start,start+cols),height=Math.max(...row.map(n=>n.height));row.forEach((node,col)=>{node.x=65+(totalWidth-(row.length*pitch-160))/2+col*pitch;node.y=y;node.layoutColumn=col;node.layoutRow=layer;node.layoutFrame=`layer-${layer}-row-${start/cols}`;node.layoutFrameLabel=[...new Set(row.map(n=>architectureRoleLabel(n)))].join(' · ');});y+=height+150;}});
  if(typeof graph!=='undefined'&&graph.nodes===nodes&&graph.edges===edges){
   const fields=['x','y','layoutColumn','layoutRow','layoutFrame','layoutFrameLabel','layoutCycleSize'];
   const snapshot=()=>nodes.map(n=>Object.fromEntries(fields.map(k=>[k,n[k]])));
   const restore=state=>nodes.forEach((n,i)=>fields.forEach(k=>{if(state[i][k]===undefined)delete n[k];else n[k]=state[i][k];}));
   render();let best=snapshot(),score=layoutScore();const candidates=[{strategy:"layered-scc",score,checks:Object.fromEntries(Object.entries(architectureQuality.checks).map(([k,v])=>[k,v.length]))}];
   previous(nodes,edges);nodes.forEach(n=>{delete n.layoutFrame;delete n.layoutFrameLabel;});render();
   candidates.push({strategy:"spine",score:layoutScore(),checks:Object.fromEntries(Object.entries(architectureQuality.checks).map(([k,v])=>[k,v.length]))});if(layoutScore()<score){best=snapshot();score=layoutScore();}
   nodes.forEach(n=>n.y=85+(n.y-85)*.9);render();
   const fallbackScore=layoutScore();candidates.push({strategy:"compressed-spine",score:fallbackScore,checks:Object.fromEntries(Object.entries(architectureQuality.checks).map(([k,v])=>[k,v.length]))});if(fallbackScore<score){best=snapshot();score=fallbackScore;}restore(best);
   graph.layoutReceipt={strategy:best[0]?.layoutFrame?'layered-scc':'compact-spine',score,candidates};
  }
  return nodes;
 };
 function layoutScore(){const c=architectureQuality.checks,b=bounds();return (c.nodeOverlap.length+c.edgeThroughNode.length+c.endpointIssues.length+c.textOverflow.length)*100000+c.labelNode.length*1000+c.labelOverlap.length*50+c.labelPath.length*25+c.crossings.length*25+(b.w-b.x)*(b.h-b.y)/100000;}

})();

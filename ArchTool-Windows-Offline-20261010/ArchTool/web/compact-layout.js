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
   const width=Math.max(260,...list.map(n=>n.width)),gap=90,cols=Math.min(3,Math.max(1,...levels.map(l=>l.length)));let y=0;
   for(const level of levels)for(let begin=0;begin<level.length;begin+=cols){const row=level.slice(begin,begin+cols),height=Math.max(...row.map(n=>n.height));row.forEach((node,i)=>{node.x=i*(width+gap);node.y=y;node.layoutRow=levels.indexOf(level);});y+=Math.max(verticalGap,height+65);}
   panels.push({group,nodes:list,width:cols*width+(cols-1)*gap,height:y});
  }
  // Tile service panels in bounded rows instead of one unbounded horizontal strip.
  const maxWidth=2400;let x=65,y=85,rowHeight=0;
  for(const panel of panels){if(x>65&&x+panel.width>maxWidth){x=65;y+=rowHeight+150;rowHeight=0;}for(const node of panel.nodes){node.x+=x;node.y+=y;node.layoutColumn=panels.indexOf(panel);}x+=panel.width+160;rowHeight=Math.max(rowHeight,panel.height);}
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
window.repairArchitectureLayout=function(){if(!graph.nodes.length)return 0;let best,count=Infinity;for(const gap of [150,165,180]){verticalGap=gap;arrangeSemantic(graph.nodes,graph.edges);render();const candidateCount=architectureQuality.warningCount;if(candidateCount<count){best=JSON.stringify(graph);count=candidateCount;}if(!count)break;}verticalGap=150;graph=JSON.parse(best);render();inspect();$('fit').click();return count;};
})();

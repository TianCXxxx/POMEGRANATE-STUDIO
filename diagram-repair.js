/* Bounded diagnosis-driven repair; commit only measurable improvements. */
'use strict';
(()=>{
const intersects=(a,b,p=12)=>a.x<b.x+b.width+p&&a.x+a.width+p>b.x&&a.y<b.y+b.height+p&&a.y+a.height+p>b.y;
const snapshot=()=>JSON.stringify(graph);
const score=()=>{const q=architectureQuality;return q.nodeOverlap.length*1000+q.edgeThroughNode.length*500+q.endpointIssues.length*500+q.textOverflow.length*500+q.labelNode.length*200+q.labelOverlap.length*100+q.labelPath.length*30+q.crossings.length*20+q.bounds.length*1000;};
window.repairArchitectureLayout=function(){
 if(!graph.nodes.length)return 0;
 // Preserve a good authored layout. Diagnosis is performed on the current scene.
 render();const initial=architectureQuality.warningCount,steps=[],deadline=performance.now()+(graph.nodes.length>32?8000:20000);let best=score(),stalled=0;
 for(let round=0;round<8&&best>0&&stalled<2&&performance.now()<deadline;round++){
  let improved=false;const scene=canonicalArchitectureScene(),trials=[];
  for(let i=0;i<graph.nodes.length;i++)for(const other of graph.nodes.slice(i+1))if(intersects(graph.nodes[i],other))for(const [dx,dy] of [[0,other.height+65],[other.width+90,0]])trials.push({kind:'move-node',id:other.id,apply:()=>{const n=graph.nodes.find(n=>n.id===other.id);n.x+=dx;n.y+=dy;}});
  const edgeIds=new Set([...architectureQuality.edgeThroughNode.map(s=>s.split(' → ')[0]),...architectureQuality.labelIssues]);
  if(architectureQuality.crossings.length||architectureQuality.endpointIssues.length)scene.routes.forEach(r=>edgeIds.add(r.edge.id));
  for(const id of edgeIds){const edge=graph.edges.find(e=>e.id===id);if(!edge)continue;trials.push({kind:'reroute',id,apply:()=>graph.edges.find(e=>e.id===id).repairRoute='detour'});
   // Respect endpoints explicitly selected by the user.
   if(!edge.sourceSide&&!edge.targetSide)for(const [a,b] of [['right','left'],['bottom','top'],['left','right'],['top','bottom']])trials.push({kind:'endpoint-route',id,apply:()=>{const e=graph.edges.find(e=>e.id===id);e.sourceSide=a;e.targetSide=b;e.repairRoute='detour';}});
   const label=scene.labels.find(l=>l.edgeId===id);if(label)for(const [dx,dy] of [[0,-35],[0,35],[-60,0],[60,0],[0,-75],[0,75]])trials.push({kind:'move-label',id,apply:()=>graph.edges.find(e=>e.id===id).repairLabel={x:label.x+dx,y:label.y+dy}});
  }
  // Bound expensive routing work and never accept a worse result.
  for(const trial of trials.slice(0,60)){if(performance.now()>=deadline)break;const before=snapshot();trial.apply();render();const value=score();if(value<best){steps.push({round:round+1,subject:trial.id,action:trial.kind,beforeScore:best,afterScore:value});best=value;improved=true;break;}graph=JSON.parse(before);render();}
  stalled=improved?0:stalled+1;
 }
 graph.repairReceipt={initialWarnings:initial,remainingWarnings:architectureQuality.warningCount,steps,stoppedReason:best===0?'passed':performance.now()>=deadline?'time-budget':stalled>=2?'no-improvement':'round-limit',scope:'编辑器实际节点、路径与标签诊断；原生 showcase 单独验收'};
 render();inspect();$('fit').click();return architectureQuality.warningCount;
};
})();

'use strict';
(()=>{
const button=document.createElement('button');button.id='drawio';button.className='small';button.textContent='导出 drawio';$('png').before(button);
function htmlText(value){return String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')}
function exportDrawio(){
 const doc=document.implementation.createDocument(null,'mxfile'),file=doc.documentElement;file.setAttribute('host','drawio');file.setAttribute('agent','构图本地工作台');
 function el(tag,attrs,parent){const node=doc.createElement(tag);for(const [key,value]of Object.entries(attrs))node.setAttribute(key,String(value));parent.append(node);return node}
 const diagram=el('diagram',{id:'architecture',name:graph.title||'架构图'},file),dim=bounds(),model=el('mxGraphModel',{dx:dim.w,dy:dim.h,grid:1,gridSize:10,guides:1,tooltips:1,connect:1,arrows:1,fold:1,page:1,pageScale:1,pageWidth:dim.w,pageHeight:dim.h,background:'#ffffff'},diagram),root=el('root',{},model);
 el('mxCell',{id:'0'},root);el('mxCell',{id:'1',parent:'0'},root);
 const ids=new Map(graph.nodes.map((node,index)=>[node.id,String(index+2)]));
 for(const node of graph.nodes){const style=semanticStyles[semanticType(node)];const value='<b>'+htmlText(node.name)+'</b><br><span style="color:#929292;font-size:10px">'+htmlText(node.sub)+'</span>',cell=el('mxCell',{id:ids.get(node.id),value,style:'rounded=1;arcSize=13;whiteSpace=wrap;html=1;fillColor='+style.fill+';strokeColor='+style.stroke+';fontColor=#333333;fontSize=13;align=left;verticalAlign=middle;spacingLeft=15;spacingRight=10;',vertex:1,parent:'1'},root);el('mxGeometry',{x:node.x,y:node.y,width:180,height:78,as:'geometry'},cell)}
 graph.edges.forEach((edge,index)=>{
 const a=graph.nodes.find(n=>n.id===edge.source),b=graph.nodes.find(n=>n.id===edge.target);if(!a||!b)return;
 const attachment=connectionGeometry(a,b,edge);const horizontal=Math.abs(b.x-a.x)>190&&Math.abs(b.y-a.y)<130,right=b.x>a.x,down=b.y>=a.y;
 const exitX=(attachment.source.x-a.x)/180,exitY=(attachment.source.y-a.y)/78,entryX=(attachment.target.x-b.x)/180,entryY=(attachment.target.y-b.y)/78;
 const transport=(edge.protocol||'协议待确认')+' · '+(edge.port?'端口 '+edge.port:'端口待确认');
 const value=htmlText(transport)+(edge.label?'<br>'+htmlText(edge.label):'');
 const cell=el('mxCell',{id:String(graph.nodes.length+2+index),value,style:'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;endFill=1;strokeColor=#b1b7c0;fontColor=#626973;fontSize=10;labelBackgroundColor=#ffffff;'+(edge.style==='dashed'?'dashed=1;dashPattern=5 5;':'')+'exitX='+exitX+';exitY='+exitY+';exitDx=0;exitDy=0;entryX='+entryX+';entryY='+entryY+';entryDx=0;entryDy=0;',edge:1,parent:'1',source:ids.get(a.id),target:ids.get(b.id)},root);
 const geometry=el('mxGeometry',{relative:1,as:'geometry'},cell),points=el('Array',{as:'points'},geometry);
 for(const p of attachment.points.slice(1,-1))el('mxPoint',{x:p.x,y:p.y},points);
 });
 return '<?xml version="1.0" encoding="UTF-8"?>\n'+new XMLSerializer().serializeToString(doc);
}
button.onclick=()=>{try{download(new Blob([exportDrawio()],{type:'application/xml;charset=utf-8'}),'构图-架构图.drawio');toast('已导出 drawio，可继续编辑组件与连线')}catch(error){toast('drawio 导出失败：'+error.message)}};
})();

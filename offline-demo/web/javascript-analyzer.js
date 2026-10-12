/* Static JS/TS module facts. Parser: @babel/parser MIT, bundled locally. */
window.analyzeJavascript=function(files){
 const nodes=[],edges=[],warnings=[],parsed=[],byFile=new Map(),dedupe=new Map();
 const basename=s=>s.split(/[\\/]/).at(-1).replace(/\.(tsx?|jsx?|mjs|cjs)$/,'');
 function walk(n,visit){if(!n||typeof n!=='object')return;if(typeof n.type==='string')visit(n);for(const [k,v]of Object.entries(n))if(!['loc','start','end','extra','tokens','comments'].includes(k)){if(Array.isArray(v))v.forEach(x=>walk(x,visit));else if(v&&typeof v==='object')walk(v,visit)}}
 function path(n){return n?.type==='Identifier'?n.name:n?.type==='MemberExpression'?path(n.object)+'.'+(n.property.name||n.property.value):''}
 function literal(n){if(n?.type==='StringLiteral'||n?.type==='NumericLiteral')return n.value;if(n?.type==='TemplateLiteral')return n.quasis.map(q=>q.value.cooked).join('{dynamic}');if(n?.type==='BinaryExpression'&&n.operator==='+'){const left=literal(n.left);return typeof left==='string'?left+(literal(n.right)??'{dynamic}'):undefined}}
 function evidence(name,n){return{file:name,line:n.loc.start.line}}
 function edge(source,target,label,protocol,port,ev){if(source===target)return;const key=JSON.stringify([source,target,protocol,port]);if(dedupe.has(key)){const old=dedupe.get(key);old.evidence.push(ev);return}const value={id:'js-fact-'+edges.length,source,target,label,protocol,port,style:'solid',evidence:[ev]};dedupe.set(key,value);edges.push(value)}
 for(const file of files){if(!/\.(tsx?|jsx?|mjs|cjs)$/.test(file.name)){warnings.push(file.name+'：未按 JavaScript / TypeScript 解析');continue}try{
  const tree=BabelParser.parse(file.text,{sourceType:'unambiguous',plugins:[...(/\.tsx?$/.test(file.name)?['typescript']:[]),'jsx'],errorRecovery:false});let frontend=false;
  walk(tree,n=>{if(n.type==='JSXElement'||n.type==='JSXFragment')frontend=true});
  const node={id:'module:'+file.name,name:basename(file.name),sub:frontend?'前端组件 · '+file.name:'代码模块 · '+file.name,type:frontend?'frontend':'backend',evidence:[{file:file.name,line:1}],x:0,y:0};nodes.push(node);byFile.set(file.name,node);parsed.push({file,tree,node});
 }catch(error){warnings.push(file.name+':'+(error.loc?.line||1)+'：语法解析失败')}}
 for(const {file,tree,node}of parsed){
  walk(tree,item=>{
   if(item.type==='ImportDeclaration'&&item.source.value.startsWith('.')){
    const expected=basename(item.source.value),matches=[...byFile.values()].filter(n=>basename(n.evidence[0].file)===expected);
    if(matches.length===1)edge(node.id,matches[0].id,'导入模块','进程内','不适用',evidence(file.name,item));else warnings.push(file.name+':'+item.loc.start.line+'：本地导入 '+item.source.value+' 未唯一解析');
   }
   if(item.type!=='CallExpression')return;const call=path(item.callee);
   if(/\.(listen)$/.test(call)&&typeof literal(item.arguments[0])==='number'){node.sub='监听端口 · :'+literal(item.arguments[0]);node.listen={protocol:'待确认',port:String(literal(item.arguments[0])),evidence:evidence(file.name,item)}}
   if(!(/(^fetch$|^(axios|https?|request)\.(get|post|put|delete|patch|request)$)/.test(call)))return;
   const address=literal(item.arguments[0]);if(typeof address!=='string'||!/^https?:\/\//.test(address))return;
   try{const url=new URL(address),port=/^https?:\/\/[^/]+:(\d+)/.exec(address)?.[1]||'',id='remote:'+url.host;let remote=nodes.find(n=>n.id===id);if(!remote){remote={id,name:url.hostname,sub:url.host,type:'external',x:0,y:0,evidence:[evidence(file.name,item)]};nodes.push(remote)}edge(node.id,id,call+' '+url.pathname,url.protocol.slice(0,-1).toUpperCase(),port,evidence(file.name,item))}catch{warnings.push(file.name+':'+item.loc.start.line+'：URL 无效')}
  });
 }
 if(!nodes.length)throw Error('没有可解析的 JavaScript / TypeScript 模块');
 return{title:'源码架构',nodes,edges,provenance:{analyzer:'Babel AST',files:files.map(f=>f.name),verified:false,scope:'模块导入、JSX 界面、明确 HTTP 请求与监听端口；动态依赖及模块内对象关系待核对',warnings}};
};

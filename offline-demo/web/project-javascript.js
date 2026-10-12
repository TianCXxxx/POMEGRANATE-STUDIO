/* Project-aware JS/TS/Vue/HTML facts. All parsing stays in this browser. */
window.analyzeProjectJavascript=function(files){
 const nodes=[],edges=[],warnings=[],coverage=[],records=new Map(),requests=[],seen=new Set();
 const norm=s=>{const p=[];for(const x of s.replaceAll('\\','/').split('/')){if(x==='..')p.pop();else if(x&&x!=='.')p.push(x)}return p.join('/')},dir=s=>s.slice(0,Math.max(0,s.lastIndexOf('/')));
 const walk=(n,fn)=>{if(!n||typeof n!=='object')return;if(n.type)fn(n);for(const [k,v]of Object.entries(n))if(!['loc','start','end','extra','comments','tokens'].includes(k)){if(Array.isArray(v))v.forEach(x=>walk(x,fn));else if(v&&typeof v==='object')walk(v,fn)}};
 const dotted=n=>n?.type==='ThisExpression'?'this':n?.type==='MetaProperty'?n.meta.name+'.'+n.property.name:n?.type==='Identifier'?n.name:n?.type==='MemberExpression'?dotted(n.object)+'.'+(n.property.name??n.property.value):'';
 const ev=(r,n)=>({file:r.file.name,line:n.loc?.start.line||1,quote:r.file.text.split('\n').slice((n.loc?.start.line||1)-1,n.loc?.end.line||n.loc?.start.line||1).join('\n').slice(0,300)});
 function edge(source,target,label,protocol,port,evidence){const key=JSON.stringify([source,target,label,protocol,port]);if(source===target||seen.has(key))return;seen.add(key);edges.push({id:'js-edge-'+edges.length,source,target,label,protocol,port,style:'solid',evidence,confidence:'confirmed'})}
 const env=new Map();for(const f of files.filter(f=>f.name.split('/').at(-1).startsWith('.env')))f.text.split('\n').forEach((line,i)=>{const m=/^\s*(?:export\s+)?([A-Za-z_]\w*)\s*=\s*(.*?)\s*$/.exec(line);if(m){const entries=env.get(m[1])||[];entries.push({value:m[2].replace(/^['"]|['"]$/g,''),evidence:{file:f.name,line:i+1,quote:line}});env.set(m[1],entries)}});
 const aliases=[];for(const f of files.filter(f=>/(tsconfig|jsconfig).*\.json$/.test(f.name))){try{const config=JSON.parse(f.text.replace(/\/\*[\s\S]*?\*\//g,'').replace(/^\s*\/\/.*$/gm,''));for(const [key,values]of Object.entries(config.compilerOptions?.paths||{}))for(const value of values)aliases.push([key.replace(/\*$/,''),norm(dir(f.name)+'/'+(config.compilerOptions.baseUrl||'.')+'/'+value.replace(/\*$/,''))]);}catch{warnings.push(f.name+'：路径别名配置未能完整解析')}}
 function resolve(r,imported){const paths=[],matches=[];if(imported.startsWith('.'))paths.push(norm(dir(r.file.name)+'/'+imported));else for(const [prefix,target]of aliases)if(imported.startsWith(prefix))paths.push(norm(target+'/'+imported.slice(prefix.length)));for(const p of paths)for(const ext of ['','.ts','.tsx','.js','.jsx','.mjs','.vue','/index.ts','/index.tsx','/index.js'])if(records.has(p+ext))matches.push(p+ext);return [...new Set(matches)]}
 for(const file of files){if(!/\.(tsx?|jsx?|mjs|cjs|vue|html?)$/i.test(file.name))continue;const name=norm(file.name);let text=file.text,frontend=/\.(vue|html?)$/i.test(name);if(frontend)text=[...text.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]).join('\n');
  try{const tree=BabelParser.parse(text,{sourceType:'unambiguous',plugins:['typescript','jsx','decorators-legacy']});walk(tree,n=>{if(n.type==='JSXElement'||n.type==='JSXFragment')frontend=true});const node={id:'module:'+name,name:name.split('/').at(-1).replace(/\.[^.]+$/,''),sub:frontend?'前端界面':'代码模块',type:frontend?'frontend':'backend',x:0,y:0,evidence:[{file:name,line:1}],confidence:'confirmed',routes:[]};const r={file:{...file,name},tree,node,values:{},bindings:{},imports:[]};records.set(name,r);nodes.push(node);coverage.push({file:name,status:'analyzed',method:'Babel AST'});if(/\.(vue|html?)$/.test(name))warnings.push(name+'：脚本块内行号；模板事件依赖需核对');
  }catch(error){warnings.push(name+':'+(error.loc?.line||1)+'：语法解析失败');coverage.push({file:name,status:'failed',reason:'语法错误'})}
 }
 function value(n,r,depth=0){if(depth>10)return;if(n?.type==='StringLiteral'||n?.type==='NumericLiteral')return n.value;if(n?.type==='Identifier')return r.values[n.name];if(n?.type==='MemberExpression'&&/^process\.env\.|^import\.meta\.env\./.test(dotted(n))){const values=env.get(n.property.name)||[];if(values.length>1&&!warnings.includes(r.file.name+'：环境配置有多个值，未选择运行环境'))warnings.push(r.file.name+'：环境配置有多个值，未选择运行环境');if(values.length===1){r.configEvidence=r.configEvidence||[];r.configEvidence.push(values[0].evidence);return values[0].value}return undefined;}if(n?.type==='TemplateLiteral'){let s='';for(let i=0;i<n.quasis.length;i++){s+=n.quasis[i].value.cooked;if(i<n.expressions.length)s+=value(n.expressions[i],r,depth+1)??'{dynamic}'}return s}if(n?.type==='BinaryExpression'&&n.operator==='+'){const a=value(n.left,r,depth+1),b=value(n.right,r,depth+1);if(typeof a==='string')return a+(b??'{dynamic}')}if(n?.type==='LogicalExpression')return value(n.left,r,depth+1)??value(n.right,r,depth+1)}
 for(const r of records.values())walk(r.tree,n=>{if(n.type==='ImportDeclaration'){const candidates=resolve(r,n.source.value);r.imports.push({item:n,candidates});for(const s of n.specifiers)r.bindings[s.local.name]={path:n.source.value,exported:s.imported?.name||'default',resolved:candidates[0],typeOnly:n.importKind==='type'||s.importKind==='type'}}});
 for(let pass=0;pass<4;pass++)for(const r of records.values()){for(const [name,b]of Object.entries(r.bindings)){const target=records.get(b.resolved);if(target&&target.values[b.exported]!==undefined)r.values[name]=target.values[b.exported]}walk(r.tree,n=>{if(n.type==='VariableDeclarator'&&n.id.type==='Identifier'){const v=value(n.init,r);if(v!==undefined)r.values[n.id.name]=v}})}
 const boundNames=(n,set)=>{if(!n)return;if(n.type==='Identifier')set.add(n.name);else if(n.type==='TSParameterProperty')boundNames(n.parameter,set);else if(n.type==='AssignmentPattern')boundNames(n.left,set);else if(n.type==='RestElement')boundNames(n.argument,set);else if(n.type==='ObjectPattern')n.properties.forEach(p=>boundNames(p.value||p.argument,set));else if(n.type==='ArrayPattern')n.elements.forEach(p=>boundNames(p,set));};
 for(const r of records.values()){
  r.shadowed=new WeakMap();
  const index=(node,inherited)=>{if(!node||typeof node!=='object')return;let scope=inherited;if(/Function|Method/.test(node.type||'')&&Array.isArray(node.params)){scope=new Set(inherited);node.params.forEach(p=>boundNames(p,scope));if(node.id)boundNames(node.id,scope);}if(node.type==='BlockStatement'){scope=new Set(scope);for(const statement of node.body){if(statement.type==='VariableDeclaration')statement.declarations.forEach(d=>boundNames(d.id,scope));if(['FunctionDeclaration','ClassDeclaration'].includes(statement.type))boundNames(statement.id,scope);}}if(node.type)r.shadowed.set(node,scope);for(const [key,value]of Object.entries(node))if(!['loc','start','end','extra','comments','tokens'].includes(key)){if(Array.isArray(value))value.forEach(n=>index(n,scope));else if(value&&typeof value==='object')index(value,scope);}};
  index(r.tree,new Set());
 }
 for(const r of records.values()){
  for(const {item,candidates}of r.imports){if(candidates.length===1)edge(r.node.id,records.get(candidates[0]).node.id,(item.importKind==='type'||item.specifiers.length>0&&item.specifiers.every(s=>s.importKind==='type'))?'类型依赖':'导入模块',(item.importKind==='type'||item.specifiers.length>0&&item.specifiers.every(s=>s.importKind==='type'))?'类型引用':'进程内','不适用',[ev(r,item)]);else if(item.source.value.startsWith('.')||item.source.value.startsWith('@/'))warnings.push(r.file.name+':'+item.loc.start.line+'：未解析导入 '+item.source.value)}
  walk(r.tree,item=>{if(!['CallExpression','NewExpression'].includes(item.type))return;const call=dotted(item.callee),tail=call.split('.').at(-1),first=value(item.arguments[0],r),root=call.split('.')[0],called=r.bindings[root];
   if(called?.resolved&&!called.typeOnly&&!r.shadowed.get(item)?.has(root)&&records.has(called.resolved))edge(r.node.id,records.get(called.resolved).node.id,call+'()','进程内','不适用',[ev(r,item)]);
   if(item.type==='NewExpression')return;
   if(tail==='listen'&&typeof first==='number'){const http=Object.values(r.bindings).some(b=>['express','http','https','node:http','node:https','fastify'].includes(b.path));r.node.listen={protocol:http?'HTTP':'',port:String(first),evidence:ev(r,item)};r.node.sub='接口服务 · :'+first}
   if(['get','post','put','delete','patch'].includes(tail)&&typeof first==='string'&&first.startsWith('/')&&['app','router','server'].includes(root)){r.node.routes.push({method:tail.toUpperCase(),path:first,evidence:ev(r,item)});r.node.sub='API 路由'}
   const b=r.bindings[root],client=call==='fetch'||['axios','http','https','request'].includes(root)||['axios','node:http','node:https','http','https'].includes(b?.path);
   if(!client||!['fetch','get','post','put','delete','patch','request'].includes(tail))return;if(typeof first!=='string'){warnings.push(r.file.name+':'+item.loc.start.line+'：请求地址无法静态求值');return}
   let method=tail==='fetch'?'GET':tail.toUpperCase();const opts=item.arguments[1];if(opts?.type==='ObjectExpression'){const m=opts.properties.find(p=>(p.key?.name||p.key?.value)==='method');if(m)method=String(value(m.value,r)||method).toUpperCase()}
   requests.push({source:r.node.id,url:first,method,evidence:ev(r,item)});
  });
 }
 // NestJS / GraphQL / TypeORM declarations are anchored to imported symbols.
 for(const r of records.values()){
  const typedFields=new Map();
  walk(r.tree,item=>{
   if(item.type!=='ClassDeclaration')return;
   for(const decorator of item.decorators||[]){const expression=decorator.expression,callee=expression.type==='CallExpression'?expression.callee:expression,b=r.bindings[dotted(callee)];
    if(b?.path==='typeorm'&&['Entity','ChildEntity','ViewEntity'].includes(b.exported))r.node.declarationKind='data';
    if(b?.path==='@nestjs/graphql'&&b.exported==='Resolver'){r.node.sub='GraphQL 入口';r.node.routes.push({method:'GRAPHQL',path:'GraphQL',evidence:ev(r,decorator)});}
    if(b?.path==='@nestjs/common'&&b.exported==='Injectable')r.node.sub='业务服务';
   }
   for(const fn of item.body.body)if(fn.kind==='constructor')for(let arg of fn.params||[]){if(arg.type==='TSParameterProperty')arg=arg.parameter;const name=arg.typeAnnotation?.typeAnnotation?.typeName?.name;if(name)typedFields.set(arg.name,name);}
  });
  walk(r.tree,item=>{
   if(item.type!=='CallExpression')return;const call=dotted(item.callee),tail=call.split('.').at(-1),args=item.arguments;
   const receiver=call.split('.'),receiverType=receiver[0]==='this'?typedFields.get(receiver[1]):null,provider=r.bindings[receiverType];let repositoryProvider=provider?.path==='typeorm';
   if(tail==='getRepository'&&provider?.resolved){const declaration=records.get(provider.resolved);if(declaration)walk(declaration.tree,n=>{if(n.type==='ClassMethod'&&n.key?.name==='getRepository')repositoryProvider=true;});}
   if(tail==='getRepository'&&repositoryProvider){
    const arg=args.at(-1),b=r.bindings[arg?.name];if(b?.resolved&&records.has(b.resolved))edge(r.node.id,records.get(b.resolved).node.id,'ORM 实体访问','进程内','不适用',[ev(r,item)]);
   }
   const parts=call.split('.'),type=parts[0]==='this'?typedFields.get(parts[1]):null;
   if(r.bindings[type]?.exported!=='EventBus'||!['publish','ofType'].includes(tail)||!args.length)return;
   const symbol=args[0].type==='NewExpression'?dotted(args[0].callee):dotted(args[0]),binding=r.bindings[symbol];if(!binding)return;
   const bus=r.bindings[type],eventId=bus?.resolved&&records.get(bus.resolved)?.node.id;
   if(eventId){
    const source=tail==='publish'?r.node.id:eventId,target=tail==='publish'?eventId:r.node.id,label=tail==='publish'?'发布进程内事件':'筛选事件类型';
    edge(source,target,label,'进程内','不适用',[ev(r,item)]);
    const relation=edges.find(e=>e.source===source&&e.target===target&&e.label===label);
    if(relation){relation.eventTypes=[...new Set([...(relation.eventTypes||[]),symbol])];if(tail!=='publish'){relation.confidence='inferred';relation.style='dashed';}}
    return;
   }
   const unresolvedEventId='event:'+norm(dir(r.file.name)+'/'+binding.path)+':'+binding.exported;
   if(!nodes.some(n=>n.id===unresolvedEventId))nodes.push({id:unresolvedEventId,name:symbol,sub:'进程内事件 · EventBus 实现未上传',type:'messagebus',x:0,y:0,evidence:[ev(r,item)],confidence:'inferred'});
   if(tail==='publish')edge(r.node.id,unresolvedEventId,'发布事件','进程内','不适用',[ev(r,item)]);else edge(unresolvedEventId,r.node.id,'筛选事件类型','进程内','不适用',[ev(r,item)]);
  });
 }
 // Framework relations remain bound to actual imports and literal addresses.
 for(const r of records.values()){
  const instances=new Map();
  const binding=n=>r.bindings[dotted(n).split('.')[0]];
  walk(r.tree,item=>{
   if(item.type==='ClassDeclaration')for(const field of item.body.body){if(field.type!=='ClassMethod'&&field.type!=='TSDeclareMethod')continue;for(let arg of field.params||[]){if(arg.type==='TSParameterProperty')arg=arg.parameter;const annotation=arg.typeAnnotation?.typeAnnotation;const name=annotation?.type==='TSTypeReference'?dotted(annotation.typeName):'';const b=r.bindings[name];if(b?.resolved&&records.has(b.resolved)){edge(r.node.id,records.get(b.resolved).node.id,'声明注入依赖','进程内','不适用',[ev(r,arg)]);const added=edges.at(-1);if(added?.label==='声明注入依赖'){added.style='dashed';added.confidence='inferred';}}}}
   if(item.type!=='VariableDeclarator'||item.id.type!=='Identifier'||!['NewExpression','CallExpression'].includes(item.init?.type))return;
   const init=item.init,b=binding(init.callee),pkg=b?.path;
   if(!['sequelize','pg','mysql2','ioredis','redis','mongoose'].includes(pkg))return;
   let address=value(init.arguments[0],r);if(init.arguments[0]?.type==='ObjectExpression'){const prop=init.arguments[0].properties.find(p=>['url','connectionString'].includes(p.key?.name||p.key?.value));if(prop)address=value(prop.value,r);}
   if(typeof address!=='string'){warnings.push(r.file.name+':'+item.loc.start.line+'：数据库或消息连接配置无法静态确认');return;}
   try{const url=new URL(address);if(!['postgres:','postgresql:','mysql:','redis:','rediss:','mongodb:','mongodb+srv:'].includes(url.protocol))return;const type=['redis:','rediss:'].includes(url.protocol)?'messagebus':'database',id=type+':'+url.protocol+url.host+url.pathname,evidence=[ev(r,item),...(r.configEvidence||[])];if(!nodes.some(n=>n.id===id))nodes.push({id,name:url.protocol.slice(0,-1).toUpperCase(),sub:url.host+url.pathname,type,x:0,y:0,evidence,confidence:'confirmed'});instances.set(item.id.name,id);edge(r.node.id,id,'连接',url.protocol.slice(0,-1).toUpperCase(),url.port,evidence);}catch{warnings.push(r.file.name+':'+item.loc.start.line+'：无效连接地址');}
  });
  walk(r.tree,item=>{if(item.type!=='CallExpression'||item.callee.type!=='MemberExpression')return;const base=dotted(item.callee.object),method=item.callee.property.name,id=instances.get(base);if(!id||!['publish','subscribe','psubscribe'].includes(method))return;const topic=value(item.arguments[0],r);if(typeof topic!=='string'){warnings.push(r.file.name+':'+item.loc.start.line+'：消息主题动态生成');return;}const channel=id+':topic:'+topic;if(!nodes.some(n=>n.id===channel))nodes.push({id:channel,name:topic,sub:'消息主题',type:'messagebus',x:0,y:0,evidence:[ev(r,item)],confidence:'confirmed'});if(method==='publish')edge(r.node.id,channel,'发布','消息','',[ev(r,item)]);else edge(channel,r.node.id,'订阅','消息','',[ev(r,item)]);});
 }
 // Attribute browser helper modules to their frontend entry, unless they expose a
 // server listener/route. This avoids depicting a browser API client as a backend.
 for(let pass=0;pass<records.size;pass++){let changed=false;for(const r of records.values())if(r.node.type==='frontend')for(const imp of r.imports){const child=records.get(imp.candidates[0]);if(imp.candidates.length===1&&child&&child.node.type!=='frontend'&&!child.node.listen&&!child.node.routes.length){child.node.type='frontend';child.node.sub=requests.some(q=>q.source===child.node.id)?'前端请求模块':'前端依赖模块';changed=true;}}if(!changed)break;}
 for(const r of requests){if(!/^https?:\/\//.test(r.url)){if(!r.url.startsWith('/'))warnings.push(r.evidence.file+':'+r.evidence.line+'：请求地址待确认');continue}try{const url=new URL(r.url),port=/^https?:\/\/[^/]+:(\d+)/.exec(r.url)?.[1]||'',id='remote:'+url.protocol+'//'+url.host;if(!nodes.some(n=>n.id===id))nodes.push({id,name:url.host,sub:'外部 HTTP 接口',type:'external',x:0,y:0,evidence:[r.evidence],confidence:'confirmed',address:url.host});edge(r.source,id,r.method+' '+url.pathname,url.protocol.slice(0,-1).toUpperCase(),port,[r.evidence])}catch{warnings.push(r.evidence.file+':'+r.evidence.line+'：URL 无效')}}
 return{title:'项目架构',nodes,edges,requests,coverage,provenance:{analyzer:'Babel AST',files:[...records.keys()],warnings,verified:false}};
};

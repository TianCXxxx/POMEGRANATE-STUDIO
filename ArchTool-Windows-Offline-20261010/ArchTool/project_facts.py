"""Cross-file Python facts and cross-language HTTP reconciliation."""
import ast
import pathlib
import re
from urllib.parse import urlsplit


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return dotted(n.value) + '.' + n.attr
    return ''


def python_facts(files):
    records, symbols, nodes, edges, warnings, coverage, requests = {}, {}, {}, {}, [], [], []
    def ev(record, item):
        return {'file': record['name'], 'line': item.lineno, 'quote': '\n'.join(record['text'].splitlines()[item.lineno-1:getattr(item, 'end_lineno', item.lineno)])[:300]}
    for file in files:
        if not file['name'].lower().endswith('.py'):
            continue
        try:
            tree = ast.parse(file['text'], filename=file['name'])
        except SyntaxError as error:
            warnings.append(f"{file['name']}:{error.lineno}：语法错误，未分析")
            coverage.append({'file': file['name'], 'status': 'failed', 'reason': '语法错误'})
            continue
        r = dict(file, tree=tree, imports={}, values={}, attrs={}, classes={})
        records[file['name']] = r
        coverage.append({'file': file['name'], 'status': 'analyzed', 'method': 'Python AST'})
        functions = [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [x for x in tree.body if isinstance(x, ast.ClassDef)]
        # Keep utility functions within a class-containing module unless they expose routes.
        meaningful = [x for x in tree.body if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant))]
        module_needed = (not classes and bool(meaningful)) or any(f.decorator_list for f in functions)
        if module_needed:
            key = 'py:' + file['name']
            nodes[key] = dict(id=key, name=pathlib.PurePosixPath(file['name']).stem, sub='Python 模块', type='backend', x=0, y=0, evidence=[{'file':file['name'],'line':1}], confidence='confirmed', routes=[])
            r['module'] = key
        for item in classes:
            key = file['name'] + '::' + item.name
            symbols[(file['name'], item.name)] = key
            r['classes'][item.name] = key
            role = '数据访问层' if 'Repository' in item.name else '业务服务' if 'Service' in item.name else '出站适配器' if re.search('Client|Gateway|Integration|Adapter', item.name) else '代码组件'
            nodes[key] = dict(id=key,name=item.name,sub=role,type='backend',x=0,y=0,evidence=[ev(r,item)],confidence='confirmed',routes=[])
        for item in functions:
            if module_needed:
                symbols[(file['name'], item.name)] = r['module']
        for item in tree.body:
            if isinstance(item, ast.Import):
                for alias in item.names:
                    r['imports'][alias.asname or alias.name.split('.')[0]] = (alias.name, None, 0)
            if isinstance(item, ast.ImportFrom):
                for alias in item.names:
                    r['imports'][alias.asname or alias.name] = (item.module or '', alias.name, item.level)

    def import_file(r, module, level):
        parts = list(pathlib.PurePosixPath(r['name']).parts[:-1])
        if level:
            parts = parts[:len(parts)-level+1]
        else:
            parts = []
        base = '/'.join(parts + module.split('.'))
        candidates = [base+'.py', base+'/__init__.py']
        found = [p for p in candidates if p in records]
        if not found and not level:
            found = [p for p in records if p.endswith('/'+base+'.py')]
        return found[0] if len(found)==1 else None

    def resolve(r, name):
        if (r['name'], name) in symbols:
            return symbols[(r['name'], name)]
        first, _, rest = name.partition('.')
        if first in r['imports']:
            module, imported, level = r['imports'][first]
            file = import_file(r, module, level)
            return symbols.get((file, imported or rest))

    def literal(n, values):
        if isinstance(n, ast.Constant) and isinstance(n.value, (str,int)):
            return n.value
        if isinstance(n,(ast.Name,ast.Attribute)):
            return values.get(dotted(n))
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add):
            a,b=literal(n.left,values),literal(n.right,values)
            if isinstance(a,str):
                return a+(str(b) if b is not None else '{dynamic}')
        if isinstance(n,ast.JoinedStr):
            return ''.join(str(literal(x,values)) if isinstance(x,ast.Constant) else str(literal(x.value,values) or '{dynamic}') for x in n.values)
        if isinstance(n,ast.Call) and dotted(n.func) in ('os.getenv','os.environ.get') and len(n.args)>1:
            return literal(n.args[1],values)

    def add_edge(source,target,label,protocol,port,evidence,confidence='confirmed'):
        if source==target or source not in nodes or target not in nodes:
            return
        key=(source,target,protocol,port)
        if key not in edges:
            edges[key]=dict(id='py-edge-'+str(len(edges)),source=source,target=target,label=label,protocol=protocol,port=port,style='solid',evidence=[evidence],confidence=confidence)
        else:
            edge=edges[key]
            if label not in edge['label'].split(' / '):
                edge['label']+=' / '+label
            if evidence not in edge['evidence']:
                edge['evidence'].append(evidence)

    class_attrs = {key:{} for key in symbols.values()}
    for r in records.values():
        for item in r['tree'].body:
            if isinstance(item,ast.Assign):
                for target in item.targets:
                    val=literal(item.value,r['values'])
                    if val is not None:
                        r['values'][dotted(target)]=val
        for cls in [x for x in r['tree'].body if isinstance(x,ast.ClassDef)]:
            key=r['classes'][cls.name]
            for item in ast.walk(cls):
                if isinstance(item,ast.Assign) and isinstance(item.value,ast.Call):
                    target_type=resolve(r,dotted(item.value.func))
                    if target_type:
                        for target in item.targets:
                            class_attrs[key][dotted(target).removeprefix('self.')]=target_type
        for item in ast.walk(r['tree']):
            if isinstance(item,ast.Assign) and isinstance(item.value,ast.Call):
                target_type=resolve(r,dotted(item.value.func))
                for target in item.targets:
                    parts=dotted(target).split('.')
                    owner=resolve(r,parts[0])
                    if len(parts)==2 and owner and target_type:
                        class_attrs[owner][parts[1]]=target_type

    # Annotated constructor injection is a declared dependency, not proof of
    # the runtime container binding. Retain this distinction in the evidence.
    injected = {}
    for r in records.values():
        for cls in [x for x in r['tree'].body if isinstance(x, ast.ClassDef)]:
            owner = r['classes'][cls.name]
            for fn in cls.body:
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                typed = {a.arg: resolve(r, dotted(a.annotation)) for a in fn.args.args if a.annotation}
                for item in ast.walk(fn):
                    if isinstance(item, ast.Assign) and isinstance(item.value, ast.Name) and typed.get(item.value.id):
                        for target in item.targets:
                            name = dotted(target)
                            if name.startswith('self.'):
                                class_attrs[owner][name[5:]] = typed[item.value.id]
                                injected[(owner, name[5:])] = ev(r, item)
                                add_edge(owner, typed[item.value.id], '声明注入依赖', '进程内', '不适用', ev(r, item), 'inferred')
    for edge in edges.values():
        if edge['confidence'] == 'inferred':
            edge['style'] = 'dashed'

    for r in records.values():
        owners=[]
        for item in r['tree'].body:
            if isinstance(item,ast.ClassDef):
                owners.append((r['classes'][item.name],item))
            elif isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)) and r.get('module'):
                owners.append((r['module'],item))
        for owner,scope in owners:
            values=dict(r['values'])
            for fn in ast.walk(scope):
                if isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    for arg,default in zip(fn.args.args[-len(fn.args.defaults):],fn.args.defaults):
                        val=literal(default,values)
                        if val is not None:
                            values[arg.arg]=val
                    for dec in fn.decorator_list:
                        if isinstance(dec,ast.Call) and dec.args:
                            route=literal(dec.args[0],values)
                            method=dotted(dec.func).split('.')[-1].upper()
                            if isinstance(route,str) and route.startswith('/') and method in ('GET','POST','PUT','DELETE','PATCH'):
                                nodes[owner]['routes'].append({'path':route,'method':method,'evidence':ev(r,dec)})
            for _ in range(3):
                for item in ast.walk(scope):
                    if isinstance(item,ast.Assign):
                        val=literal(item.value,values)
                        if val is not None:
                            for target in item.targets:
                                values[dotted(target)]=val
            for item in ast.walk(scope):
                if not isinstance(item,ast.Call):
                    continue
                call=dotted(item.func);parts=call.split('.');evidence=ev(r,item)
                target=resolve(r,call)
                if parts[0]=='self' and len(parts)>=3:
                    target=owner
                    for attr in parts[1:-1]:
                        target=class_attrs.get(target,{}).get(attr)
                if target:
                    inferred = parts[0]=='self' and len(parts)>=3 and (owner,parts[1]) in injected
                    add_edge(owner,target,parts[-1]+'()','进程内','不适用',evidence,'inferred' if inferred else 'confirmed')
                    if inferred:
                        edges[(owner,target,'进程内','不适用')]['style']='dashed'
                if isinstance(item.func,ast.Call) and dotted(item.func.func)=='getattr' and len(item.func.args)>=2:
                    obj,method=item.func.args[:2]
                    reflected=class_attrs.get(owner,{}).get(dotted(obj).removeprefix('self.'))
                    if reflected and isinstance(method,ast.Constant) and isinstance(method.value,str):
                        add_edge(owner,reflected,'反射调用 '+method.value,'进程内','不适用',evidence,'inferred')
                        edges[(owner,reflected,'进程内','不适用')]['style']='dashed'
                    else:
                        warnings.append(r['name']+':'+str(item.lineno)+'：反射目标或方法名无法静态确认')
                if call=='sqlite3.connect':
                    filename=literal(item.args[0],values) if item.args else None
                    key='sqlite:'+str(filename or r['name'])
                    nodes.setdefault(key,dict(id=key,name='SQLite',sub=str(filename or '路径待确认'),type='database',x=0,y=0,evidence=[evidence],confidence='confirmed'))
                    add_edge(owner,key,'读写本地文件','SQLite 文件','不适用',evidence)
                helper=next((f for f in r['tree'].body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.name==call),None)
                is_helper=helper is not None and any(isinstance(c,ast.Call) and dotted(c.func) in ('Request','urlopen','urllib.request.urlopen') for c in ast.walk(helper))
                known=call.startswith(('requests.','httpx.')) or call in ('Request','urlopen','urllib.request.Request','urllib.request.urlopen') or is_helper
                if not known or not item.args:
                    continue
                address=literal(item.args[0],values)
                if not isinstance(address,str) or not address.startswith(('http://','https://')):
                    warnings.append(f"{r['name']}:{item.lineno}：HTTP 地址无法静态求值")
                    continue
                try:
                    url=urlsplit(address);port=str(url.port or '')
                except ValueError:
                    warnings.append(f"{r['name']}:{item.lineno}：HTTP 地址无效")
                    continue
                key='remote:'+url.scheme+'://'+url.netloc
                nodes.setdefault(key,dict(id=key,name=url.hostname or '外部接口',sub=url.netloc,type='external',x=0,y=0,evidence=[evidence],confidence='confirmed'))
                method=parts[-1].upper() if parts[-1].lower() in ('post','get','put','patch','delete') else 'HTTP'
                add_edge(owner,key,method+' '+url.path,url.scheme.upper(),port,evidence)
                requests.append({'source':owner,'url':address,'method':method,'evidence':evidence})
        for item in ast.walk(r['tree']):
            if not isinstance(item,ast.Call):
                continue
            call=dotted(item.func)
            if call.endswith('HTTPServer') and len(item.args)>=2 and isinstance(item.args[0],(ast.Tuple,ast.List)):
                owner=resolve(r,dotted(item.args[1]));address=item.args[0].elts
                if owner and len(address)==2:
                    port=literal(address[1],r['values'])
                    if isinstance(port,int):
                        nodes[owner]['listen']={'protocol':'HTTP','port':str(port),'evidence':ev(r,item)}
                        nodes[owner]['sub']='HTTP 接口 · :'+str(port)
            if call in ('uvicorn.run','app.run') and r.get('module'):
                kw={k.arg:literal(k.value,r['values']) for k in item.keywords}
                if isinstance(kw.get('port'),int):
                    nodes[r['module']]['listen']={'protocol':'HTTP','port':str(kw['port']),'evidence':ev(r,item)}
        # Module imports establish dependencies for function-based projects.
        if r.get('module'):
            for item in r['tree'].body:
                if isinstance(item,ast.ImportFrom):
                    for alias in item.names:
                        target=resolve(r,alias.asname or alias.name)
                        if target:
                            add_edge(r['module'],target,'导入模块','进程内','不适用',ev(r,item))
    return {'nodes':list(nodes.values()),'edges':list(edges.values()),'requests':requests,'coverage':coverage,'warnings':warnings}


def combine_facts(py, js):
    nodes={n['id']:n for n in py['nodes']+js.get('nodes',[])}
    edges=py['edges']+js.get('edges',[])
    warnings=py['warnings']+js.get('provenance',{}).get('warnings',[])
    listeners=[n for n in nodes.values() if n.get('listen')]
    for edge in edges:
        target=nodes.get(edge['target'],{})
        if target.get('type')=='external' and edge.get('port'):
            candidates=[n for n in listeners if n['listen']['port']==edge['port']]
            # Port matching is only unambiguous for explicit loopback URLs in this project.
            if len(candidates)==1 and re.fullmatch(r'(?:localhost|127\.0\.0\.1)(?::\d+)?',target.get('address', target.get('sub',''))):
                edge['target']=candidates[0]['id'];edge['evidence'].append(candidates[0]['listen']['evidence'])
    for request in py['requests']+js.get('requests',[]):
        if not request['url'].startswith('/'):
            continue
        candidates=[n for n in nodes.values() if any(r['path']==request['url'] and r['method']==request['method'] for r in n.get('routes',[]))]
        if len(candidates)==1:
            target=candidates[0];listen=target.get('listen',{})
            edges.append(dict(id='relative-'+str(len(edges)),source=request['source'],target=target['id'],label=request['method']+' '+request['url']+'（路由匹配）',protocol=listen.get('protocol',''),port=listen.get('port',''),style='dashed',confidence='inferred',evidence=[request['evidence']]+[r['evidence'] for r in target['routes'] if r['path']==request['url']]))
            warnings.append(request['evidence']['file']+'：相对 URL 按同名路由关联，代理与部署地址待确认')
        else:
            warnings.append(request['evidence']['file']+'：相对请求 '+request['url']+' 未找到唯一目标，需提供路由/代理配置')
    used={e[k] for e in edges for k in ('source','target')}
    nodes={k:v for k,v in nodes.items() if v['type']!='external' or k in used}
    unique={}
    for edge in edges:
        key=(edge['source'],edge['target'],edge['label'],edge.get('protocol',''),edge.get('port',''))
        if key not in unique:
            edge['id']='edge-'+str(len(unique));unique[key]=edge
    return {'title':'项目架构','nodes':list(nodes.values()),'edges':list(unique.values()),'warnings':warnings,'coverage':py['coverage']+js.get('coverage',[])}

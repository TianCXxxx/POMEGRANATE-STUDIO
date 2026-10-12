"""Framework declarations from AST, without importing any uploaded program."""
import ast,re
from project_facts import dotted

def enrich_frameworks(files,result):
    nodes={n['id']:n for n in result['nodes']};records={};env={}
    for f in files:
        if f['name'].split('/')[-1].startswith('.env'):
            for i,line in enumerate(f['text'].splitlines(),1):
                m=re.match(r'([A-Za-z_]\w*)=(.*)',line)
                if m:env.setdefault(m[1],[]).append((m[2].strip(chr(34)+chr(39)),{'file':f['name'],'line':i,'quote':line}))
        if f['name'].endswith('.py'):
            source=re.sub(r'(?m)^(\s*except) ([A-Za-z_][\w.]*(?:,\s*[A-Za-z_][\w.]*)+)(?=\s*(?:as \w+)?\s*:)',r'\1 (\2)',f['text'])
            try:records[f['name']]=(f,ast.parse(source))
            except SyntaxError:pass
    def evidence(f,item):return {'file':f['name'],'line':item.lineno,'quote':'\n'.join(f['text'].splitlines()[item.lineno-1:getattr(item,'end_lineno',item.lineno)])[:600]}
    def module(name):
        key='py:'+name
        if key in nodes:return key
    seen={(e['source'],e['target'],e['label'],e.get('protocol',''),e.get('port','')) for e in result['edges']}
    def connect(a,b,label,ev,inferred=False,protocol='进程内',port='不适用'):
        key=(a,b,label,protocol,port)
        if key in seen:return
        seen.add(key)
        if a and b and a!=b:result['edges'].append(dict(id='framework-'+str(len(result['edges'])),source=a,target=b,label=label,protocol=protocol,port=port,evidence=ev,style='dashed' if inferred else 'solid',confidence='inferred' if inferred else 'confirmed'))
    for name,(f,tree) in records.items():
        current=module(name);imports={}
        for item in tree.body:
            if isinstance(item,ast.ImportFrom):
                for a in item.names:imports[a.asname or a.name]=(item.module or '',a.name,item.level)
        def imported(name):
            first,_,rest=name.partition('.')
            if first not in imports:return None
            package,alias,level=imports[first]
            if level:
                parts=f['name'].split('/')[:-1];base='/'.join(parts[:len(parts)-level+1]+package.split('.'))
            else:base=package.replace('.','/')
            paths=[base+'/'+alias+'.py',base+'.py']
            candidates=[p for p in records if any(p==x or p.endswith('/'+x) for x in paths)]
            if len(candidates)==1:return module(candidates[0])
        for item in ast.walk(tree):
            if not isinstance(item,ast.Call):continue
            call=dotted(item.func);tail=call.split('.')[-1];ev=[evidence(f,item)]
            binding=imports.get(call)
            if binding:tail=binding[1]
            if tail in ('FastAPI','APIRouter') and binding and binding[0]=='fastapi' and current:
                nodes[current]['sub']='FastAPI 入口' if tail=='FastAPI' else 'API 路由模块'
                nodes[current]['frameworkEntry']=tail=='FastAPI'
            if tail=='include_router' and item.args:
                connect(current,imported(dotted(item.args[0])),'注册路由',ev)
            if tail=='Depends' and binding and binding[0]=='fastapi' and item.args:
                connect(current,imported(dotted(item.args[0])),'声明框架注入',ev,True)
            if tail=='Session' and binding and binding[0] in ('sqlmodel','sqlalchemy.orm') and item.args:
                connect(current,imported(dotted(item.args[0])),'SQLModel 会话使用引擎',ev,True)
            # Annotated aliases imported by route functions identify provider modules.
            if isinstance(item.func,ast.Attribute) and tail in ('exec','get','add','commit') and 'sqlmodel' in f['text']:
                for package,alias,level in imports.values():
                    if alias in ('SessionDep','get_db'):
                        connect(current,imported(alias),'SQLModel 会话依赖',ev,True)
            if tail=='create_engine' and binding and binding[0] in ('sqlmodel','sqlalchemy') and item.args:
                arg=item.args[0]
                if isinstance(arg,ast.Call) and dotted(arg.func)=='str' and arg.args:arg=arg.args[0]
                if dotted(arg).endswith('DATABASE_URL'):
                    choices=env.get('DATABASE_URL',[])
                    if len(choices)==1:
                        value,config=choices[0];m=re.match(r'(postgresql|postgres|mysql)(?:\+[^:]+)?://[^@]*@([^/]+)/(.*)',value)
                        if m:
                            key='configured-db:'+config['file']+':DATABASE_URL';nodes.setdefault(key,dict(id=key,name=m[1].upper(),sub=m[2]+'/'+m[3]+' · 环境配置候选',type='database',evidence=[config],x=0,y=0,confidence='inferred'))
                            port=m[2].rsplit(':',1)[1] if ':' in m[2] else ''
                            connect(current,key,'SQLModel 配置连接',ev+[config],True,m[1].upper(),port)
            if call=='dj_database_url.config':
                key='configured-db:'+name;nodes.setdefault(key,dict(id=key,name='Django 数据库配置',sub='连接地址 / 数据库类型待确认',type='database',evidence=ev,x=0,y=0,confidence='inferred'))
                connect(current,key,'数据库配置声明',ev,True,'','')
            if tail in ('path','re_path') and binding and binding[0]=='django.urls' and current and item.args and isinstance(item.args[0],ast.Constant) and isinstance(item.args[0].value,str):
                nodes[current].setdefault('routes',[]).append({'path':item.args[0].value,'method':'ANY','evidence':ev[0]});nodes[current]['sub']='Django URL 入口'
            if tail=='Celery' and binding and binding[0]=='celery' and current:
                nodes[current]['sub']='Celery 任务应用';nodes[current]['frameworkEntry']=True
    result['nodes']=list(nodes.values());return result

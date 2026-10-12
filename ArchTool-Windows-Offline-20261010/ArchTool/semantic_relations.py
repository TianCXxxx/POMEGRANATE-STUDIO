"""Bounded framework connections; source/config evidence only, never execute."""
import ast
import re
from urllib.parse import urlsplit
from project_facts import dotted


def enrich_relations(files, result):
    nodes = {n['id']: n for n in result['nodes']}
    env = {}
    for f in files:
        if f['name'].split('/')[-1].startswith('.env'):
            for line, text in enumerate(f['text'].splitlines(), 1):
                match = re.fullmatch(r"\s*(?:export\s+)?([A-Za-z_]\w*)\s*=\s*(.*?)\s*", text)
                if match:
                    env.setdefault(match[1], []).append((match[2].strip(chr(34)+chr(39)), {'file':f['name'],'line':line,'quote':text}))
    for row in result.get('coverage', []):
        if row['file'].split('/')[-1].startswith('.env'):
            row.update(status='analyzed', method='环境配置键值；部署环境仍需核对')
    for f in files:
        if not f['name'].endswith('.py'):
            continue
        try:
            tree = ast.parse(f['text'])
        except SyntaxError:
            continue
        imports, values, resources = {}, {}, {}
        def ev(item):
            return {'file':f['name'],'line':item.lineno,'quote':'\n'.join(f['text'].splitlines()[item.lineno-1:getattr(item,'end_lineno',item.lineno)])[:500]}
        for item in tree.body:
            if isinstance(item, ast.Import):
                for alias in item.names: imports[alias.asname or alias.name.split('.')[0]]=alias.name
            elif isinstance(item, ast.ImportFrom):
                for alias in item.names: imports[alias.asname or alias.name]=(item.module or '')+'.'+alias.name
        def qualified(name):
            first, _, rest = name.partition('.')
            return imports.get(first,first)+('.'+rest if rest else '')
        def literal(item):
            if isinstance(item, ast.Constant): return item.value, []
            if isinstance(item, ast.Name): return values.get(item.id,(None,[]))
            if isinstance(item, ast.Call) and qualified(dotted(item.func)) in ('os.getenv','os.environ.get') and item.args:
                key,_=literal(item.args[0]); choices=env.get(key,[])
                if len(choices)==1: return choices[0][0],[choices[0][1]]
                if len(choices)>1:
                    result['warnings'].append(f['name']+':'+str(item.lineno)+'：环境变量存在多个配置值，未选择部署环境')
                    return None,[]
                if len(item.args)>1:
                    val,_=literal(item.args[1]); return val,[dict(ev(item),verification='environment-default; runtime-override-possible')]
            return None,[]
        def owner(item):
            candidates=[c for c in tree.body if isinstance(c,ast.ClassDef) and c.lineno<=item.lineno<=c.end_lineno]
            key=f['name']+'::'+candidates[0].name if candidates else 'py:'+f['name']
            return key if key in nodes else None
        def relation(source,target,label,protocol,port,evidence,inferred=False):
            if not source or source==target:return
            result['edges'].append(dict(id='semantic-'+str(len(result['edges'])),source=source,target=target,label=label,protocol=protocol,port=port,evidence=evidence,style='dashed' if inferred else 'solid',confidence='inferred' if inferred else 'confirmed'))
        def resource(item,url,kind,evidence):
            if not isinstance(url,str) or '{' in url:return
            try:
                parsed=urlsplit(url); scheme=parsed.scheme.split('+')[0]; port=str(parsed.port or '')
            except ValueError:return
            allowed={'postgresql','postgres','mysql','sqlite','redis','rediss','amqp','amqps','mongodb','mongodb+srv'}
            if scheme not in allowed:return
            # Never include usernames/passwords in the display or stable identity.
            location=(parsed.hostname or '')+(':'+port if port else '')+parsed.path
            key=kind+':'+scheme+':'+location
            nodes.setdefault(key,dict(id=key,name=scheme.upper(),sub=location,type=kind,x=0,y=0,evidence=evidence,confidence='confirmed'))
            relation(owner(item),key,'ORM 连接' if kind=='database' else '消息连接',scheme.upper(),port,evidence,any(e.get('verification') for e in evidence))
            return key
        for _ in range(3):
            for item in ast.walk(tree):
                if isinstance(item,ast.Assign):
                    val=literal(item.value)
                    if val[0] is not None:
                        for target in item.targets: values[dotted(target)]=val
        for item in ast.walk(tree):
            if not isinstance(item,ast.Call):continue
            name=qualified(dotted(item.func))
            if name in ('sqlalchemy.create_engine','sqlalchemy.ext.asyncio.create_async_engine','redis.from_url','redis.Redis.from_url','pymongo.MongoClient','pika.URLParameters') and item.args:
                url,config=literal(item.args[0]); kind='messagebus' if name.startswith(('redis.','pika.')) else 'database'
                evidence=[ev(item)]+config
                key=resource(item,url,kind,evidence)
                if not key:
                    result['warnings'].append(f['name']+':'+str(item.lineno)+'：数据库或消息地址无法静态确认')
                for assignment in ast.walk(tree):
                    if isinstance(assignment,ast.Assign) and assignment.value is item:
                        for target in assignment.targets: resources[dotted(target)]=key
        for item in ast.walk(tree):
            if not isinstance(item,ast.Call):continue
            call=dotted(item.func); base,_,method=call.rpartition('.')
            key=resources.get(base)
            if key and method in ('publish','subscribe','psubscribe') and item.args:
                topic,_=literal(item.args[0])
                if isinstance(topic,str):
                    channel=key+':topic:'+topic
                    nodes.setdefault(channel,dict(id=channel,name=topic,sub='消息主题',type='messagebus',x=0,y=0,evidence=[ev(item)],confidence='confirmed'))
                    if method=='publish':relation(owner(item),channel,'发布','消息','', [ev(item)])
                    else:relation(channel,owner(item),'订阅','消息','', [ev(item)])
                else:result['warnings'].append(f['name']+':'+str(item.lineno)+'：消息主题动态生成，未推断发布订阅配对')
    result['nodes']=list(nodes.values())
    return result

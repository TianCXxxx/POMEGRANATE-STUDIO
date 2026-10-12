"""Conservative architecture projection over retained, evidence-backed facts."""
import copy
import re


def refine_architecture(result):
    raw = copy.deepcopy({'nodes': result['nodes'], 'edges': result['edges']})
    nodes = {n['id']: n for n in result['nodes']}
    edges = result['edges']
    for edge in edges:
        label=edge.get('label','')
        kind=('type-reference' if label=='类型依赖' or edge.get('protocol')=='类型引用' else
              'import' if label=='导入模块' else
              'registration' if label=='注册路由' else
              'injection' if '注入' in label else
              'event' if '事件' in label or label in ('发布','订阅') else
              'data-access' if any(word in label for word in ('ORM','SQLModel','数据库','读写本地')) else
              'call' if '()' in label or label.startswith('反射调用') else
              'network' if edge.get('protocol') in ('HTTP','HTTPS','TCP','gRPC') else 'dependency')
        edge['relationKind']=kind
        edge['architectureImportance']='support' if kind in ('import','type-reference') else 'primary'
        edge['relationReason']='源码引用，不证明执行调用' if kind in ('import','type-reference') else '声明型依赖，运行时绑定待核对' if kind=='injection' else '按调用、注册或连接语句提炼，保留原始置信度'
    parent = {i: i for i in nodes}
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    def file(n):
        files = {e.get('file') for e in n.get('evidence', []) if e.get('file')}
        return next(iter(files)) if len(files) == 1 else None
    for n in nodes.values():
        entry = bool(n.get('listen') or n.get('routes') or n.get('frameworkEntry'))
        module = n['id'].startswith(('module:', 'py:'))
        n['abstractionLevel'] = 'service' if n.get('listen') else 'module' if module else 'component'
        n['architectureRole'] = ('frontend' if n['type'] == 'frontend' else
            'data' if n['type'] in ('database', 'messagebus') else
            'data-model' if n.get('declarationKind')=='data' else
            'entry' if entry else
            'repository' if re.search(r'Repository|仓储|数据访问', n['name']+' '+n.get('sub',''), re.I) else
            'integration' if re.search(r'Client|Gateway|Adapter|出站', n['name']+' '+n.get('sub',''), re.I) else
            'business' if n['type']=='backend' and (re.search(r'Service\b|服务$|业务服务',n['name']+' '+n.get('sub',''),re.I) or not (module or '::' in n['id'])) else
            'repository' if any(e['source']==n['id'] and e['relationKind']=='data-access' for e in edges) else
            'business' if n['type'] == 'backend' and (n.get('businessEvidence') or re.search(r'Service\b|业务服务',n['name']+' '+n.get('sub',''),re.I)) else
            'helper' if n['type']=='backend' else 'dependency')
        n['roleReason']='模型/枚举继承或实体声明，不等同运行数据库' if n['architectureRole']=='data-model' else '框架入口/路由声明' if entry else 'JSX、模板或前端依赖证据' if n['architectureRole']=='frontend' else '连接或消息组件证据，遵循原置信度' if n['architectureRole']=='data' else '职责命名、领域模型行为函数或数据访问语句；静态角色需核对' if n['architectureRole'] in ('business','repository','integration') else '未获得独立业务职责证据，保留为辅助/未分类源码'
        n['roleConfidence']='inferred' if n['architectureRole'] in ('business','repository','integration','helper') else n.get('confidence','confirmed')
        n['abstractionReason'] = '源码监听证据支持独立服务入口；部署实例仍需确认' if n.get('listen') else '按源码模块或逻辑职责分类，不推断独立部署'
    for n in nodes.values():
        if n.get('listen') or n.get('routes'):
            continue
        incoming = [e for e in edges if e['target'] == n['id']]
        # A helper with exactly one importing UI owner can be folded into that UI.
        if n['type'] == 'frontend' and n.get('sub') in ('前端依赖模块', '前端请求模块'):
            owners = {e['source'] for e in incoming}
            if len(owners) == 1 and all(e.get('label') == '导入模块' for e in incoming):
                owner = nodes[next(iter(owners))]
                if owner['type'] == 'frontend' and root(owner['id']) != root(n['id']):
                    parent[root(n['id'])] = root(owner['id'])
        # Generic classes in one file with a direct local relationship are one module.
        elif n.get('sub') == '代码组件' and n['architectureRole']=='helper':
            for e in incoming:
                owner = nodes[e['source']]
                if owner['architectureRole']=='helper' and owner.get('sub') == '代码组件' and file(owner) and file(owner) == file(n) and e.get('relationKind')=='call' and not owner.get('listen') and not owner.get('routes'):
                    if root(n['id']) != root(owner['id']):
                        parent[root(n['id'])] = root(owner['id'])
    # Entry ownership travels only along confirmed in-process dependencies.
    # Network requests do not make the remote service part of the caller.
    local = [e for e in edges if e.get('protocol') == '进程内'
             and e.get('relationKind') not in ('import','type-reference','dependency')
             and e.get('confidence', 'confirmed') == 'confirmed'
             and e.get('style', 'solid') != 'dashed']
    adjacency = {i: [] for i in nodes}
    incoming_local = {i: [] for i in nodes}
    for edge in local:
        if edge['source'] in nodes and edge['target'] in nodes:
            adjacency[edge['source']].append(edge['target'])
            incoming_local[edge['target']].append(edge['source'])
    registered = {e['target'] for e in edges if e.get('label') == '注册路由' and e.get('confidence') == 'confirmed'}
    entries = sorted(i for i, n in nodes.items() if n['architectureRole'] == 'entry' and (i not in registered or n.get('frameworkEntry') or n.get('listen')))
    owners = {i: set() for i in nodes}
    for entry in entries:
        pending, visited = [entry], set()
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            if current != entry and current in entries:
                continue
            if nodes[current]['type'] != 'backend':
                continue
            owners[current].add(entry)
            pending.extend(adjacency[current])
    for i, node in nodes.items():
        node['entryOwners'] = sorted(owners[i])
        if len(owners[i]) == 1:
            owner = next(iter(owners[i]))
            node['architectureGroup'] = owner
            node['ownershipLabel'] = nodes[owner]['name'] + ' · 逻辑归属'
        elif len(owners[i]) > 1:
            node['architectureGroup'] = '__shared__'
            node['ownershipLabel'] = '多入口共享组件'
        else:
            node['ownershipLabel'] = '独立前端' if node['type'] == 'frontend' else '入口归属未确定'
    # Fold utility modules into their sole direct owner across files, only when
    # both are reached from the same one entry. Business/repository/adapter nodes
    # and unresolved or shared dependencies remain individually visible.
    for i in sorted(nodes):
        node = nodes[i]
        if node['architectureRole']!='helper' or node.get('frameworkEntry') or node['type'] != 'backend' or node.get('listen') or node.get('routes'):
            continue
        if node.get('sub') not in ('代码模块', 'Python 模块', '代码组件') or len(owners[i]) != 1:
            continue
        callers = set(incoming_local[i])
        all_callers = {e['source'] for e in edges if e['target'] == i}
        if len(callers) != 1 or callers != all_callers:
            continue
        caller = next(iter(callers))
        if owners[caller] == owners[i] and nodes[caller]['type'] == 'backend' and root(i) != root(caller):
            parent[root(i)] = root(caller)
    declarations = {}
    for i,node in nodes.items():
        source = i.split('::')[0] if '::' in i else file(node)
        if node.get('declarationKind') == 'data' and i.startswith('module:') and source:
            source = source.rsplit('/',1)[0]
        if node.get('declarationKind') == 'data' and source:
            declarations.setdefault(source, []).append(i)
    for source, members in declarations.items():
        representative=members[0]
        for i in members[1:]:
            if root(i)!=root(representative): parent[root(i)]=root(representative)
        if len(members)>1:
            nodes[representative]['name']=source.split('/')[-1].removesuffix('.py')+' · 数据定义'
            nodes[representative]['sub']='模型 / 枚举声明集合'
    # Several logical classes in the same Python source file form one visible
    # module. This is a source boundary, never a deployment-service assertion.
    if len(nodes)>100:
        modules={}
        for i,node in nodes.items():
            if root(i)!=i:continue
            if '::' in i and node['architectureRole']=='helper' and not node.get('routes') and not node.get('listen'):
                modules.setdefault(i.split('::')[0],[]).append(i)
        for source,members in modules.items():
            if len(members)<3:continue
            representative=root(members[0])
            for i in members[1:]:
                if root(i)!=representative:parent[root(i)]=representative
            nodes[representative]['name']=source.split('/')[-1].removesuffix('.py')+' · 逻辑模块'
            nodes[representative]['sub']='同文件类集合 · 保留成员与内部关系'
    # Large UI trees are shown as source-directory components. Members and
    # internal dependencies stay in architectureDetails, never discarded.
    if sum(n['type'] == 'frontend' for n in nodes.values()) > 24:
        directories = {}
        for i,node in nodes.items():
            if root(i)!=i:continue
            source = i.removeprefix('module:') if i.startswith('module:') else file(node)
            if node['type'] == 'frontend' and source and '/' in source:
                directories.setdefault(source.rsplit('/',1)[0], []).append(i)
        for directory,members in directories.items():
            representative = root(members[0])
            for i in members[1:]:
                if root(i) != representative:parent[root(i)] = representative
            if len(members)>1:
                nodes[representative]['name'] = directory
                nodes[representative]['sub'] = '前端目录组件 · 保留源码成员'
    if len(nodes)>70:
        directories={}
        for i,node in nodes.items():
            if root(i)!=i:continue
            source=i.removeprefix('module:').removeprefix('py:').split('::')[0]
            if not source.endswith(('.py','.ts','.tsx','.js','.jsx')) or '/' not in source:continue
            if node.get('listen') or node.get('routes') or node.get('frameworkEntry') or node.get('declarationKind'):continue
            if node['architectureRole']!='helper' or not (node.get('sub') in ('代码组件','代码模块','Python 模块') or node.get('sub','').startswith('同文件类集合')):continue
            group=(source.rsplit('/',1)[0],node.get('architectureGroup','__other__'))
            directories.setdefault(group,[]).append(i)
        for (directory,owner),members in directories.items():
            if len({i.removeprefix('module:').removeprefix('py:').split('::')[0] for i in members})<4:continue
            representative=root(members[0])
            for i in members[1:]:
                if root(i)!=representative:parent[root(i)]=representative
            nodes[representative]['name']=directory
            nodes[representative]['sub']='源码目录组件 · 逻辑边界，保留成员'
    groups = {}
    for i in nodes:
        groups.setdefault(root(i), []).append(nodes[i])
    projected = []
    for i, members in groups.items():
        node = copy.deepcopy(nodes[i])
        node['members'] = copy.deepcopy(members)
        if len(members) > 1:
            node['abstractionLevel'] = 'service' if node.get('listen') else 'component'
            node['abstractionReason'] = '按同文件/实体声明归并数据定义，保持与运行存储的区别；原始成员及关系保留' if node['architectureRole']=='data-model' else '按前端源码目录边界归并；不声称独立部署，保留原始成员和关系' if node['architectureRole']=='frontend' else '按确认依赖与辅助源码边界归并；业务组件保持独立，原始成员及关系保留'
            node['evidence'] = [e for member in members for e in member.get('evidence', [])]
            node['sub'] = ('前端应用' if node['type'] == 'frontend' else '服务入口' if node.get('listen') else node.get('sub', '逻辑组件')) + ' · '+str(len(members))+' 个源码成员'
        projected.append(node)
    output, internal = {}, []
    for edge in edges:
        source, target = root(edge['source']), root(edge['target'])
        if source == target:
            internal.append(copy.deepcopy(edge))
            continue
        key = (source, target, '' if edge['relationKind']=='call' else edge.get('label',''), edge.get('protocol',''), edge.get('port',''), edge.get('confidence','confirmed'),edge['relationKind'])
        if key not in output:
            output[key] = dict(copy.deepcopy(edge), source=source, target=target, originalEdgeIds=[edge['id']])
            if edge['relationKind']=='call':output[key]['callNames']=[edge['label']]
        else:
            output[key]['evidence'].extend(copy.deepcopy(edge.get('evidence', [])))
            output[key]['originalEdgeIds'].append(edge['id'])
            if edge['relationKind']=='call' and edge['label'] not in output[key]['callNames']:
                output[key]['callNames'].append(edge['label'])
                output[key]['label']='代码调用 · '+str(len(output[key]['callNames']))+' 个方法/构造调用'
    result['nodes'], result['edges'] = projected, list(output.values())
    # Retain classification on the raw evidence graph as well as the projection.
    by_edge={e['id']:e for e in edges}
    for original in raw['edges']:
        classified=by_edge[original['id']]
        for field in ('relationKind','architectureImportance','relationReason'):original[field]=classified[field]
    result['architectureDetails'] = dict(raw, internalEdges=internal)
    # Shortest evidence-backed chains, explicitly including uncertain declarations.
    visible={n['id']:n for n in projected};spines=[]
    for entry in entries:
        start=root(entry);queue=[(start,[start],[])];visited={start}
        for current,path,used in queue:
            for edge in output.values():
                if edge['source']!=current or edge['relationKind'] in ('import','type-reference','dependency','event'):continue
                target=edge['target']
                if target in visited:continue
                visited.add(target);next_path=path+[target];next_used=used+[edge['id']]
                if visible[target]['architectureRole'] in ('data','data-model'):
                    spines.append({'nodes':next_path,'edges':next_used,'confidence':'inferred' if any(e.get('confidence')=='inferred' for e in output.values() if e['id'] in next_used) else 'confirmed','endsAt':'data-model' if visible[target]['architectureRole']=='data-model' else 'storage'})
                queue.append((target,next_path,next_used))
    result['architectureSpine']=spines[:24]
    result['architectureSpineStatus']='found' if spines else 'insufficient-evidence'
    result['architectureSpineNote']='主链包含静态调用与声明依赖，推断绑定仍需核对；数据模型不是运行数据库' if spines else '当前源码范围未找到入口到存储/模型的完整证据链；没有补造关系，请核对缺失源码或动态配置'
    spine_edges={i for p in result['architectureSpine'] for i in p['edges']}
    for edge in result['edges']:edge['isArchitectureSpine']=edge['id'] in spine_edges
    result['abstraction'] = {'version':3, 'rawNodeCount':len(raw['nodes']), 'visibleNodeCount':len(projected), 'mergedNodeCount':len(raw['nodes'])-len(projected), 'policy':'沿确认关系识别入口归属；大项目按同文件声明和同目录源码边界聚合，保留成员与内部关系，不添加部署事实', 'entryCount':len(entries), 'sharedNodeCount':sum(len(v)>1 for v in owners.values())}
    return result

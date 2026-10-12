"""Conservative architecture projection over retained, evidence-backed facts."""
import copy
import re


def refine_architecture(result):
    raw = copy.deepcopy({'nodes': result['nodes'], 'edges': result['edges']})
    nodes = {n['id']: n for n in result['nodes']}
    edges = result['edges']
    parent = {i: i for i in nodes}
    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i
    def file(n):
        files = {e.get('file') for e in n.get('evidence', []) if e.get('file')}
        return next(iter(files)) if len(files) == 1 else None
    for n in nodes.values():
        entry = bool(n.get('listen') or n.get('routes'))
        module = n['id'].startswith(('module:', 'py:'))
        n['abstractionLevel'] = 'service' if n.get('listen') else 'module' if module else 'component'
        n['architectureRole'] = ('frontend' if n['type'] == 'frontend' else
            'data' if n['type'] in ('database', 'messagebus') else
            'entry' if entry else
            'repository' if re.search(r'Repository|仓储|数据访问', n['name']+' '+n.get('sub',''), re.I) else
            'integration' if re.search(r'Client|Gateway|Adapter|出站', n['name']+' '+n.get('sub',''), re.I) else
            'business' if n['type'] == 'backend' else 'dependency')
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
        elif n.get('sub') == '代码组件':
            for e in incoming:
                owner = nodes[e['source']]
                if owner.get('sub') == '代码组件' and file(owner) and file(owner) == file(n) and e.get('protocol') == '进程内' and not owner.get('listen') and not owner.get('routes'):
                    if root(n['id']) != root(owner['id']):
                        parent[root(n['id'])] = root(owner['id'])
    # Entry ownership travels only along confirmed in-process dependencies.
    # Network requests do not make the remote service part of the caller.
    local = [e for e in edges if e.get('protocol') == '进程内'
             and e.get('confidence', 'confirmed') == 'confirmed'
             and e.get('style', 'solid') != 'dashed']
    adjacency = {i: [] for i in nodes}
    incoming_local = {i: [] for i in nodes}
    for edge in local:
        if edge['source'] in nodes and edge['target'] in nodes:
            adjacency[edge['source']].append(edge['target'])
            incoming_local[edge['target']].append(edge['source'])
    entries = sorted(i for i, n in nodes.items() if n['architectureRole'] == 'entry')
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
        if node['type'] != 'backend' or node.get('listen') or node.get('routes'):
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
    groups = {}
    for i in nodes:
        groups.setdefault(root(i), []).append(nodes[i])
    projected = []
    for i, members in groups.items():
        node = copy.deepcopy(nodes[i])
        node['members'] = copy.deepcopy(members)
        if len(members) > 1:
            node['abstractionLevel'] = 'service' if node.get('listen') else 'component'
            node['abstractionReason'] = '依据直接依赖与唯一入口归属合并辅助代码；共享依赖和业务职责保持独立，原始成员及内部关系保留'
            node['evidence'] = [e for member in members for e in member.get('evidence', [])]
            node['sub'] = ('前端应用' if node['type'] == 'frontend' else '服务入口' if node.get('listen') else node.get('sub', '逻辑组件')) + ' · '+str(len(members))+' 个源码成员'
        projected.append(node)
    output, internal = {}, []
    for edge in edges:
        source, target = root(edge['source']), root(edge['target'])
        if source == target:
            internal.append(copy.deepcopy(edge))
            continue
        key = (source, target, edge.get('label',''), edge.get('protocol',''), edge.get('port',''), edge.get('confidence','confirmed'))
        if key not in output:
            output[key] = dict(copy.deepcopy(edge), source=source, target=target, originalEdgeIds=[edge['id']])
        else:
            output[key]['evidence'].extend(copy.deepcopy(edge.get('evidence', [])))
            output[key]['originalEdgeIds'].append(edge['id'])
    result['nodes'], result['edges'] = projected, list(output.values())
    result['architectureDetails'] = dict(raw, internalEdges=internal)
    result['abstraction'] = {'version':2, 'rawNodeCount':len(raw['nodes']), 'visibleNodeCount':len(projected), 'mergedNodeCount':len(raw['nodes'])-len(projected), 'policy':'沿已确认进程内关系识别入口归属，仅合并唯一归属辅助代码；不添加部署事实', 'entryCount':len(entries), 'sharedNodeCount':sum(len(v)>1 for v in owners.values())}
    return result

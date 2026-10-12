"""Side-effect-free Python architecture extraction. Never imports submitted code."""
import ast
import json
import sys
import math
import pathlib
import subprocess
import tempfile
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analysis_pipeline
from input_loader import import_files
from native_quality import validate_native


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + '.' + node.attr
    return ''


def analyze(files):
    classes, trees, warnings = {}, [], []
    for file in files:
        if not file['name'].endswith('.py'):
            warnings.append(file['name'] + '：当前语法分析器不支持此格式')
            continue
        try:
            tree = ast.parse(file['text'], filename=file['name'])
        except SyntaxError as error:
            warnings.append(f"{file['name']}:{error.lineno}：语法错误，未分析")
            continue
        trees.append((file['name'], tree))
        for item in tree.body:
            if isinstance(item, ast.ClassDef):
                if item.name in classes:
                    warnings.append(item.name + '：同名类存在歧义，未合并')
                    continue
                classes[item.name] = {'ast': item, 'file': file['name'], 'attrs': {}, 'values': {}}
    nodes, edges = {}, {}
    http_helpers = {}
    for file, tree in trees:
        helpers = set()
        for function in tree.body:
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                isinstance(call, ast.Call) and (dotted(call.func) in ('Request', 'urlopen', 'urllib.request.urlopen', 'urllib.request.Request')
                                              or dotted(call.func).startswith(('requests.', 'httpx.')))
                for call in ast.walk(function)
            ):
                helpers.add(function.name)
        http_helpers[file] = helpers

    def evidence(file, item):
        return {'file': file, 'line': item.lineno}

    def node(key, name, sub, kind, ev):
        if key not in nodes:
            nodes[key] = dict(id=key, name=name, sub=sub, type=kind, evidence=[ev], x=0, y=0)
        elif ev not in nodes[key]['evidence']:
            nodes[key]['evidence'].append(ev)

    def edge(source, target, label, protocol, port, ev):
        if source == target:
            return
        key = (source, target, protocol, port)
        if key not in edges:
            edges[key] = dict(id='fact-' + str(len(edges)), source=source, target=target,
                             label=label, protocol=protocol, port=port, style='solid', evidence=[ev])
        else:
            value = edges[key]
            if label not in value['label'].split(' / '):
                value['label'] += ' / ' + label
            if ev not in value['evidence']:
                value['evidence'].append(ev)

    def literal(item, values):
        if isinstance(item, ast.Constant) and isinstance(item.value, (str, int)):
            return item.value
        if isinstance(item, (ast.Name, ast.Attribute)):
            return values.get(dotted(item))
        if isinstance(item, ast.BinOp) and isinstance(item.op, ast.Add):
            a, b = literal(item.left, values), literal(item.right, values)
            if isinstance(a, str):
                return a + (b if isinstance(b, str) else '{dynamic}')
        if isinstance(item, ast.JoinedStr):
            return ''.join(x.value if isinstance(x, ast.Constant) else '{dynamic}' for x in item.values)
        return None

    for name, record in classes.items():
        item, file = record['ast'], record['file']
        bases = [dotted(base) for base in item.bases]
        role = 'HTTP 接口' if any('RequestHandler' in b for b in bases) else '数据访问层' if 'Repository' in name else '业务服务' if 'Service' in name else '出站适配器' if any(part in name for part in ('Client', 'Gateway', 'Integration', 'Adapter')) else '代码组件'
        node(name, name, role, 'backend', evidence(file, item))
        for member in item.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg, default in zip(member.args.args[-len(member.args.defaults):], member.args.defaults):
                    value = literal(default, {})
                    if value is not None:
                        record['values'][arg.arg] = value
            for assignment in ast.walk(member):
                if not isinstance(assignment, ast.Assign):
                    continue
                for target in assignment.targets:
                    key = dotted(target)
                    if isinstance(assignment.value, ast.Call) and dotted(assignment.value.func) in classes:
                        record['attrs'][key.removeprefix('self.')] = dotted(assignment.value.func)
                    value = literal(assignment.value, record['values'])
                    if value is not None:
                        record['values'][key] = value
    # Resolve class attributes assigned at the application's entry point.
    for file, tree in trees:
        for assignment in ast.walk(tree):
            if isinstance(assignment, ast.Assign) and isinstance(assignment.value, ast.Call):
                destination = dotted(assignment.value.func)
                for target in assignment.targets:
                    path = dotted(target).split('.')
                    if len(path) == 2 and path[0] in classes and destination in classes:
                        classes[path[0]]['attrs'][path[1]] = destination
            if isinstance(assignment, ast.Call) and dotted(assignment.func).split('.')[-1] == 'HTTPServer' and len(assignment.args) >= 2:
                handler = dotted(assignment.args[1])
                address = assignment.args[0]
                if handler in nodes and isinstance(address, (ast.Tuple, ast.List)) and len(address.elts) == 2:
                    host, port = (literal(x, {}) for x in address.elts)
                    if isinstance(port, int):
                        nodes[handler]['sub'] = f'HTTP 入站 · {host}:{port}'
                        nodes[handler]['listen'] = {'protocol': 'HTTP', 'port': str(port), 'evidence': evidence(file, assignment)}
    for name, record in classes.items():
        file = record['file']
        for method in record['ast'].body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            values = dict(record['values'])
            for item in ast.walk(method):
                if isinstance(item, ast.Assign):
                    value = literal(item.value, values)
                    if value is not None:
                        for target in item.targets:
                            values[dotted(target)] = value
            for item in ast.walk(method):
                if not isinstance(item, ast.Call):
                    continue
                path = dotted(item.func).split('.')
                ev = evidence(file, item)
                if path[0] == 'self' and len(path) >= 3:
                    owner = name
                    for attribute in path[1:-1]:
                        owner = classes.get(owner, {}).get('attrs', {}).get(attribute)
                        if not owner:
                            break
                    if owner in nodes:
                        edge(name, owner, path[-1] + '()', '进程内', '不适用', ev)
                if dotted(item.func) == 'sqlite3.connect':
                    filename = literal(item.args[0], values) if item.args else None
                    key = 'sqlite:' + str(filename or file)
                    node(key, 'SQLite', str(filename or '文件路径待确认'), 'database', ev)
                    edge(name, key, '读写本地文件', 'SQLite 文件', '不适用', ev)
                # Only a URL used as the first argument of an HTTP call is evidence.
                call_name = dotted(item.func)
                known_http = call_name in http_helpers[file] or call_name in ('Request', 'urlopen', 'urllib.request.urlopen', 'urllib.request.Request') or call_name.startswith(('requests.', 'httpx.'))
                if not known_http or not item.args:
                    continue
                value = literal(item.args[0], values)
                if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
                    continue
                try:
                    url = urlsplit(value)
                    port = str(url.port or '')
                except ValueError:
                    warnings.append(f'{file}:{item.lineno}：无效 URL')
                    continue
                key = 'remote:' + url.netloc
                endpoint = url.path or '/'
                display = method.name + ' 接口'
                node(key, display, url.netloc, 'external', ev)
                edge(name, key, path[-1].upper() + ' ' + endpoint, url.scheme.upper(), port, ev)
    if not nodes:
        raise ValueError('未提取到支持的 Python 类。请上传 Python 入口、服务、仓储和适配器文件；其他语言暂保留模型分析。')
    return {'title': '源码架构', 'nodes': list(nodes.values()), 'edges': list(edges.values()),
            'provenance': {'analyzer': 'Python AST', 'files': [x['name'] for x in files], 'verified': False,
                           'scope': '仅静态可解析的类、对象调用、SQLite 与 HTTP 地址；动态加载和运行时依赖待核对', 'warnings': warnings}}


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        origin = self.headers.get('Origin', '')
        if origin.startswith('http://127.0.0.1:') or origin.startswith('http://localhost:'):
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.respond(200, {})

    def do_GET(self):
        if self.path.startswith('/jobs/'):
            job = analysis_pipeline.snapshot(self.path.split('/')[-1])
            return self.respond(200 if job else 404, job or {'error': '任务不存在'})
        self.respond(200 if self.path == '/health' else 404, {'service': 'architecture-pipeline-v2'})

    def do_POST(self):
        try:
            if self.path not in ('/analyze', '/export-archify', '/import', '/jobs', '/cancel', '/validate-native', '/deliver-native'):
                return self.respond(404, {'error': 'Not found'})
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 140000000:
                raise ValueError('输入大小超限')
            data = json.loads(self.rfile.read(length))
            if self.path in ('/validate-native', '/deliver-native'):
                return self.respond(200, validate_native(data['graph'], deliver=self.path == '/deliver-native'))
            if self.path == '/import':
                return self.respond(200, import_files(data['files']))
            if self.path == '/jobs':
                return self.respond(202, analysis_pipeline.submit(data))
            if self.path == '/cancel':
                return self.respond(200, analysis_pipeline.cancel(data['id']))
            if self.path == '/export-archify':
                return self.respond(200, {'html': export_archify(data['graph'])})
            files = data['files']
            if not isinstance(files, list) or len(files) > 12:
                raise ValueError('文件数量超限')
            for file in files:
                if not isinstance(file.get('name'), str) or not isinstance(file.get('text'), str):
                    raise ValueError('无效文件')
            self.respond(200, analyze(files))
        except (ValueError, KeyError, TypeError, OSError, subprocess.TimeoutExpired) as error:
            self.respond(400, {'error': str(error)})
        except Exception as error:
            self.respond(400, {'error': '无法处理该文件：' + str(error)})


def export_archify(graph):
    root = pathlib.Path(__file__).resolve().parent
    items = graph['nodes']
    if not isinstance(items, list) or not 1 <= len(items) <= 60:
        raise ValueError('无效组件数量')
    mapping = {item['id']: 'n' + str(i) for i, item in enumerate(items)}
    types = {'frontend', 'backend', 'database', 'cloud', 'security', 'messagebus', 'external'}
    def point(value):
        if not isinstance(value, list) or len(value) != 2 or not all(isinstance(x, (int, float)) and math.isfinite(x) and abs(x) < 10000 for x in value):
            raise ValueError('无效坐标')
        return value
    components = [dict(id=mapping[item['id']], label=str(item['name'])[:120], sublabel=str(item.get('sub', ''))[:200],
                       type=item['type'] if item['type'] in types else 'cloud' if item['type'] == 'model' else 'backend',
                       pos=point([item['x'], item['y']]), size=[180, 78]) for item in items]
    connections = []
    if len(graph['edges']) > 150:
        raise ValueError('连线数量超限')
    label_boxes = []
    for i, item in enumerate(graph['edges']):
        relation = dict(id='e' + str(i), **{'from': mapping[item['source']], 'to': mapping[item['target']]},
                        label=' · '.join(str(item.get(k, '')) for k in ('protocol', 'port', 'label') if item.get(k)),
                        variant='dashed' if item.get('style') == 'dashed' else 'default')
        geometry = item.get('exportGeometry', {})
        for key in ('fromSide', 'toSide'):
            if geometry.get(key) in ('top', 'right', 'bottom', 'left'):
                relation[key] = geometry[key]
        if geometry.get('points'):
            route_points = [point(p) for p in geometry['points']]
            relation['via'] = route_points[1:-1]
        if geometry.get('labelAt'):
            relation['labelAt'] = point(geometry['labelAt'])
        # The native renderer uses one label line, unlike the editor's two lines.
        # Re-measure that full label and place it clear of all component boxes.
        first = next(c for c in components if c['id'] == relation['from'])
        last = next(c for c in components if c['id'] == relation['to'])
        origin = relation.get('labelAt', [(first['pos'][0]+last['pos'][0])/2+90, (first['pos'][1]+last['pos'][1])/2+25])
        width = max(30, sum(2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1 for ch in relation['label'])*4.8+10)
        obstacles = [(c['pos'][0]-3, c['pos'][1]-3, 186, 84) for c in components] + label_boxes
        def intersects(a, b):
            return a[0] < b[0]+b[2] and a[0]+a[2] > b[0] and a[1] < b[1]+b[3] and a[1]+a[3] > b[1]
        found = False
        for dy in (0, -20, 20, -40, 40, -60, 60, -90, 90, -120, 120):
            for dx in (0, -20, 20, -50, 50):
                candidate = [origin[0]+dx, origin[1]+dy]
                rect = (candidate[0]-width/2, candidate[1]-10, width, 14)
                if rect[0] >= 5 and rect[1] >= 5 and not any(intersects(rect, obstacle) for obstacle in obstacles):
                    relation['labelAt'] = candidate
                    label_boxes.append(rect)
                    found = True
                    break
            if found:
                break
        connections.append(relation)
    cards = []
    for item in items:
        refs = ', '.join(f"{e['file']}:{e['line']}" for e in item.get('evidence', [])[:20])
        if refs:
            cards.append({'dot': 'slate', 'title': str(item['name']), 'items': ['源码依据：' + refs]})
    spec = dict(schema_version=1, diagram_type='architecture', meta=dict(title=str(graph.get('title', '架构图'))[:100],
                subtitle='本地源码架构 · Archify 原生渲染', locale='zh-CN'), components=components, connections=connections, cards=cards)
    with tempfile.TemporaryDirectory(prefix='archify-export-') as temporary:
        source, output = pathlib.Path(temporary) / 'diagram.json', pathlib.Path(temporary) / 'diagram.html'
        source.write_text(json.dumps(spec, ensure_ascii=False), encoding='utf-8')
        result = subprocess.run([str(root / 'node.exe'), str(root / 'archify/renderers/architecture/render-architecture.mjs'), str(source), str(output)],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15,
                                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        if result.returncode:
            raise ValueError('Archify 原生校验未通过：' + result.stderr[-1600:])
        return output.read_text(encoding='utf-8')


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 18767), Handler).serve_forever()

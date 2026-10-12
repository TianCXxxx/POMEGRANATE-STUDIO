"""Run the pinned native Archify showcase validator, retaining its real receipt."""
import json
import hashlib
import html as html_escape
import xml.etree.ElementTree as ET
import math
import pathlib
import subprocess
import sys
import tempfile


def validate_native(graph, deliver=False):
    root=pathlib.Path(__file__).resolve().parent
    if not 1 <= len(graph['nodes']) <= 200 or len(graph['edges'])>500:
        raise ValueError('无效图规模')
    def point(values):
        if len(values)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) and abs(v)<=200000 for v in values):
            raise ValueError('无效坐标')
        return values
    ids={n['id']:'n'+str(i) for i,n in enumerate(graph['nodes'])}
    types={'frontend','backend','database','cloud','security','messagebus','external'}
    components=[{'id':ids[n['id']],'type':n['type'] if n['type'] in types else 'cloud','label':str(n['name'])[:300], 'sublabel':str(n['sub'])[:700],'pos':point([n['x'],n['y']]),'size':point([n.get('width',240),n.get('height',112)])} for n in graph['nodes']]
    connections=[]
    for i,e in enumerate(graph['edges']):
        geometry=e['exportGeometry']
        relation={'id':'e'+str(i),'from':ids[e['source']],'to':ids[e['target']],'label':' · '.join(str(e.get(k,'')) for k in ('protocol','port','label') if e.get(k)), 'variant':'dashed' if e.get('style')=='dashed' else 'default'}
        for side in ('fromSide','toSide'):
            if geometry.get(side) in ('top','right','bottom','left'):
                relation[side]=geometry[side]
        relation['via']=[point(p) for p in geometry['points'][1:-1]]
        relation['labelAt']=point(geometry['labelAt'])
        connections.append(relation)
    spec={'schema_version':1,'diagram_type':'architecture','meta':{'title':str(graph.get('title','架构图'))[:300],'quality_profile':'showcase','locale':'zh-CN'},'components':components,'connections':connections}
    with tempfile.TemporaryDirectory(prefix='archtool-quality-') as temp:
        source=pathlib.Path(temp)/'graph.json';source.write_text(json.dumps(spec,ensure_ascii=False),encoding='utf-8')
        output=pathlib.Path(temp)/'architecture.html'
        command=[str(root/'node.exe'),str(root/'archify/bin/archify.mjs'),'deliver' if deliver else 'validate','architecture',str(source)]
        if deliver:
            command.append(str(output))
        result=subprocess.run(command+['--quality','showcase','--json'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        html=output.read_bytes().decode('utf-8') if deliver and result.returncode==0 else None
    try:
        receipt=json.loads(result.stdout)
    except ValueError:
        receipt={'error':result.stderr[-6000:],'output':result.stdout[-6000:]}
    response={'passed':result.returncode==0,'exitCode':result.returncode,'receipt':receipt,'spec':spec,'scope':'Archify 原生渲染器的独立 showcase 校验；与编辑器换行 SVG 不同，不能混同两种验收。'}
    if html is not None:
        canonical = graph.get('canonicalSVG')
        editor = graph.get('editorReceipt', {})
        if not isinstance(canonical, str) or len(canonical) > 8_000_000:
            raise ValueError('缺少同画布 SVG 快照，请刷新页面后重试')
        tree = ET.fromstring(canonical)
        if tree.tag.split('}')[-1] != 'svg':
            raise ValueError('无效 SVG 快照')
        allowed = {'svg','g','defs','marker','path','rect','text','title','circle','line','polyline','polygon','ellipse','tspan'}
        for element in tree.iter():
            if element.tag.split('}')[-1] not in allowed:
                raise ValueError('SVG 包含不支持的内容')
            for key, value in element.attrib.items():
                name = key.split('}')[-1].lower()
                if name.startswith('on') or name in ('href','style'):
                    raise ValueError('SVG 包含外部引用或动态属性')
        if editor.get('warningCount') != 0:
            raise ValueError('编辑画布仍有质量诊断，请先自动修图或处理剩余问题')
        title = html_escape.escape(str(graph.get('title','架构图')))
        artifact = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+title+'</title><style>body{margin:0;font:14px Segoe UI,Microsoft YaHei;background:#f1f5f9}header{padding:16px;background:white;position:sticky;top:0}main{padding:24px;overflow:auto}svg{background:white}button{margin-left:12px;padding:6px 12px}</style><header>'+title+'<button id="fit">适应</button><button id="actual">原尺寸</button></header><main>'+canonical+'</main><script>const s=document.querySelector("svg"),w=+s.getAttribute("width"),h=+s.getAttribute("height");function scale(z){s.style.width=w*z+"px";s.style.height=h*z+"px"}document.getElementById("fit").onclick=()=>scale(Math.min(1,(innerWidth-48)/w));document.getElementById("actual").onclick=()=>scale(1);document.getElementById("fit").click();</script></html>'
        response['html'] = artifact
        response['editorReceipt'] = editor
        response['canonicalSvgSha256'] = hashlib.sha256(canonical.encode()).hexdigest()
        response['artifactSha256'] = hashlib.sha256(artifact.encode()).hexdigest()
        response['nativeArtifactSha256'] = hashlib.sha256(html.encode()).hexdigest()
        response['scope'] = '最终 HTML 使用编辑画布的同一 SVG，保留颜色、系统边界、换行及路径；编辑器诊断与原生规范校验分别记录。原生校验收据只认证原生对照产物，不认证最终 SVG。'

    return response

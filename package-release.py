"""Build a clean, self-contained Windows distribution from the offline bundle."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / 'offline-demo'
OUT = ROOT / 'release'
OUT.mkdir(exist_ok=True)
archive = OUT / 'Pomegranate-Studio-2.0-Windows-Offline.zip'
root_files = {'analysis_pipeline.py','architecture_abstraction.py','semantic_relations.py','framework_relations.py','code-analyzer.py','input_loader.py','project_facts.py','rfp_facts.py','native_quality.py','node.exe','launch.ps1','start.cmd','stop.cmd','stop.ps1','start-analyzer.ps1','stop-analyzer.ps1','official-model-hashes.json','runtime-release.json','model-revision-1.5b.json'}
web_files = {'index.html','apple.html'} | set(re.findall(r'src="([^"/]+\.js)"', (BUNDLE/'web/index.html').read_text(encoding='utf-8')))
files = []
for p in sorted(BUNDLE.rglob('*')):
    if not p.is_file(): continue
    rel = p.relative_to(BUNDLE)
    if '__pycache__' in rel.parts or p.suffix == '.pyc': continue
    if len(rel.parts)==1 and rel.name in root_files:
        files.append((p,rel.as_posix()))
    elif rel.parts[0] in {'models','runtime','python','licenses','archify'}:
        files.append((p,rel.as_posix()))
    elif rel.parts[0]=='web' and (rel.parts[1]=='vendor' or len(rel.parts)==2 and rel.name in web_files):
        files.append((p,rel.as_posix()))
required = root_files | {'models/qwen2.5-1.5b-instruct-q4_k_m.gguf'} | {'web/'+f for f in web_files}
missing = required - {name for _,name in files}
if missing: raise SystemExit('Missing required files: '+str(sorted(missing)))
readme = """# 石榴构图 / POMEGRANATE STUDIO 2.0

适用 Windows x64。无需安装 Ollama、Python 或 Node；模型随包提供，首次启动可离线。

1. 把整个 ZIP 解压到一个可写文件夹，例如 Documents 下的 Pomegranate-Studio。不要在 ZIP 中直接启动。
2. 双击 start.cmd，等待模型就绪，浏览器会打开 http://127.0.0.1:18765/index.html。
3. 上传文字型 PDF / Markdown / TXT，或代码目录 / ZIP。分析期间可以取消。
4. 拖动、编辑组件与四边连接点；协议、端口和依据可以查看与修改。
5. 导出 PNG / drawio / HTML，或保存 JSON 项目；传给别人请使用保存的项目文件。
6. 使用完双击 stop.cmd。启动失败时查看运行后产生的 server-error.log 和 analyzer-error.log。

首次加载和分析速度取决于 CPU、内存与磁盘。模型约 1.1 GB；请保留包内全部文件。
18765 和 18767 端口仅用于本机服务；被占用时先停止此前启动的工具。
浏览器自动保存的数据不会随软件包转移。不要依赖自动保存替代 JSON 项目备份。

代码关系：Python / JS / TS 静态分析，结合 Qwen2.5 1.5B 综合；虚线表示推断。
动态反射、运行环境、完整容器绑定和 ORM 映射仍需人工核对。扫描 PDF 需要先 OCR。
单文件最多 2 MB；最多 1000 文件 / 20 MB 文本；最多 200 组件 / 500 关系。
自动修图只接受可测量的改善，无法改善的诊断保留。
同画布校验版 HTML 保留编辑器 SVG；原生 showcase 对照和编辑器检查分别记录。

许可证保留在 licenses、archify/LICENSE、archify/THIRD_PARTY_NOTICES.md 和 web/vendor 中。
manifest.json 记录包内文件 SHA-256。模型与运行程序来源元数据随包保留。
交付包不含测试资料、旧预览、用户项目、模型运行日志或进程记录。
"""
entries = {}
for p,name in files:
    if name.endswith('provenance.json'):
        try:
            value=json.loads(p.read_text(encoding='utf-8-sig'));value.pop('installedSource',None)
            entries[name]=json.dumps(value,ensure_ascii=False,indent=2).encode()
        except ValueError: pass
entries['README.md']=readme.encode('utf-8-sig')
manifest={'product':'石榴构图','englishName':'POMEGRANATE STUDIO','version':'2.0','release':'2026-10-11','platform':'Windows x64','offline':True,'model':'Qwen2.5-1.5B-Instruct Q4_K_M','files':{}}
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
    for p,name in files:
        content=entries.pop(name,None)
        digest=hashlib.sha256()
        if content is not None:
            digest.update(content);z.writestr('Pomegranate-Studio-2.0/'+name,content);size=len(content)
        else:
            with p.open('rb') as source,z.open('Pomegranate-Studio-2.0/'+name,'w',force_zip64=True) as target:
                while block:=source.read(4*1024*1024):digest.update(block);target.write(block)
            size=p.stat().st_size
        manifest['files'][name]={'bytes':size,'sha256':digest.hexdigest()}
    for name,content in entries.items():
        z.writestr('Pomegranate-Studio-2.0/'+name,content)
        manifest['files'][name]={'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
    z.writestr('Pomegranate-Studio-2.0/manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive) as z:
    if z.testzip():raise SystemExit('ZIP integrity check failed')
    names=z.namelist()
    if any('/examples/' in n or '/styles/' in n or n.endswith('.log') or '-process.json' in n for n in names):raise SystemExit('Unexpected private or obsolete file')
sha=hashlib.sha256()
with archive.open('rb') as stream:
    while block:=stream.read(4*1024*1024):sha.update(block)
(OUT/(archive.name+'.sha256')).write_text(sha.hexdigest()+'  '+archive.name+'\n',encoding='ascii')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'files':len(names),'sha256':sha.hexdigest()},ensure_ascii=False))

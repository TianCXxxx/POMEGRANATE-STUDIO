import pathlib
import shutil
root=pathlib.Path(__file__).resolve().parent
bundle=root/'offline-demo'
for name in ('code-analyzer.py','input_loader.py','project_facts.py','rfp_facts.py','analysis_pipeline.py','native_quality.py','architecture_abstraction.py','semantic_relations.py','framework_relations.py'):
    shutil.copy2(root/name,bundle/name)
for name in ('project-javascript.js','offline-pipeline.js','architecture-renderer.js','compact-layout.js','canonical-drawio.js','quality-boundaries.js','workspace-recovery.js','relationship-preview.js','diagram-repair.js'):
    if (root/name).exists():
        shutil.copy2(root/name,bundle/'web'/name)
for path in [bundle/'web'/'index.html']:
    if not path.exists():
        continue
    text=path.read_text(encoding='utf-8-sig')
    text=text.replace('<script src="offline-model.js"></script>','<script src="project-javascript.js"></script><script src="offline-pipeline.js"></script>')
    if (root/'architecture-renderer.js').exists() and 'src="architecture-renderer.js"' not in text:
        text=text.replace('<script src="offline-pipeline.js">','<script src="architecture-renderer.js"></script><script src="offline-pipeline.js">')
    if (root/'workspace-recovery.js').exists() and 'src="workspace-recovery.js"' not in text:
        text=text.replace('</body>','<script src="workspace-recovery.js"></script></body>')
    if (root/'canonical-drawio.js').exists() and 'src="canonical-drawio.js"' not in text:
        text=text.replace('<script src="offline-pipeline.js">','<script src="canonical-drawio.js"></script><script src="offline-pipeline.js">')
    if (root/'quality-boundaries.js').exists() and 'src="quality-boundaries.js"' not in text:
        text=text.replace('<script src="offline-pipeline.js">','<script src="quality-boundaries.js"></script><script src="offline-pipeline.js">')
    if (root/'compact-layout.js').exists() and 'src="compact-layout.js"' not in text:
        text=text.replace('<script src="quality-boundaries.js">','<script src="compact-layout.js"></script><script src="quality-boundaries.js">')
    if 'src="relationship-preview.js"' not in text:
        text=text.replace('</body>','<script src="relationship-preview.js"></script></body>')
    if 'src="diagram-repair.js"' not in text:
        text=text.replace('</body>','<script src="diagram-repair.js"></script></body>')
    # Match the 200 node graph contract; bounds can exceed the original 3000 px.
    text=text.replace('Math.min(3000,','Math.min(100000,').replace('n.x>3000||n.y>3000','n.x>100000||n.y>100000')
    path.write_text(text,encoding='utf-8')
path=bundle/'start-analyzer.ps1'
path.write_text(path.read_text(encoding='utf-8-sig').replace('architecture-ast-v1','architecture-pipeline-v2'),encoding='utf-8-sig')
import runpy
runpy.run_path(str(root/'patch-reader-layout.py'))
print('Updated offline bundle')

"""Local ArchTool adaptation: apply the native outer-width solver to tall diagrams too.

Geometry, SVG typography and all validators remain unchanged. The solver retains
its 960px minimum reader width, so oversized diagrams still report overflow.
"""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
target = root / 'offline-demo/archify/assets/template.html'
text = target.read_text(encoding='utf-8')
before = 'shell && diagram && svg && ratio >= WIDE_RATIO &&'
after = 'shell && diagram && svg && ratio > 0 && // ArchTool: adapt tall diagrams too.'
record = root / 'offline-demo/archify/ARCHTOOL-PATCHES.json'
if before in text:
    upstream = hashlib.sha256(target.read_bytes()).hexdigest()
    target.write_text(text.replace(before, after, 1), encoding='utf-8')
    record.write_text(json.dumps({'templateUpstreamSha256': upstream,
        'templatePatchedSha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'patch': 'Enable existing desktop outer-width solver for all positive SVG aspect ratios; keep geometry, fonts, minimum width and validators unchanged.'}, indent=2), encoding='utf-8')
elif after not in text:
    raise RuntimeError('Unknown Archify template; patch not applied')

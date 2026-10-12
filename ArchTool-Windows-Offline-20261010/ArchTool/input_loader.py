"""Bounded, in-memory local document/project import; never extract ZIP to disk."""
import base64
import io
import pathlib
import zipfile

MAX_FILES = 1000
MAX_TOTAL = 20 * 1024 * 1024
MAX_FILE = 2 * 1024 * 1024
TEXT_EXTENSIONS = {'.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.html', '.htm', '.css', '.scss', '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.properties', '.java', '.go', '.rs', '.cs', '.cpp', '.c', '.h', '.sql', '.md', '.markdown', '.txt', '.xml', '.sh'}
SKIP_DIRS = {'node_modules', '.git', '.venv', 'venv', '__pycache__', 'dist', 'build', 'coverage', '.next', 'vendor'}


def import_files(items):
    files, skipped, issues = [], [], []
    total = 0
    seen = set()

    def add(name, raw):
        nonlocal total
        name = name.replace('\\', '/')
        parts = pathlib.PurePosixPath(name).parts
        if name.startswith('/') or '..' in parts or any(':' in part for part in parts):
            skipped.append({'file': name, 'reason': '不接受绝对路径或上级目录路径'})
            return
        if any(part in SKIP_DIRS for part in parts) or name.endswith(('.min.js', '.map', 'package-lock.json', 'yarn.lock')):
            skipped.append({'file': name, 'reason': '依赖、构建或缓存文件'})
            return
        if name in seen:
            raise ValueError('重复文件路径：' + name + '。请用目录或 ZIP 保留路径。')
        seen.add(name)
        if len(raw) > MAX_FILE:
            skipped.append({'file': name, 'reason': '单文件超过 2 MB'})
            return
        total += len(raw)
        if total > MAX_TOTAL or len(files) >= MAX_FILES:
            raise ValueError('项目超过 1000 文件或 20 MB 文本上限，请排除构建产物后重试')
        suffix = pathlib.PurePosixPath(name).suffix.lower()
        if pathlib.PurePosixPath(name).name.startswith('.env'):
            suffix = '.txt'
        if suffix == '.pdf':
            from pypdf import PdfReader
            try:
                reader = PdfReader(io.BytesIO(raw))
                if reader.is_encrypted and not reader.decrypt(''):
                    raise ValueError('PDF 已加密，请先解密')
                if len(reader.pages) > 300:
                    raise ValueError('PDF 超过 300 页，请按章节拆分')
                pages = []
                empty = []
                for number, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ''
                    if not text.strip():
                        empty.append(number)
                    pages.append({'page': number, 'text': text})
                if not any(p['text'].strip() for p in pages):
                    raise ValueError('没有可提取的文字，可能是扫描型 PDF；请先 OCR 后导入')
                files.append({'name': name, 'text': '\n'.join(f"[第 {p['page']} 页]\n{p['text']}" for p in pages), 'pages': pages, 'bytes': len(raw)})
                if empty:
                    issues.append(name + '：以下页面未提取到文字，需核对是否为扫描页：' + ','.join(map(str, empty)))
            except Exception as error:
                raise ValueError(name + '：PDF 读取失败：' + str(error)) from error
        elif suffix in TEXT_EXTENSIONS or pathlib.PurePosixPath(name).name in ('Dockerfile', '.env', '.env.example'):
            if b'\x00' in raw[:4000]:
                skipped.append({'file': name, 'reason': '二进制内容'})
                return
            for encoding in ('utf-8-sig', 'gb18030'):
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    text = None
            if text is None:
                skipped.append({'file': name, 'reason': '文本编码无法识别'})
                return
            files.append({'name': name, 'text': text, 'bytes': len(raw)})
        else:
            skipped.append({'file': name, 'reason': '非源码/文档格式'})

    for item in items:
        name = str(item['name'])
        raw = base64.b64decode(item['base64'], validate=True) if 'base64' in item else str(item['text']).encode('utf-8')
        if name.lower().endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                infos = archive.infolist()
                if len(infos) > 15000 or sum(i.file_size for i in infos) > 100 * 1024 * 1024:
                    raise ValueError('ZIP 展开规模超过限制，请排除依赖与构建产物')
                for info in infos:
                    if info.is_dir():
                        continue
                    if info.flag_bits & 1:
                        raise ValueError('不支持加密 ZIP')
                    if info.file_size > MAX_FILE:
                        skipped.append({'file': info.filename, 'reason': '单文件超过 2 MB'})
                        continue
                    add(info.filename, archive.read(info))
        else:
            add(name, raw)
    if not files:
        raise ValueError('没有可分析的文件。' + '；'.join(x['reason'] for x in skipped[:3]))
    return {'files': files, 'skipped': skipped, 'issues': issues, 'bytes': total}

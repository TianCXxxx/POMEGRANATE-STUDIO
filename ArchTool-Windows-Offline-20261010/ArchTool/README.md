# ArchTool 离线架构工具

适用 Windows x64。无需安装 Ollama、Python 或 Node；模型随包提供，首次启动可离线。

1. 把整个 ZIP 解压到一个可写文件夹，例如 Documents 下的 ArchTool。不要在 ZIP 中直接启动。
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
最多 1000 文件 / 20 MB 文本；最多 200 组件 / 500 关系。
自动修图只接受可测量的改善，无法改善的诊断保留。
同画布校验版 HTML 保留编辑器 SVG；原生 showcase 对照和编辑器检查分别记录。

许可证保留在 licenses、archify/LICENSE、archify/THIRD_PARTY_NOTICES.md 和 web/vendor 中。
manifest.json 记录包内文件 SHA-256。模型与运行程序来源元数据随包保留。
交付包不含测试资料、旧预览、用户项目、模型运行日志或进程记录。

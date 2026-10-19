# 石榴构图 / POMEGRANATE STUDIO 2.0

本地离线架构图工具：导入文字型 PDF、Markdown、TXT 或代码目录 / ZIP，结合静态解析与内置 Qwen2.5 1.5B 生成可编辑架构图。

支持组件拖动、四边连接点、协议和端口标注，以及 PNG、HTML、drawio 和 JSON 项目导出。

## 使用

Windows x64 离线发行包包含模型、Python、Node 和 llama.cpp。完整解压发行包后双击 `start.cmd`；使用完成后运行 `stop.cmd`。

源码仓库不包含这些大型运行文件。直接下载本仓库不会得到可启动的完整离线环境。当前离线包名：`Pomegranate-Studio-2.0-Windows-Offline.zip`。

## 源码结构

- 根目录 Python / JavaScript：分析、架构提炼、布局、编辑与导出实现。
- `offline-demo/web`：发布网页与所需前端依赖。
- `offline-demo/archify`：保留许可证的 Archify 集成资源。
- `deploy-v2.py`：将当前实现同步到离线目录。
- `package-release.py`：基于完整离线目录打包并生成文件哈希清单。

构建需要完整的离线运行文件；在配齐运行环境后执行 `python deploy-v2.py`，再执行 `python package-release.py`。

## 能力边界

单文件 2 MB，最多 1000 文件 / 20 MB 文本；扫描 PDF 需先 OCR。Python、JS/TS 有静态解析；动态调用和复杂项目关系需人工核对。复杂图仍可能存在标签遮挡。

## 可选：Codex 在线演示

默认使用内置本地模型。安装并登录 Codex CLI 后，可在 `offline-demo` 目录建立本机配置文件 `provider.local.json`，内容为 `{"provider":"codex","model":"gpt-5.6-luna"}`，重启项目后使用在线模型。可用模型取决于账号权限；删除该文件并重启可恢复本地模型。本机配置不会提交到 Git，不要将凭证写入此文件。

此模式需要联网，会将分析所需的文档内容、代码片段或提取的组件事实发送至 OpenAI，且受账号限额、网络、项目大小与排版耗时影响。请只使用允许发送的资料。也可通过环境变量 `POMEGRANATE_MODEL_PROVIDER=codex` 和 `POMEGRANATE_CODEX_MODEL` 配置。

## 第三方许可

第三方组件的许可证随源码保留于 `offline-demo/licenses`、`offline-demo/archify` 和前端 vendor 目录。项目自身尚未指定开源许可证。

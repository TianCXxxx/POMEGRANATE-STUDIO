# 企业指标分析平台：预期关系

指标服务调用身份和目录服务完成校验与查询，报告任务通过队列异步生成；缓存存储热点结果。

## 可核对的主链

- InsightsPage → Metrics API：HTTP / 8300（web/src/api.ts、services/metrics/api.py）
- Metrics API → MetricsService → MetricsRepository → PostgreSQL（services/metrics/api.py、service.py、repository.py、database.py）
- MetricsService → IdentityClient → identity API：HTTP / 8301（services/metrics/clients.py）
- MetricsService → CatalogClient → catalog API：HTTP / 8302（services/metrics/clients.py）
- MetricsService → RabbitMQ → Report worker：AMQP / 5672，任务 `reports.on_metrics_requested`（services/metrics/events.py、services/reports/worker.py）
- Identity API → IdentityService → IdentityRepository → PostgreSQL（services/identity/api.py、service.py、repository.py、database.py）
- Catalog API → CatalogService → CatalogRepository → PostgreSQL（services/catalog/api.py、service.py、repository.py、database.py）
- Report API → ReportService → ReportRepository → PostgreSQL（services/reports/api.py、service.py、repository.py、database.py）
- MetricsService → MetricsCache → Redis：6379（services/metrics/cache.py）

## 使用与判断

将同名文件夹或 ZIP 作为“代码项目”导入；本说明不放在项目文件夹中，避免答案直接进入分析内容。上述是源码声明的预期关系，不代表解析器一定识别。事件订阅、依赖注入、ORM、服务部署可能需要人工核对。服务内的细粒度类可根据架构抽象合并；不要把 import 或类型引用直接当作运行时调用。示例中的 localhost 和 demo 连接串仅用于演示。

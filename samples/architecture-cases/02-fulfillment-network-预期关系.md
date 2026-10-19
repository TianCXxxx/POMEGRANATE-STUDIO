# 仓储履约网络：预期关系

履约服务协调仓储、运力与物流，发货事件由跟踪服务消费，前端查询物流状态。

## 可核对的主链

- FulfillmentPage → Fulfillment API：HTTP / 8200（web/src/api.ts、services/fulfillment/api.py）
- Fulfillment API → FulfillmentService → FulfillmentRepository → PostgreSQL（services/fulfillment/api.py、service.py、repository.py、database.py）
- FulfillmentService → WarehouseClient → warehouse API：HTTP / 8201（services/fulfillment/clients.py）
- FulfillmentService → CarrierClient → carrier API：HTTP / 8202（services/fulfillment/clients.py）
- FulfillmentService → RabbitMQ → Tracking worker：AMQP / 5672，任务 `tracking.on_dispatched`（services/fulfillment/events.py、services/tracking/worker.py）
- Warehouse API → WarehouseService → WarehouseRepository → PostgreSQL（services/warehouse/api.py、service.py、repository.py、database.py）
- Carrier API → CarrierService → CarrierRepository → PostgreSQL（services/carrier/api.py、service.py、repository.py、database.py）
- Tracking API → TrackingService → TrackingRepository → PostgreSQL（services/tracking/api.py、service.py、repository.py、database.py）

## 使用与判断

将同名文件夹或 ZIP 作为“代码项目”导入；本说明不放在项目文件夹中，避免答案直接进入分析内容。上述是源码声明的预期关系，不代表解析器一定识别。事件订阅、依赖注入、ORM、服务部署可能需要人工核对。服务内的细粒度类可根据架构抽象合并；不要把 import 或类型引用直接当作运行时调用。示例中的 localhost 和 demo 连接串仅用于演示。

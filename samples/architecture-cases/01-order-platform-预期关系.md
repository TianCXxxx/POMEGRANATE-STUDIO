# 订单交易平台：预期关系

前端下单后经过订单、库存和支付服务；订单写库后发布事件，通知服务异步处理。

## 可核对的主链

- OrderPage → Order API：HTTP / 8100（web/src/api.ts、services/orders/api.py）
- Order API → OrderService → OrderRepository → PostgreSQL（services/orders/api.py、service.py、repository.py、database.py）
- OrderService → InventoryClient → inventory API：HTTP / 8101（services/orders/clients.py）
- OrderService → PaymentClient → payments API：HTTP / 8102（services/orders/clients.py）
- OrderService → RabbitMQ → Notification worker：AMQP / 5672，任务 `notifications.on_order_created`（services/orders/events.py、services/notifications/worker.py）
- Inventory API → InventoryService → InventoryRepository → PostgreSQL（services/inventory/api.py、service.py、repository.py、database.py）
- Payment API → PaymentService → PaymentRepository → PostgreSQL（services/payments/api.py、service.py、repository.py、database.py）
- Notification API → NotificationService → NotificationRepository → PostgreSQL（services/notifications/api.py、service.py、repository.py、database.py）

## 使用与判断

将同名文件夹或 ZIP 作为“代码项目”导入；本说明不放在项目文件夹中，避免答案直接进入分析内容。上述是源码声明的预期关系，不代表解析器一定识别。事件订阅、依赖注入、ORM、服务部署可能需要人工核对。服务内的细粒度类可根据架构抽象合并；不要把 import 或类型引用直接当作运行时调用。示例中的 localhost 和 demo 连接串仅用于演示。

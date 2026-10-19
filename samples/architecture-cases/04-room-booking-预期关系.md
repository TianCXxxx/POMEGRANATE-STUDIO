# 会议室预约系统：预期关系

这是中等规模的单后端项目，用于演示代码生成架构图。以下预期依据源码编写，实际识别可能有遗漏，不能把预期当成已验证的输出。

- **前端页面 → API 请求模块**：`web/src/BookingPage.js` 调用 `web/src/api.js` 的查询和预约函数。
- **前端 → 后端 API**：`web/src/api.js` 通过 HTTP 调用 `localhost:8080` 的 `/api/rooms` 和 `/api/bookings`；路由见 `backend/api.py`。
- **后端 API → 业务服务**：`backend/api.py` 通过依赖注入使用 `RoomService` 和 `BookingService`；业务实现见 `backend/services.py`。
- **业务服务 → 数据访问 → SQLite**：业务服务调用 `RoomRepository` 和 `BookingRepository`，再通过 `BookingDatabase` 操作 `meeting_rooms.db`。相关代码见 `backend/repository.py`、`backend/database.py`。
- **预约服务 → 通知模块**：`BookingService.reserve()` 调用 `NotificationService.send_confirmation()`；通知只写日志，没有外部邮件服务。

项目文件夹和 ZIP 不含本预期说明。导入时选择同名 ZIP 或项目文件夹；观察前后端分层、HTTP 端口、业务服务、数据存储与通知模块即可。细粒度类是否合并由工具的抽象策略决定。

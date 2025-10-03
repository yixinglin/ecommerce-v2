非常好！下面是为你的**订单履约系统**量身设计的 ✅**接口清单（API spec）** + ✅**数据返回结构说明**，从用户视角出发，覆盖典型使用场景。

---

# 📦 1. **订单管理模块**

### ✅ 1.1 拉取订单（多渠道）

```http
POST /api/orders/pull
```

#### 🔸 Body

```json
{
  "channel": "woocommerce",
  "seller_id": "store_abc"
}
```

#### 🔸 Response

```json
{
  "pulled": 120,
  "new_orders": 85,
  "failed": 0
}
```

---

### ✅ 1.2 查询订单列表

```http
GET /api/orders
```

#### 🔸 Query Params:

* `status`: 订单状态（可多选）
* `channel`: 平台
* `seller_id`: 店铺
* `batch_id`: 所属批次
* `page`, `limit`: 分页

#### 🔸 Response

```json
{
  "total": 124,
  "orders": [
    {
      "order_id": "123456",
      "channel": "woocommerce",
      "seller_id": "store_abc",
      "status": "label_created",
      "tracking_number": "DHL123456",
      "batch_id": "BATCH_woocommerce_20251005_002",
      "created_at": "2025-10-04T15:23:00"
    }
  ]
}
```

---

### ✅ 1.3 订单详情

```http
GET /api/orders/{order_id}
```

#### 🔸 Response

```json
{
  "order_id": "123456",
  "channel": "woocommerce",
  "status": "label_failed",
  "items": [
    {
      "sku": "ABC-001",
      "name": "T-Shirt",
      "quantity": 2
    }
  ],
  "shipping_address": {
    "country": "DE",
    "city": "Berlin",
    "postcode": "10115",
    "address_line1": "Sample St 1"
  },
  "logs": [
    {
      "timestamp": "2025-10-04T15:30:00",
      "from_status": "waiting_labels",
      "to_status": "label_failed"
    }
  ]
}
```

---

# 🚚 2. **快递单处理模块**

### ✅ 2.1 批量生成快递单

```http
POST /api/orders/generate_labels
```

#### 🔸 Body

```json
{
  "order_ids": ["123456", "123457"]
}
```

#### 🔸 Response

```json
{
  "success": ["123456"],
  "failed": [
    {
      "order_id": "123457",
      "error": "Invalid address format"
    }
  ]
}
```

---

### ✅ 2.2 重试生成失败快递单

```http
POST /api/orders/{order_id}/retry_label
```

---

### ✅ 2.3 同步物流号到平台

```http
POST /api/orders/sync_tracking
```

#### 🔸 Body

```json
{
  "order_ids": ["123456", "123457"]
}
```

---

# 📄 3. **打包批次（Batch）模块**

### ✅ 3.1 创建打包批次（从 synced 订单）

```http
POST /api/batches/create
```

#### 🔸 Body

```json
{
  "channel": "woocommerce",
  "seller_id": "store_abc"
}
```

#### 🔸 Response

```json
{
  "batch_id": "BATCH_woocommerce_20251005_003",
  "order_count": 30
}
```

---

### ✅ 3.2 查看所有批次

```http
GET /api/batches
```

#### 🔸 Response

```json
[
  {
    "batch_id": "BATCH_woocommerce_20251005_003",
    "status": "uploaded",
    "order_count": 30,
    "file_url": "https://cdn.example.com/batch/BATCH_xxx.zip",
    "created_at": "2025-10-05T10:00:00"
  }
]
```

---

### ✅ 3.3 下载打印资料 ZIP

```http
GET /api/batches/{batch_id}/download
```

📎 返回 `application/zip` 文件流

---

# 🔐 4. **凭证管理接口**

### ✅ 4.1 查询所有凭证

```http
GET /api/credentials
```

#### 🔸 Response

```json
[
  {
    "id": 1,
    "type": "order_channel",
    "provider_code": "woocommerce",
    "external_id": "store_abc",
    "is_active": true,
    "created_at": "2025-10-01T12:00:00"
  }
]
```

---

### ✅ 4.2 添加 / 更新凭证

```http
POST /api/credentials
```

```json
{
  "type": "logistics",
  "provider_code": "dhl",
  "external_id": "dhl_account_x",
  "api_key": "xxx",
  "api_secret": "yyy"
}
```

---

# 🚨 5. **异常与日志中心**

### ✅ 5.1 查询异常订单

```http
GET /api/orders/failed
```

#### 🔸 可按 step、error_type、时间筛选

---

### ✅ 5.2 查看某订单的异常记录

```http
GET /api/orders/{order_id}/errors
```

---

### ✅ 5.3 状态流转日志

```http
GET /api/orders/{order_id}/logs
```

---

# 📊 6. **统计与仪表盘（可选）**

```http
GET /api/dashboard/summary
```

```json
{
  "total_orders_today": 150,
  "pending_labels": 25,
  "label_failed": 3,
  "synced_not_batched": 18,
  "batches_today": 4
}
```

---

# ✅ 补充说明

| 技术点         | 说明                                       |
| ----------- | ---------------------------------------- |
| Auth / 权限控制 | 可以用 token / JWT 区分权限角色                   |
| 错误格式统一      | 推荐统一错误结构：`{"error": "...", "code": 400}` |
| 文档工具推荐      | 可用 Swagger UI（FastAPI 默认支持）生成 API 文档     |

---

## ✅ 如果你需要：

* 我来直接写这些接口的 FastAPI 控制器
* 生成 Swagger 自动文档
* 设计接口权限模型（角色分级）

告诉我「继续哪一块」，我可以马上给出下一步代码实现 ✅

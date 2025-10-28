# n8n 查询问题解决方案

## 问题诊断

### ✅ Flask 服务本身是正常的

通过 Python 测试,Flask 服务能正确返回数据:

```json
{
  "count": 1,
  "data": [{ ... 完整的数据 ... }],
  "success": true
}
```

### ❌ n8n 中查询返回空数据

```json
{
  "count": 0,
  "data": [],
  "success": true
}
```

## 问题原因分析

### 最可能的原因:n8n 请求参数格式问题

在 n8n 的 HTTP Request 节点中,`params` 数组中的数字可能被转换成了字符串或其他格式。

## 解决方案

### 方案1:在 n8n 中使用表达式确保数字类型

**HTTP Request 节点配置:**

```
Method: POST
URL: http://localhost:5000/db/query
Body Content Type: JSON
```

**Body (使用 JSON 模式):**

```json
{
  "db_path": "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
  "sql": "SELECT * FROM douyin_aweme where aweme_id =? ",
  "params": [{{ 7554322613938523407 }}]
}
```

**或者使用表达式模式:**

```javascript
{
  "db_path": "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
  "sql": "SELECT * FROM douyin_aweme where aweme_id =? ",
  "params": [Number(7554322613938523407)]
}
```

### 方案2:在 n8n 中添加 Code 节点预处理

**节点1: Code (准备请求数据)**

```javascript
return [
  {
    json: {
      db_path: "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
      sql: "SELECT * FROM douyin_aweme where aweme_id =? ",
      params: [7554322613938523407]  // 直接使用数字
    }
  }
];
```

**节点2: HTTP Request**

```
Method: POST
URL: http://localhost:5000/db/query
Body Content Type: JSON
Body: {{ $json }}
```

### 方案3:修改 SQL 使用字符串比较(临时方案)

如果上述方法都不行,可以临时修改 SQL:

```json
{
  "db_path": "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
  "sql": "SELECT * FROM douyin_aweme where CAST(aweme_id AS TEXT) = ?",
  "params": ["7554322613938523407"]
}
```

## n8n 调试步骤

### 1. 检查实际发送的请求

在 HTTP Request 节点后添加一个 **Code 节点**:

```javascript
// 查看实际发送的请求
console.log('Request Body:', $input.first().json.body);
console.log('Params Type:', typeof $input.first().json.body.params[0]);
console.log('Params Value:', $input.first().json.body.params[0]);

return $input.all();
```

### 2. 查看 Flask 服务日志

在 Flask 服务端添加日志,查看接收到的参数:

```python
@app.route('/db/query', methods=['POST'])
def query_db():
    data = request.json
    print(f"收到的参数: {data}")
    print(f"params 类型: {type(data['params'][0])}")
    print(f"params 值: {data['params'][0]}")
    # ... 其他代码
```

### 3. 使用 n8n 的 Webhook 测试

创建一个简单的测试流程:

**节点1: Webhook**

```
Method: POST
Path: /test-query
```

**节点2: Code**

```javascript
// 准备测试数据
return [{
  json: {
    db_path: "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
    sql: "SELECT * FROM douyin_aweme where aweme_id = ?",
    params: [7554322613938523407]
  }
}];
```

**节点3: HTTP Request**

```
Method: POST
URL: http://localhost:5000/db/query
Body: {{ $json }}
```

**节点4: Respond to Webhook**

```javascript
return [{
  json: {
    request_params: $('Code').first().json,
    response: $json
  }
}];
```

然后用 Postman 或 curl 触发这个 webhook,查看完整的请求和响应。

## 常见的 n8n 参数问题

### 问题1: 数字被转为字符串

```javascript
// ❌ 错误
{
  "params": ["7554322613938523407"]  // 字符串
}

// ✅ 正确
{
  "params": [7554322613938523407]  // 数字
}
```

### 问题2: 使用了 n8n 表达式但没有正确求值

```javascript
// ❌ 错误 - 字符串形式的表达式
{
  "params": ["{{ $json.aweme_id }}"]  // 可能是字符串
}

// ✅ 正确 - 使用 Number() 转换
{
  "params": [{{ Number($json.aweme_id) }}]
}
```

### 问题3: JSON 编辑器的引号问题

在 n8n 的 JSON 编辑器中:

- 数字不要加引号: `7554322613938523407`
- 字符串要加引号: `"some_string"`

## 推荐的 n8n 工作流配置

### 完整示例工作流

```json
{
  "nodes": [
    {
      "name": "准备查询参数",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "return [{\n  json: {\n    db_path: \"O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db\",\n    sql: \"SELECT * FROM douyin_aweme where aweme_id = ?\",\n    params: [7554322613938523407]\n  }\n}];"
      }
    },
    {
      "name": "查询数据库",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://localhost:5000/db/query",
        "jsonParameters": true,
        "options": {},
        "bodyParametersJson": "={{ $json }}"
      }
    },
    {
      "name": "处理结果",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// 检查查询结果\nconst result = $input.first().json;\n\nif (result.success && result.count > 0) {\n  // 返回查询到的数据\n  return result.data.map(item => ({ json: item }));\n} else {\n  throw new Error(`查询失败或无数据: count=${result.count}`);\n}"
      }
    }
  ]
}
```

## 关于 n8n 的 "Split Out" 提示

你看到的这个提示:
> To split the contents of 'data' into separate items for easier processing, add a 'Split Out' node after this one

**这不是错误!** 这是 n8n 的一个建议提示,意思是:

- 你的返回数据是一个包含 `data` 数组的对象
- n8n 建议你使用 "Split Out" 节点将数组中的每一项分离成独立的项目
- 这样后续节点可以逐个处理每条记录

### 如何使用 Split Out

如果你想处理查询结果中的每一条记录:

**添加 Split Out 节点:**

```
Field to Split Out: data
```

这样,如果查询返回 3 条记录,Split Out 会将它们分成 3 个独立的项目,后续节点可以分别处理。

## 总结

1. **Flask 服务是正常的** - 能正确返回数据
2. **问题在 n8n 的请求配置** - 参数类型可能不对
3. **解决方法**:
   - 使用 Code 节点准备请求数据,确保数字类型
   - 检查 n8n 的 JSON 编辑器中数字没有被加引号
   - 使用表达式时用 `Number()` 确保类型正确
4. **"Split Out" 提示不是错误** - 只是一个优化建议

## 快速测试

在 n8n 中创建这个简单的测试流程:

```javascript
// Code 节点
return [{
  json: {
    db_path: "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
    sql: "SELECT COUNT(*) as total FROM douyin_aweme",
    params: []
  }
}];
```

先测试一个不需要参数的查询,确认连接正常,然后再测试带参数的查询。

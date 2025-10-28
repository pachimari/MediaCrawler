# 大整数精度问题完整解决方案

## 问题根源

### JavaScript 数字精度限制

- **JavaScript 安全整数范围**: `-9,007,199,254,740,991` 到 `9,007,199,254,740,991` (即 ±2^53-1)
- **你的 aweme_id**: `7,554,322,613,938,523,407` ✗ **超出安全范围**
- **结果**: 在 JSON 传输过程中精度丢失
  - 数据库中: `7554322613938523407` ✓
  - n8n/JavaScript 中: `7554322613938523000` ✗ (丢失了末尾的 `407`)

### 为什么会发生

```
数据库(SQLite BIGINT) → Flask(Python int) → JSON 序列化 → n8n(JavaScript Number)
                                                              ↑
                                                        精度在这里丢失!
```

## 解决方案

### 方案1: 修改 Flask 服务(推荐)

修改 Flask 服务,将大整数字段转为字符串返回:

```python
# 在 Flask 服务的 /db/query 路由中
@app.route('/db/query', methods=['POST'])
def query_db():
    data = request.json
    db_path = data.get('db_path')
    sql = data.get('sql')
    params = data.get('params', [])
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(sql, params)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # 关键修改:将大整数字段转为字符串
    bigint_fields = ['aweme_id', 'user_id', 'comment_id', 'video_id', 
                     'note_id', 'create_time', 'add_ts', 'last_modify_ts']
    
    result = []
    for row in rows:
        row_dict = {}
        for col, value in zip(columns, row):
            # 如果是大整数字段,转为字符串
            if col in bigint_fields and isinstance(value, int):
                row_dict[col] = str(value)
            else:
                row_dict[col] = value
        result.append(row_dict)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'count': len(result),
        'data': result,
        'db_path': db_path
    })
```

### 方案2: 在 n8n 中使用字符串查询(快速方案)

不修改 Flask 服务,直接在 n8n 中使用字符串类型:

```javascript
// n8n Code 节点
return [{
  json: {
    db_path: "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
    sql: "SELECT * FROM douyin_aweme WHERE CAST(aweme_id AS TEXT) = ?",
    params: ["7554322613938523407"]  // 使用字符串
  }
}];
```

或者直接在 SQL 中硬编码:

```javascript
return [{
  json: {
    db_path: "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
    sql: "SELECT * FROM douyin_aweme WHERE aweme_id = 7554322613938523407",
    params: []  // 不使用参数
  }
}];
```

### 方案3: 使用 Python 脚本代替 n8n HTTP 请求

在 n8n 中使用 Execute Command 节点直接运行 Python 脚本:

```python
# query_aweme.py
import sqlite3
import json
import sys

aweme_id = sys.argv[1]
db_path = "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT * FROM douyin_aweme WHERE aweme_id = ?", (aweme_id,))
columns = [desc[0] for desc in cursor.description]
row = cursor.fetchone()

if row:
    result = dict(zip(columns, row))
    # 将大整数转为字符串
    for key in ['aweme_id', 'user_id', 'create_time', 'add_ts', 'last_modify_ts']:
        if key in result and isinstance(result[key], int):
            result[key] = str(result[key])
    print(json.dumps(result, ensure_ascii=False))
else:
    print(json.dumps({"error": "Not found"}))

conn.close()
```

在 n8n 中:

```bash
python O:\ai\2025AIAgent\MediaCrawler\query_aweme.py 7554322613938523407
```

## 推荐的完整解决流程

### 步骤1: 修改 Flask 服务

找到你的 Flask 服务代码,添加大整数字段的字符串转换逻辑。

### 步骤2: 在 n8n 中测试

```javascript
// Code 节点
return [{
  json: {
    db_path: "O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db",
    sql: "SELECT * FROM douyin_aweme WHERE aweme_id = ?",
    params: ["7554322613938523407"]  // 现在使用字符串
  }
}];
```

### 步骤3: 处理返回的字符串 ID

在后续的 n8n 节点中,`aweme_id` 现在是字符串类型:

```javascript
// 如果需要比较
const awemeId = $json.aweme_id;  // "7554322613938523407"

// 如果需要用于 URL
const url = `https://www.douyin.com/video/${awemeId}`;
```

## 验证方案

### 测试1: 直接在数据库中查询

```sql
-- 使用字符串比较
SELECT * FROM douyin_aweme WHERE CAST(aweme_id AS TEXT) = '7554322613938523407';

-- 或者直接使用数字(在 SQLite 中可以)
SELECT * FROM douyin_aweme WHERE aweme_id = 7554322613938523407;
```

### 测试2: 在 Python 中测试

```python
import sqlite3

conn = sqlite3.connect("O:/ai/2025AIAgent/MediaCrawler/database/sqlite_tables.db")
cursor = conn.cursor()

# 测试1: 使用整数
cursor.execute("SELECT aweme_id FROM douyin_aweme WHERE aweme_id = ?", (7554322613938523407,))
print("整数查询:", cursor.fetchone())

# 测试2: 使用字符串
cursor.execute("SELECT aweme_id FROM douyin_aweme WHERE aweme_id = ?", ("7554322613938523407",))
print("字符串查询:", cursor.fetchone())

# 测试3: 使用 CAST
cursor.execute("SELECT aweme_id FROM douyin_aweme WHERE CAST(aweme_id AS TEXT) = ?", ("7554322613938523407",))
print("CAST 查询:", cursor.fetchone())

conn.close()
```

### 测试3: 在 n8n 中测试

创建测试工作流:

1. **Code 节点** - 准备三种不同的查询方式
2. **HTTP Request 节点** - 分别测试
3. **Code 节点** - 比较结果

## 其他受影响的字段

除了 `aweme_id`,以下字段也可能受影响:

- `user_id`
- `comment_id`
- `video_id`
- `note_id`
- `create_time` (时间戳)
- `add_ts` (时间戳)
- `last_modify_ts` (时间戳)

建议在 Flask 服务中统一处理所有大整数字段。

## 长期解决方案

### 1. 数据库设计层面

在创建表时使用 `TEXT` 类型存储大整数:

```sql
CREATE TABLE douyin_aweme (
    id INTEGER PRIMARY KEY,
    aweme_id TEXT NOT NULL,  -- 使用 TEXT 而不是 BIGINT
    ...
);
```

### 2. API 设计层面

在 API 文档中明确说明:

- 所有 ID 字段都以字符串形式返回
- 客户端应该将 ID 视为不透明字符串,不进行数学运算

### 3. 前端处理层面

在 JavaScript/TypeScript 中:

```javascript
// 使用 BigInt (ES2020+)
const awemeId = BigInt("7554322613938523407");

// 或者始终作为字符串处理
const awemeId = "7554322613938523407";
```

## 总结

**问题**: JavaScript 数字精度限制导致大整数在 JSON 传输中丢失精度

**快速解决**: 在 n8n 中使用字符串类型的参数

```javascript
{
  "sql": "SELECT * FROM douyin_aweme WHERE CAST(aweme_id AS TEXT) = ?",
  "params": ["7554322613938523407"]
}
```

**最佳解决**: 修改 Flask 服务,将所有大整数字段转为字符串返回

**验证方法**:

1. 检查返回的 `aweme_id` 是否完整(末尾是 `407` 而不是 `000`)
2. 使用字符串类型的 ID 进行查询
3. 确保所有 ID 字段都作为字符串处理

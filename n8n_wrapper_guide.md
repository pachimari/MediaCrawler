# n8n_crawler_wrapper.py 使用指南

## 📖 简介

`n8n_crawler_wrapper.py` 是一个不修改原项目代码的包装器脚本，允许通过命令行动态配置抖音爬虫参数，特别适合在 n8n 等自动化工具中使用。

## ✨ 核心特性

- ✅ **动态配置视频ID** - 无需手动修改配置文件
- ✅ **动态配置评论数量** - 灵活控制爬取数据量
- ✅ **自动备份恢复** - 执行前自动备份配置，执行后自动恢复
- ✅ **支持三种爬取模式** - detail(视频详情) / creator(创作者) / search(搜索)
- ✅ **完整参数支持** - 支持所有主要爬虫参数
- ✅ **Dry-run 模式** - 可以先测试配置而不实际执行

---

## 🚀 快速开始

### 1. 基础用法

#### 爬取指定视频的评论（detail 模式）

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407,7280854932641664319" \
  --comment-count 100 \
  --save-option sqlite
```

#### 爬取创作者主页（creator 模式）

```bash
python n8n_crawler_wrapper.py \
  --type creator \
  --creator-ids "MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE" \
  --comment-count 50
```

#### 关键词搜索（search 模式）

```bash
python n8n_crawler_wrapper.py \
  --type search \
  --keywords "Python教程,AI工具" \
  --comment-count 30
```

---

## 📋 完整参数说明

### 爬取目标参数

| 参数 | 说明 | 示例 | 适用模式 |
|------|------|------|----------|
| `--video-ids` | 视频ID列表（逗号分隔） | `"7554322613938523407,7280..."` | detail |
| `--creator-ids` | 创作者ID列表（逗号分隔） | `"MS4wLjABAAAA..."` | creator |
| `--keywords` | 搜索关键词（逗号分隔） | `"Python,编程"` | search |

### 爬取配置参数

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `--type` | 爬取类型 | `detail` | `detail` / `creator` / `search` |
| `--comment-count` | 每个视频的评论数量 | `10` | 任意正整数 |
| `--sub-comment` | 是否爬取二级评论 | `0` | `0`(否) / `1`(是) |
| `--save-option` | 数据保存方式 | `sqlite` | `sqlite` / `json` / `csv` / `db` |
| `--login-type` | 登录方式 | `qrcode` | `qrcode` / `phone` / `cookie` |
| `--cookies` | Cookie字符串 | 空 | Cookie 字符串 |

### 特殊参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 仅更新配置，不执行爬虫（用于测试） |
| `--keep-config` | 保留修改后的配置，不自动恢复 |
| `--help` | 显示帮助信息 |

---

## 💡 实际使用示例

### 示例1：爬取单个视频的100条评论

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --save-option sqlite
```

### 示例2：爬取多个视频，包含二级评论

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407,7280854932641664319,7202432992642387233" \
  --comment-count 50 \
  --sub-comment 1 \
  --save-option json
```

### 示例3：使用 Cookie 登录爬取

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --login-type cookie \
  --cookies "your_cookie_string_here"
```

### 示例4：关键词搜索并保存为CSV

```bash
python n8n_crawler_wrapper.py \
  --type search \
  --keywords "AI工具,ChatGPT,编程" \
  --comment-count 30 \
  --save-option csv
```

### 示例5：先测试配置（不实际执行）

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --dry-run
```

---

## 🔧 n8n 集成配置

### 方案A：简单直接调用（推荐）

#### 节点配置示例

**节点1: Set（设置参数）**

```javascript
// 动态设置爬取参数
return [
  {
    json: {
      video_ids: "7554322613938523407,7280854932641664319",
      comment_count: 100,
      sub_comment: 0,
      save_option: "sqlite"
    }
  }
];
```

**节点2: Execute Command（执行爬虫）**

```bash
cd O:\ai\2025AIAgent\MediaCrawler

python n8n_crawler_wrapper.py --video-ids "{{ $json.video_ids }}" --comment-count {{ $json.comment_count }} --sub-comment {{ $json.sub_comment }} --save-option {{ $json.save_option }}
```

**节点3: Code（读取结果 - SQLite）**

```javascript
// 读取 SQLite 数据库结果
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

const dbPath = 'O:\\ai\\2025AIAgent\\MediaCrawler\\database\\sqlite_tables.db';
const query = `SELECT * FROM douyin_aweme_comment ORDER BY id DESC LIMIT ${$input.item.json.comment_count}`;

const { stdout } = await execPromise(`sqlite3 "${dbPath}" "${query}" -json`);

return JSON.parse(stdout);
```

---

### 方案B：使用 HTTP Request 触发

如果你想通过 HTTP 请求触发爬虫：

**节点1: Webhook（接收请求）**

```
Method: POST
Path: /crawl-douyin
```

**节点2: Code（参数验证）**

```javascript
// 验证必要参数
const body = $input.item.json.body;

if (!body.video_ids) {
  throw new Error('缺少必要参数: video_ids');
}

return {
  json: {
    video_ids: body.video_ids,
    comment_count: body.comment_count || 10,
    sub_comment: body.sub_comment || 0,
    save_option: body.save_option || 'sqlite',
    login_type: body.login_type || 'qrcode'
  }
};
```

**节点3: Execute Command（执行爬虫）**

```bash
cd O:\ai\2025AIAgent\MediaCrawler

python n8n_crawler_wrapper.py \
  --video-ids "{{ $json.video_ids }}" \
  --comment-count {{ $json.comment_count }} \
  --sub-comment {{ $json.sub_comment }} \
  --save-option {{ $json.save_option }} \
  --login-type {{ $json.login_type }}
```

**节点4: Respond to Webhook（返回结果）**

```javascript
return {
  json: {
    success: true,
    message: "爬虫任务已完成",
    params: $input.item.json
  }
};
```

---

### 方案C：定时任务 + 动态配置

**节点1: Schedule Trigger（定时触发）**

```
Cron Expression: 0 9 * * *  # 每天早上9点
```

**节点2: HTTP Request（获取待爬取视频列表）**

```
Method: GET
URL: https://your-api.com/get-video-list
```

**节点3: Code（处理视频列表）**

```javascript
// 将API返回的视频列表转换为逗号分隔的字符串
const videos = $input.item.json.videos;
const videoIds = videos.map(v => v.id).join(',');

return {
  json: {
    video_ids: videoIds,
    comment_count: 100
  }
};
```

**节点4: Execute Command（执行爬虫）**

```bash
cd O:\ai\2025AIAgent\MediaCrawler

python n8n_crawler_wrapper.py \
  --video-ids "{{ $json.video_ids }}" \
  --comment-count {{ $json.comment_count }} \
  --save-option sqlite
```

**节点5: Code（读取并发送结果）**

```javascript
// 读取爬取结果并发送通知
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

const dbPath = 'O:\\ai\\2025AIAgent\\MediaCrawler\\database\\sqlite_tables.db';
const query = `SELECT COUNT(*) as count FROM douyin_aweme_comment WHERE DATE(create_time) = DATE('now')`;

const { stdout } = await execPromise(`sqlite3 "${dbPath}" "${query}"`);

return {
  json: {
    message: `今日爬取评论数: ${stdout.trim()}`,
    timestamp: new Date().toISOString()
  }
};
```

---

## 🎯 完整 n8n 工作流示例

### 场景：每天爬取热门视频评论

```json
{
  "name": "抖音爬虫自动化",
  "nodes": [
    {
      "name": "每天早上9点触发",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
        }
      }
    },
    {
      "name": "设置爬取参数",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {"name": "video_ids", "value": "7554322613938523407,7280854932641664319"},
            {"name": "save_option", "value": "sqlite"}
          ],
          "number": [
            {"name": "comment_count", "value": 100}
          ]
        }
      }
    },
    {
      "name": "执行爬虫",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "cd O:\\ai\\2025AIAgent\\MediaCrawler && python n8n_crawler_wrapper.py --video-ids \"{{ $json.video_ids }}\" --comment-count {{ $json.comment_count }} --save-option {{ $json.save_option }}"
      }
    },
    {
      "name": "读取结果统计",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const { exec } = require('child_process');\nconst util = require('util');\nconst execPromise = util.promisify(exec);\n\nconst dbPath = 'O:\\\\ai\\\\2025AIAgent\\\\MediaCrawler\\\\database\\\\sqlite_tables.db';\nconst query = `SELECT COUNT(*) as count FROM douyin_aweme_comment WHERE DATE(create_time) = DATE('now')`;\n\nconst { stdout } = await execPromise(`sqlite3 \"${dbPath}\" \"${query}\"`);\n\nreturn [{json: {count: parseInt(stdout.trim()), date: new Date().toISOString()}}];"
      }
    },
    {
      "name": "发送通知",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://your-webhook.com/notify",
        "jsonParameters": true,
        "bodyParametersJson": "={\"message\": \"今日爬取评论数: \" + $json.count, \"status\": \"success\"}"
      }
    }
  ]
}
```

---

## 📊 数据读取示例

### 从 SQLite 读取最新评论

```bash
# 命令行方式
sqlite3 database/sqlite_tables.db \
  "SELECT * FROM douyin_aweme_comment ORDER BY create_time DESC LIMIT 10" \
  -json
```

### 从 JSON 文件读取

```bash
# 查看最新的 JSON 文件
ls -lt data/douyin/json/ | head -5

# 读取 JSON 文件
cat data/douyin/json/comment_*.json
```

### 使用 Python 读取

```python
import sqlite3
import json
from pathlib import Path

# 读取 SQLite
db_path = "database/sqlite_tables.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT * FROM douyin_aweme_comment 
    WHERE DATE(create_time) = DATE('now')
    ORDER BY create_time DESC
    LIMIT 100
""")

results = cursor.fetchall()
print(f"今日爬取评论数: {len(results)}")

conn.close()
```

---

## ⚠️ 注意事项

### 1. 配置文件备份

- 脚本会自动备份并恢复配置文件
- 备份文件命名格式: `*.py.bak_20250117_143025`
- 使用 `--keep-config` 可保留配置不恢复

### 2. 评论数量限制

- 建议单次不超过 500 条评论
- 数量过大可能触发平台限流
- 可以通过多次小批量爬取规避

### 3. 登录方式选择

- `qrcode`: 每次扫码（最安全）
- `cookie`: 复用登录态（便捷，但可能失效）
- `phone`: 手机号登录（需要额外配置）

### 4. 数据保存位置

- **SQLite**: `database/sqlite_tables.db`
- **JSON**: `data/douyin/json/`
- **CSV**: `data/douyin/csv/`

### 5. 执行环境

- 确保在项目根目录执行
- 需要已安装 `uv` 和相关依赖
- Windows 环境建议使用 PowerShell

---

## 🐛 故障排查

### 问题1: 找不到配置文件

```
❌ 错误: 配置文件不存在！
```

**解决方案**: 确保在项目根目录执行脚本

```bash
cd O:\ai\2025AIAgent\MediaCrawler
python n8n_crawler_wrapper.py --help
```

### 问题2: 参数缺失

```
error: --type detail 需要提供 --video-ids 参数
```

**解决方案**: 根据爬取类型提供对应参数

- `detail` 需要 `--video-ids`
- `creator` 需要 `--creator-ids`
- `search` 需要 `--keywords`

### 问题3: 爬虫执行失败

```
❌ 爬虫执行失败，退出码: 1
```

**解决方案**:

1. 检查登录状态是否有效
2. 查看终端输出的详细错误信息
3. 使用 `--dry-run` 测试配置是否正确
4. 检查视频ID是否有效

---

## 📚 更多资源

- [MediaCrawler 项目文档](https://nanmicoder.github.io/MediaCrawler/)
- [n8n 官方文档](https://docs.n8n.io/)
- [SQLite 使用指南](https://www.sqlite.org/docs.html)

---

## 🎉 快速测试

运行以下命令进行快速测试：

```bash
# 1. 测试配置（不实际执行）
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 10 \
  --dry-run

# 2. 实际爬取少量数据测试
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 5 \
  --save-option json

# 3. 查看结果
ls -lt data/douyin/json/
```

---

**祝你使用愉快！** 🚀

如有问题，请参考主项目文档或提交 Issue。

# 🚀 n8n 集成包装器 - 快速开始

本目录包含了用于 n8n 集成的所有必要文件，可以在不修改原项目代码的情况下动态配置抖音爬虫参数。

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `n8n_crawler_wrapper.py` | **核心包装器脚本**，用于动态配置和执行爬虫 |
| `n8n_wrapper_guide.md` | **完整使用文档**，包含详细的参数说明和 n8n 配置示例 |
| `n8n_douyin_crawler_workflow.json` | **n8n 工作流配置**，可直接导入 n8n |
| `test_n8n_wrapper.bat` | Windows 测试脚本 |
| `test_n8n_wrapper.sh` | Linux/Mac 测试脚本 |

---

## ⚡ 快速开始（3步搞定）

### 第1步：测试包装器脚本

**Windows:**

```bash
test_n8n_wrapper.bat
```

**Linux/Mac:**

```bash
chmod +x test_n8n_wrapper.sh
./test_n8n_wrapper.sh
```

### 第2步：手动测试单次爬取

```bash
# 爬取指定视频的100条评论
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --save-option sqlite
```

### 第3步：在 n8n 中使用

#### 方式A：直接使用 Execute Command 节点

```bash
cd O:\ai\2025AIAgent\MediaCrawler

python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407,7280854932641664319" \
  --comment-count 100 \
  --save-option sqlite
```

#### 方式B：导入预配置工作流

1. 打开 n8n
2. 点击"导入工作流"
3. 选择 `n8n_douyin_crawler_workflow.json`
4. 修改"设置爬取参数"节点中的参数
5. 执行工作流

---

## 📖 核心功能

### ✅ 支持的爬取模式

| 模式 | 说明 | 必需参数 |
|------|------|----------|
| `detail` | 爬取指定视频 | `--video-ids` |
| `creator` | 爬取创作者主页 | `--creator-ids` |
| `search` | 关键词搜索 | `--keywords` |

### 🎯 核心参数

```bash
--video-ids "视频ID1,视频ID2"     # 视频ID列表（逗号分隔）
--comment-count 100                # 每个视频爬取的评论数
--sub-comment 1                    # 是否爬二级评论 (0/1)
--save-option sqlite               # 保存方式 (sqlite/json/csv/db)
--login-type qrcode                # 登录方式 (qrcode/cookie/phone)
```

---

## 💡 实际使用示例

### 示例1：爬取单个视频

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --save-option sqlite
```

### 示例2：爬取多个视频（含二级评论）

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407,7280854932641664319" \
  --comment-count 50 \
  --sub-comment 1 \
  --save-option json
```

### 示例3：使用 Cookie 登录

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --login-type cookie \
  --cookies "你的cookie字符串"
```

### 示例4：关键词搜索

```bash
python n8n_crawler_wrapper.py \
  --type search \
  --keywords "Python教程,AI工具" \
  --comment-count 30
```

### 示例5：测试配置（不实际执行）

```bash
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 100 \
  --dry-run
```

---

## 🔧 n8n 集成示例

### 基础工作流

```
[触发器] → [设置参数] → [执行爬虫] → [读取结果] → [处理数据]
```

### Execute Command 节点配置

```bash
cd O:\ai\2025AIAgent\MediaCrawler

python n8n_crawler_wrapper.py \
  --video-ids "{{ $json.video_ids }}" \
  --comment-count {{ $json.comment_count }} \
  --save-option {{ $json.save_option }}
```

### 从 n8n 传递参数

在 n8n 的 **Set 节点**中：

```javascript
{
  "video_ids": "7554322613938523407,7280854932641664319",
  "comment_count": 100,
  "sub_comment": 0,
  "save_option": "sqlite"
}
```

---

## 📊 数据读取

### 查询 SQLite 数据库

```bash
# 查看今日爬取的评论数
sqlite3 database/sqlite_tables.db \
  "SELECT COUNT(*) FROM douyin_aweme_comment WHERE DATE(create_time) = DATE('now')"

# 查看最新10条评论
sqlite3 database/sqlite_tables.db \
  "SELECT * FROM douyin_aweme_comment ORDER BY create_time DESC LIMIT 10" \
  -json
```

### 在 n8n 中读取数据

**Code 节点示例：**

```javascript
const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

const dbPath = 'O:\\ai\\2025AIAgent\\MediaCrawler\\database\\sqlite_tables.db';
const query = `SELECT * FROM douyin_aweme_comment ORDER BY create_time DESC LIMIT 100`;

const { stdout } = await execPromise(`sqlite3 "${dbPath}" "${query}" -json`);

return JSON.parse(stdout);
```

---

## ⚙️ 高级配置

### 定时任务示例

在 n8n 中使用 **Schedule Trigger**：

```
Cron: 0 9 * * *  # 每天早上9点
```

然后连接到执行爬虫节点。

### Webhook 触发示例

1. 添加 **Webhook 节点**
2. 设置为 POST 方法
3. 路径：`/crawl-douyin`
4. 在后续节点中使用 `$json.body.video_ids`

调用示例：

```bash
curl -X POST http://your-n8n.com/webhook/crawl-douyin \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": "7554322613938523407",
    "comment_count": 100
  }'
```

---

## 🐛 故障排查

### 问题1：找不到配置文件

```
❌ 错误: 配置文件不存在！
```

**解决方案**：确保在项目根目录执行

```bash
cd O:\ai\2025AIAgent\MediaCrawler
python n8n_crawler_wrapper.py --help
```

### 问题2：参数缺失

```
error: --type detail 需要提供 --video-ids 参数
```

**解决方案**：根据爬取类型提供对应参数

- `detail` → 需要 `--video-ids`
- `creator` → 需要 `--creator-ids`
- `search` → 需要 `--keywords`

### 问题3：爬虫执行失败

**解决方案**：

1. 使用 `--dry-run` 测试配置
2. 检查视频ID是否有效
3. 查看登录状态是否过期
4. 降低评论数量重试

---

## 📚 完整文档

查看 `n8n_wrapper_guide.md` 获取：

- 完整参数说明
- 详细的 n8n 配置示例
- 多种场景的工作流配置
- 数据处理和分析示例

---

## ⚠️ 注意事项

1. **评论数量**：建议单次不超过 500 条
2. **执行频率**：避免频繁请求，建议间隔 5-10 分钟
3. **登录状态**：Cookie 可能失效，需要重新登录
4. **配置备份**：脚本会自动备份并恢复配置文件
5. **数据去重**：使用 SQLite 可以自动去重

---

## 🎯 推荐使用流程

```
1. 先用 --dry-run 测试配置
   ↓
2. 小批量测试（5-10条评论）
   ↓
3. 验证数据是否正确
   ↓
4. 正式批量爬取
   ↓
5. 在 n8n 中配置自动化
```

---

## 🔗 相关链接

- [MediaCrawler 主项目](https://github.com/NanmiCoder/MediaCrawler)
- [n8n 官方文档](https://docs.n8n.io/)
- [Python argparse 文档](https://docs.python.org/zh-cn/3/library/argparse.html)

---

## 💬 获取帮助

```bash
# 查看所有参数说明
python n8n_crawler_wrapper.py --help

# 测试配置
python n8n_crawler_wrapper.py --video-ids "123" --comment-count 10 --dry-run
```

---

**祝你使用愉快！** 🎉

如有问题欢迎提 Issue 或查看完整文档。

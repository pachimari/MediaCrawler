#!/bin/bash
# 测试 n8n_crawler_wrapper.py

echo "========================================"
echo "测试 n8n_crawler_wrapper.py"
echo "========================================"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo "[测试 1/4] 显示帮助信息"
echo "----------------------------------------"
python n8n_crawler_wrapper.py --help
echo ""
echo ""

echo "[测试 2/4] Dry-run 模式测试（仅配置，不执行）"
echo "----------------------------------------"
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 10 \
  --dry-run
echo ""
echo ""

echo "[测试 3/4] 实际爬取测试（少量数据）"
echo "----------------------------------------"
echo "提示: 需要扫码登录"
echo ""
python n8n_crawler_wrapper.py \
  --video-ids "7554322613938523407" \
  --comment-count 5 \
  --save-option json
echo ""
echo ""

echo "[测试 4/4] 查看爬取结果"
echo "----------------------------------------"
if [ -d "data/douyin/json" ]; then
    echo "JSON 文件列表:"
    ls -lt data/douyin/json/*.json 2>/dev/null | head -5
    echo ""
    
    echo "最新的评论文件内容:"
    latest_file=$(ls -t data/douyin/json/comment*.json 2>/dev/null | head -1)
    if [ -n "$latest_file" ]; then
        cat "$latest_file"
    else
        echo "未找到评论文件"
    fi
else
    echo "未找到 JSON 数据目录"
fi
echo ""

echo "========================================"
echo "测试完成！"
echo "========================================"
echo ""
echo "如果需要在 n8n 中使用，参考命令:"
echo "python n8n_crawler_wrapper.py --video-ids \"视频ID\" --comment-count 100 --save-option sqlite"
echo ""


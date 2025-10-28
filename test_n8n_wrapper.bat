@echo off
chcp 65001 >nul
echo ========================================
echo 测试 n8n_crawler_wrapper.py
echo ========================================
echo.

REM 切换到项目目录
cd /d "%~dp0"

echo [测试 1/4] 显示帮助信息
echo ----------------------------------------
python n8n_crawler_wrapper.py --help
echo.
echo.

echo [测试 2/4] Dry-run 模式测试（仅配置，不执行）
echo ----------------------------------------
python n8n_crawler_wrapper.py ^
  --video-ids "7554322613938523407" ^
  --comment-count 10 ^
  --dry-run
echo.
echo.

echo [测试 3/4] 实际爬取测试（少量数据）
echo ----------------------------------------
echo 提示: 需要扫码登录
echo.
python n8n_crawler_wrapper.py ^
  --video-ids "7554322613938523407" ^
  --comment-count 5 ^
  --save-option json
echo.
echo.

echo [测试 4/4] 查看爬取结果
echo ----------------------------------------
if exist "data\douyin\json\" (
    echo JSON 文件列表:
    dir /b /o-d "data\douyin\json\*.json" | findstr /i "comment"
    echo.
    echo 最新的评论文件内容:
    for /f "delims=" %%f in ('dir /b /o-d "data\douyin\json\comment*.json" 2^>nul') do (
        type "data\douyin\json\%%f"
        goto :break
    )
    :break
) else (
    echo 未找到 JSON 数据文件
)
echo.

echo ========================================
echo 测试完成！
echo ========================================
echo.
echo 如果需要在 n8n 中使用，参考命令:
echo python n8n_crawler_wrapper.py --video-ids "视频ID" --comment-count 100 --save-option sqlite
echo.
pause


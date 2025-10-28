# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MediaCrawler is a multi-platform social media data collection tool that supports crawling public information from platforms like Xiaohongshu (Little Red Book), Douyin, Kuaishou, Bilibili, Weibo, Tieba, and Zhihu. The project uses Playwright for browser automation and maintains login states to access platform data without requiring JS reverse engineering.

## Development Commands

### Environment Setup (Recommended: uv)
```bash
# Install dependencies using uv (recommended)
uv sync

# Install browser drivers
uv run playwright install

# Alternative: Using traditional Python venv
pip install -r requirements.txt
playwright install
```

### Running the Crawler
```bash
# Basic usage - search by keywords
uv run main.py --platform xhs --lt qrcode --type search

# Get specific post details
uv run main.py --platform xhs --lt qrcode --type detail

# Initialize database
uv run main.py --init_db sqlite  # for SQLite
uv run main.py --init_db mysql   # for MySQL

# Run with data storage
uv run main.py --platform xhs --lt qrcode --type search --save_data_option sqlite
uv run main.py --platform xhs --lt qrcode --type search --save_data_option db  # for MySQL

# View all available options
uv run main.py --help
```

### Testing
```bash
# Run individual test files
uv run python test/test_db_sync.py
uv run python test/test_proxy_ip_pool.py
uv run python test/test_utils.py

# Run all tests (if pytest is configured)
uv run pytest
```

### N8N Integration Testing
```bash
# Test N8N wrapper functionality
./test_n8n_wrapper.sh  # Linux/Mac
test_n8n_wrapper.bat   # Windows
```

## Architecture Overview

### Core Components

1. **Main Entry Point (`main.py`)**
   - Uses `CrawlerFactory` to create platform-specific crawlers
   - Handles database initialization via `--init_db` parameter
   - Manages global crawler instance and cleanup

2. **Platform Abstraction (`base/base_crawler.py`)**
   - `AbstractCrawler` base class defines the crawling interface
   - Each platform implements this base class in `media_platform/`

3. **Platform Implementations (`media_platform/`)**
   - `xhs/` - Xiaohongshu crawler
   - `douyin/` - Douyin crawler
   - `kuaishou/` - Kuaishou crawler
   - `bilibili/` - Bilibili crawler
   - `weibo/` - Weibo crawler
   - `tieba/` - Tieba crawler
   - `zhihu/` - Zhihu crawler

4. **Configuration System (`config/`)**
   - `base_config.py` - Main configuration with platform selection and crawler settings
   - Platform-specific config files for each social media platform
   - Database configuration in `db_config.py`

5. **Data Storage (`store/`)**
   - Platform-specific storage implementations
   - Supports CSV, JSON, SQLite, and MySQL storage options
   - Async file writing capabilities

6. **Browser Automation (`tools/`)**
   - `browser_launcher.py` - Browser startup and management
   - `cdp_browser.py` - Chrome DevTools Protocol support for better stealth
   - `crawler_util.py` - Common crawler utilities

### Key Features

- **Login State Management**: Supports QR code, phone, and cookie-based login
- **IP Proxy Pool**: Configurable proxy support with multiple providers
- **Headless/Headed Mode**: Can run with or without browser UI
- **CDP Mode**: Chrome DevTools Protocol for better anti-detection
- **Comment Crawling**: Optional multi-level comment extraction
- **Data Export**: Multiple format support (CSV, JSON, SQLite, MySQL)

### Configuration Pattern

The project uses a centralized configuration system in `config/base_config.py`:
- `PLATFORM`: Target social media platform
- `KEYWORDS`: Search keywords for crawling
- `LOGIN_TYPE`: Authentication method (qrcode/phone/cookie)
- `CRAWLER_TYPE`: search/detail/creator
- `ENABLE_IP_PROXY`: Proxy usage flag
- `HEADLESS`: Browser visibility setting
- `ENABLE_CDP_MODE`: Chrome DevTools Protocol mode

### Database Schema

The project uses SQLAlchemy ORM with models in `database/models.py`. Key entities include:
- Posts/Notes information
- Comments data
- User/Creator information
- Interaction metrics (likes, shares, etc.)

### Anti-Detection Measures

- Playwright browser automation with stealth mode
- Optional CDP mode using user's existing browser
- Configurable request delays and retry logic
- User agent rotation and proxy support
- JS execution for signature generation

## Development Guidelines

### Platform Implementation
When adding new platform support:
1. Create new directory under `media_platform/`
2. Implement `AbstractCrawler` interface
3. Add configuration in `config/`
4. Create storage implementation in `store/`
5. Update `CrawlerFactory` in `main.py`

### Testing
- Test files are located in `test/` directory
- Focus on database operations, proxy functionality, and utility functions
- Use `uv run python` for consistent environment execution

### Configuration Management
- All platform-specific settings should go in respective config files
- Base configuration in `base_config.py` contains shared settings
- Use environment variables or config file modifications for different deployment scenarios

## Important Notes

- This project is for educational and research purposes only
- Respect platform terms of service and robots.txt
- Control request frequency to avoid platform disruption
- Some platforms may require manual verification (CAPTCHA) during initial login
- CDP mode requires Chrome/Edge browser to be installed and accessible
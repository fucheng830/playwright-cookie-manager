# Playwright Cookie Manager

Universal browser cookie/storage_state manager with pluggable backends. Provides CLI, MCP, and library interfaces.

## Installation

```bash
pip install playwright-cookie-manager
# With optional backends:
pip install playwright-cookie-manager[all]
```

## Usage

### Python Library

```python
from playwright_cookie_manager import CookieManager

mgr = CookieManager("data/cookies")

# Save cookies (from Playwright storage_state dict)
mgr.save("xhs", "account_1", storage_state_dict, nickname="MyAccount")

# Load cookies
data = mgr.load("xhs", "account_1")

# Use with Playwright
context = await browser.new_context(storage_state=data)

# List accounts
accounts = mgr.list("xhs")
# [{"platform": "xhs", "account_id": "account_1", "nickname": "MyAccount"}]

# Validate (checks for auth tokens)
valid = mgr.validate("xhs", "account_1")
```

### CLI

```bash
# Save cookies from file or stdin
cookie-manager save xhs account_1 --file cookies.json
cat cookies.json | cookie-manager save xhs account_1

# Load and export
cookie-manager load xhs account_1
cookie-manager export xhs account_1

# List all accounts for a platform
cookie-manager list xhs

# Delete an account
cookie-manager delete xhs account_1

# Interactive login (opens browser)
cookie-manager login xhs
```

### MCP Server

The package provides an MCP service entry point. Configure in your MCP client to run:

```
python -m playwright_cookie_manager.mcp
```

Available MCP tools: `save_cookie`, `load_cookie`, `list_cookies`, `delete_cookie`, `login_platform`.

## Supported Platforms

Built-in login URLs and auth token detectors for:
x, xhs (Xiaohongshu), douyin, kuaishou, bilibili, wechat

## Configuration via Environment Variables

```bash
# Database mode (wanxiang / any PostgreSQL)
export COOKIE_BACKEND=sql
export COOKIE_DB_URL=postgresql://postgresuser:postgrespass@192.168.0.17:5432/wanxiang
export COOKIE_DB_TABLE=platform_accounts

# File mode (default)
export COOKIE_BACKEND=file
export COOKIE_PATH=data/cookies
```

After setting env vars, all commands auto-detect configuration:

```bash
cookie-manager config    # Show current config
cookie-manager list      # Auto-uses DB or file based on env
cookie-manager login xhs # Auto-saves to configured backend
```

## Backends

- **file** (default): JSON files stored at `{base_path}/{platform}/{account_id}.json`
- **sql** (optional): SQLAlchemy-based (requires `sqlalchemy>=2.0`)
- **redis** (optional): Redis-based (requires `redis>=5.0`)

```python
mgr = CookieManager("sqlite:///cookies.db", backend="sql")
mgr = CookieManager("redis://localhost:6379", backend="redis")
```

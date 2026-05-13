"""MCP Server for cookie manager."""
import json, sys, asyncio, os
from .manager import CookieManager

MCP_SERVER_CODE = '''#!/usr/bin/env python3
"""MCP server for playwright-cookie-manager."""
import json, sys, asyncio
from playwright_cookie_manager import CookieManager

mgr = CookieManager()

async def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "tools": [
                {"name": "save_cookie", "description": "Save browser cookies for a platform account",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string"},
                     "cookie_data": {"type": "string", "description": "JSON string of Playwright storage_state"}
                 }, "required": ["platform", "account_id", "cookie_data"]}},
                {"name": "load_cookie", "description": "Load saved cookies for a platform account",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string"}
                 }, "required": ["platform", "account_id"]}},
                {"name": "list_cookies", "description": "List saved cookie accounts",
                 "inputSchema": {"type": "object", "properties": {"platform": {"type": "string"}}}},
                {"name": "delete_cookie", "description": "Delete a saved cookie account",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string"}
                 }, "required": ["platform", "account_id"]}},
                {"name": "login_platform", "description": "Open browser for user to login and save cookies",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string", "default": "default"}
                 }, "required": ["platform"]}},
            ]
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "save_cookie":
            mgr.save(args["platform"], args["account_id"], json.loads(args["cookie_data"]))
            return {"content": [{"type": "text", "text": f"Saved {args['platform']}/{args['account_id']}"}]}

        elif tool_name == "load_cookie":
            data = mgr.load(args["platform"], args["account_id"])
            return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False) if data else "Not found"}]}

        elif tool_name == "list_cookies":
            accounts = mgr.list(args.get("platform"))
            return {"content": [{"type": "text", "text": json.dumps(accounts, ensure_ascii=False, indent=2)}]}

        elif tool_name == "delete_cookie":
            mgr.delete(args["platform"], args["account_id"])
            return {"content": [{"type": "text", "text": f"Deleted {args['platform']}/{args['account_id']}"}]}

        elif tool_name == "login_platform":
            from playwright_cookie_manager.browser import login_platform
            state = await login_platform(args["platform"])
            mgr.save(args["platform"], args.get("account_id", "default"), state)
            return {"content": [{"type": "text", "text": f"Logged in: {args['platform']}"}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

    return {}

async def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            resp = await handle_request(req)
            if resp:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(str(e) + "\\n")
            sys.stderr.flush()

if __name__ == "__main__":
    asyncio.run(main())
'''


mgr = CookieManager()


async def handle_request(req: dict) -> dict:
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "tools/list":
        return {
            "tools": [
                {"name": "save_cookie", "description": "Save browser cookies for a platform account",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string"},
                     "cookie_data": {"type": "string", "description": "JSON string of Playwright storage_state"}
                 }, "required": ["platform", "account_id", "cookie_data"]}},
                {"name": "load_cookie", "description": "Load saved cookies for a platform account",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string"}
                 }, "required": ["platform", "account_id"]}},
                {"name": "list_cookies", "description": "List saved cookie accounts",
                 "inputSchema": {"type": "object", "properties": {"platform": {"type": "string"}}}},
                {"name": "delete_cookie", "description": "Delete a saved cookie account",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string"}
                 }, "required": ["platform", "account_id"]}},
                {"name": "login_platform", "description": "Open browser for user to login and save cookies",
                 "inputSchema": {"type": "object", "properties": {
                     "platform": {"type": "string"}, "account_id": {"type": "string", "default": "default"}
                 }, "required": ["platform"]}},
            ]
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "save_cookie":
            mgr.save(args["platform"], args["account_id"], json.loads(args["cookie_data"]))
            return {"content": [{"type": "text", "text": f"Saved {args['platform']}/{args['account_id']}"}]}

        elif tool_name == "load_cookie":
            data = mgr.load(args["platform"], args["account_id"])
            return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False) if data else "Not found"}]}

        elif tool_name == "list_cookies":
            accounts = mgr.list(args.get("platform"))
            return {"content": [{"type": "text", "text": json.dumps(accounts, ensure_ascii=False, indent=2)}]}

        elif tool_name == "delete_cookie":
            mgr.delete(args["platform"], args["account_id"])
            return {"content": [{"type": "text", "text": f"Deleted {args['platform']}/{args['account_id']}"}]}

        elif tool_name == "login_platform":
            from playwright_cookie_manager.browser import login_platform
            state = await login_platform(args["platform"])
            mgr.save(args["platform"], args.get("account_id", "default"), state)
            return {"content": [{"type": "text", "text": f"Logged in: {args['platform']}"}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

    return {}


def create_server():
    """Create an MCP server instance. Used by mcp.services entry point."""
    return sys.modules[__name__]


# Write MCP server as standalone file on first import
mcp_dir = os.path.dirname(__file__)
mcp_file = os.path.join(mcp_dir, "_mcp_server.py")
if not os.path.exists(mcp_file):
    with open(mcp_file, "w", encoding="utf-8") as f:
        f.write(MCP_SERVER_CODE)


async def _async_main():
    """Run the MCP server via stdin/stdout JSON-RPC."""
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            resp = await handle_request(req)
            if resp:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(str(e) + "\n")
            sys.stderr.flush()


if __name__ == "__main__":
    asyncio.run(_async_main())

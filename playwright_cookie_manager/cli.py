"""Command-line interface for cookie-manager."""
import argparse, json, asyncio, sys
from .manager import CookieManager


def main():
    parser = argparse.ArgumentParser(description="Playwright Cookie Manager")
    sub = parser.add_subparsers(dest="cmd")

    # Save
    p_save = sub.add_parser("save", help="Save cookies")
    p_save.add_argument("platform")
    p_save.add_argument("account_id")
    p_save.add_argument("--file", "-f", help="JSON file with cookie data")
    p_save.add_argument("--data", "-d", help="JSON string of cookie data")
    p_save.add_argument("--nickname", default="")
    p_save.add_argument("--path", default="data/cookies", help="Storage path")
    p_save.add_argument("--db", help="Database URL (e.g. postgresql://user:pass@host/db)")

    # Load
    p_load = sub.add_parser("load", help="Load cookies")
    p_load.add_argument("platform")
    p_load.add_argument("account_id")
    p_load.add_argument("--path", default="data/cookies")
    p_load.add_argument("--db", help="Database URL (e.g. postgresql://user:pass@host/db)")

    # List
    p_list = sub.add_parser("list", help="List accounts")
    p_list.add_argument("platform", nargs="?", default=None)
    p_list.add_argument("--path", default="data/cookies")
    p_list.add_argument("--db", help="Database URL (e.g. postgresql://user:pass@host/db)")

    # Delete
    p_del = sub.add_parser("delete", help="Delete account")
    p_del.add_argument("platform")
    p_del.add_argument("account_id")
    p_del.add_argument("--path", default="data/cookies")
    p_del.add_argument("--db", help="Database URL (e.g. postgresql://user:pass@host/db)")

    # Login
    p_login = sub.add_parser("login", help="Login to platform")
    p_login.add_argument("platform")
    p_login.add_argument("account_id", nargs="?", default="default")
    p_login.add_argument("--headless", action="store_true")
    p_login.add_argument("--path", default="data/cookies")
    p_login.add_argument("--db", help="Database URL (e.g. postgresql://user:pass@host/db)")

    # Export
    p_export = sub.add_parser("export", help="Export cookies as JSON")
    p_export.add_argument("platform")
    p_export.add_argument("account_id")
    p_export.add_argument("--path", default="data/cookies")
    p_export.add_argument("--db", help="Database URL (e.g. postgresql://user:pass@host/db)")

    # Config
    p_config = sub.add_parser("config", help="Show current configuration")

    # Validate
    p_val = sub.add_parser("validate", help="Check if cookies are still valid")
    p_val.add_argument("platform")
    p_val.add_argument("account_id")
    p_val.add_argument("--db", help="Database URL")
    p_val.add_argument("--path", default="data/cookies")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        return

    db_url = getattr(args, "db", None)
    if db_url:
        mgr = CookieManager(db_url, backend="sql")
    else:
        mgr = CookieManager()  # reads from env

    if args.cmd == "config":
        info = mgr.config_info()
        print(f"Backend: {info['backend']}")
        if info['backend'] == 'sql':
            print(f"Database: {info['url']}")
            print(f"Table:    {info['table']}")
        else:
            print(f"Path:     {info['path']}")

    elif args.cmd == "validate":
        valid = mgr.validate(args.platform, args.account_id)
        if valid:
            print(f"Valid: {args.platform}/{args.account_id}")
        else:
            print(f"Invalid or not found: {args.platform}/{args.account_id}", file=sys.stderr)
            sys.exit(1)

    elif args.cmd == "save":
        if args.file:
            with open(args.file) as f:
                data = json.load(f)
        elif args.data:
            data = json.loads(args.data)
        else:
            data = json.load(sys.stdin)
        mgr.save(args.platform, args.account_id, data, nickname=args.nickname)
        print(f"Saved: {args.platform}/{args.account_id}")

    elif args.cmd == "load":
        data = mgr.load(args.platform, args.account_id)
        if data:
            json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        else:
            print(f"Not found: {args.platform}/{args.account_id}", file=sys.stderr)
            sys.exit(1)

    elif args.cmd == "list":
        accounts = mgr.list(args.platform)
        if accounts:
            for a in accounts:
                print(f"{a['platform']}/{a['account_id']}  {a.get('nickname', '')}")
        else:
            print("No accounts found")

    elif args.cmd == "delete":
        mgr.delete(args.platform, args.account_id)
        print(f"Deleted: {args.platform}/{args.account_id}")

    elif args.cmd == "login":
        async def _login():
            from .browser import login_platform
            state = await login_platform(args.platform, headless=args.headless)
            mgr.save(args.platform, args.account_id, state)
            print(f"Logged in and saved: {args.platform}/{args.account_id}")
        asyncio.run(_login())

    elif args.cmd == "export":
        data = mgr.load(args.platform, args.account_id)
        if data:
            json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        else:
            print(f"Not found: {args.platform}/{args.account_id}", file=sys.stderr)
            sys.exit(1)

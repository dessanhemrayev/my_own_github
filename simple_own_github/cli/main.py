from __future__ import annotations

import argparse

try:
    from simple_own_github.service.adduser import addME, create_user
    from simple_own_github.web.app import app as web_app
except ImportError:  # pragma: no cover
    from service.adduser import addME, create_user
    from web.app import app as web_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a local Linux user account.")
    parser.add_argument("--username", help="Username to create")
    parser.add_argument("--comment", default="", help="Optional comment for the user")
    parser.add_argument("--password", help="Password for the new account (avoid passing secrets in shell history)")
    parser.add_argument("--password-file", help="Read the account password from a file instead of the command line")
    parser.add_argument("--web", action="store_true", help="Run the HTTP web service")
    parser.add_argument("--host", default="0.0.0.0", help="Host for the web server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the web server")
    return parser.parse_args()


def main() -> None:
    print("Hello user in my own GITHUB (Dessan)")
    args = parse_args()

    if args.web:
        import uvicorn

        uvicorn.run(web_app, host=args.host, port=args.port)
        return

    if args.username or args.password or args.password_file:
        if not args.username:
            raise ValueError("Username is required when using --password or --password-file.")
        password = args.password
        if args.password_file:
            with open(args.password_file, "r", encoding="utf-8") as handle:
                password = handle.read().rstrip("\r\n")
        if not password:
            raise ValueError("Password is required when using --username.")
        create_user(args.username, args.comment, password)
        return

    addME()


if __name__ == "__main__":
    main()

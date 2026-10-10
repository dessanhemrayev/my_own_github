#!/usr/bin/env python3

import fcntl
import getpass
import os
import pwd
import re
import shlex
import shutil
import subprocess
from pathlib import Path

USERNAME_PATTERN = re.compile(r"^[a-z]+$")
COMMENT_PATTERN = re.compile(r"^[a-z,]*$")
PASSWORD_SYMBOLS = r" !#$%&'()*+,-./[\\]^_`{|}~\""


def _normalize_secret(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return value.replace("\r", "").replace("\n", "")


def is_valid_username(username: str) -> bool:
    """Check that username contains only lowercase latin letters."""
    if not isinstance(username, str):
        return False
    return bool(USERNAME_PATTERN.fullmatch(username))


def is_valid_comment(comment: str) -> bool:
    """Check that comment only has lowercase letters and commas."""
    if not isinstance(comment, str):
        return False
    return bool(COMMENT_PATTERN.fullmatch(comment))


def is_valid_password(password: str) -> bool:
    """Require at least 8 chars and a mix of letters, digits, and symbols."""
    if not isinstance(password, str):
        return False
    if not password or "\n" in password or "\r" in password:
        return False
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!#$%&'()*+,-./\[\\\]^_`{|}~ ]", password):
        return False
    return True


def hash_password(password: str) -> str:
    """Hash the password with the strong OpenSSL SHA-512/crypt format."""
    candidate = _normalize_secret(password)
    if not is_valid_password(candidate):
        raise ValueError("Password must be at least 8 chars and include letters, digits, and symbols.")
    return subprocess.check_output(
        ["openssl", "passwd", "-6", "-stdin"],
        input=f"{candidate}\n".encode("utf-8"),
        stderr=subprocess.DEVNULL,
    ).decode("utf-8").strip()


def build_useradd_command(username: str, comment: str, password: str) -> str:
    """Return a shell command showing the useradd flow without printing a raw password."""
    safe_comment = shlex.quote(comment or "")
    safe_name = shlex.quote(username)
    _ = password
    return (
        f"useradd --create-home --user-group --comment {safe_comment} "
        f"--home /home/{username} --shell /bin/bash "
        f"--password \"$(printf '%s' '<redacted>' | openssl passwd -1 -stdin)\" {safe_name}"
    )


def root_check() -> None:
    """Exit if the current user is not root."""
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        print("ERROR: THIS PROGRAM REQUIRES ROOT PRIVILEGES. EXITING.")
        raise SystemExit(1)


def username_prompt() -> str:
    """Prompt user for a valid lowercase username."""
    print("Valid usernames contain only the characters 'a-z', e.g. trex")

    while True:
        username = input("Enter username to add: ").strip()
        confirm_name = input("To confirm, re-enter username: ").strip()

        if username != confirm_name or not is_valid_username(username):
            print("SORRY, THAT'S NOT ALLOWED. TRY AGAIN.")
            continue

        print(f"OK, checking if user: {username} exists.")
        return username


def username_check() -> str:
    """Check whether the username is already in use."""
    while True:
        candidate = username_prompt()

        try:
            pwd.getpwnam(candidate)
            print(f"USER {candidate} EXISTS. TRY A DIFFERENT USERNAME.")
        except KeyError:
            print(f"User {candidate} does not exist. Continuing...")
            return candidate


def comment_prompt() -> str:
    """Prompt for a comment containing only lowercase letters and commas."""
    print("Valid comments contain only the characters 'a-z' and ',', e.g. rex,tyrannosaurus. This field can be left blank.")

    while True:
        comment = input("Enter user comments, or press 'return' twice to leave blank: ").strip()
        confirm_comment = input("To confirm, re-enter comments: ").strip()

        if comment != confirm_comment or not is_valid_comment(comment):
            print("SORRY, THAT'S NOT ALLOWED. TRY AGAIN.")
            continue

        print("Comments match. Continuing...")
        return comment


def passwd_prompt() -> str:
    """Prompt user for a secure password."""
    print("Password MUST contain AT LEAST: one lower-case letter, one number, one symbol, and be a MINIMUM of 8 characters in length, e.g. 4.lizard")

    while True:
        password = getpass.getpass(prompt="Enter password for user: ")
        confirm_password = getpass.getpass(prompt="To confirm, re-enter password: ")

        if password != confirm_password or not is_valid_password(password):
            print("SORRY, THAT'S NOT ALLOWED. TRY AGAIN.")
            continue

        print("Password meets complexity requirement. Continuing...")
        return password


def create_user(username: str, comment: str = "", password: str | None = None) -> str:
    """Create a local Linux user account from validated data."""
    if not is_valid_username(username):
        raise ValueError("Username must contain only lowercase letters.")
    if not is_valid_comment(comment):
        raise ValueError("Comment may contain only lowercase letters and commas.")
    if password is None:
        raise ValueError("Password is required.")

    normalized_password = _normalize_secret(password)
    if not is_valid_password(normalized_password):
        raise ValueError("Password must be at least 8 chars and include letters, digits, and symbols.")

    try:
        pwd.getpwnam(username)
    except KeyError:
        pass
    else:
        raise ValueError(f"User '{username}' already exists.")

    encrypted_password = hash_password(normalized_password)
    subprocess.run(
        [
            "useradd",
            "--create-home",
            "--user-group",
            "--comment",
            comment,
            "--home",
            f"/home/{username}",
            "--shell",
            "/bin/bash",
            "--password",
            encrypted_password,
            username,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return username


def add_usr() -> None:
    """Create a new Linux account with the provided parameters."""
    name = username_check()
    note = comment_prompt()
    password = passwd_prompt()

    print(f"Adding user: {name}")
    create_user(name, note, password)
    print("Done.")


def addME() -> None:
    """Add a user to the local Linux system."""
    root_check()
    add_usr()


class UserService:
    """Service abstraction for user validation and creation."""

    def is_valid_username(self, username: str) -> bool:
        return is_valid_username(username)

    def is_valid_comment(self, comment: str) -> bool:
        return is_valid_comment(comment)

    def is_valid_password(self, password: str) -> bool:
        return is_valid_password(password)

    def normalize_comment(self, comment: str) -> str:
        text = "" if comment is None else str(comment).strip()
        if not text:
            return ""
        return text

    def create_user(self, username: str, comment: str = "", password: str | None = None) -> str:
        return create_user(username, comment, password)


class RepositoryService:
    """Create bare Git repositories for existing local users."""

    def __init__(self, base_dir: str | os.PathLike[str] | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir is not None else Path("/home")

    @staticmethod
    def is_valid_repo_name(repo_name: str) -> bool:
        if not isinstance(repo_name, str):
            return False
        normalized = repo_name.removesuffix(".git")
        return bool(re.fullmatch(r"[A-Za-z0-9._-]+", normalized)) and normalized not in {"", ".", ".."}

    def _user_repo_root(self, username: str) -> Path:
        if not is_valid_username(username):
            raise ValueError("Username must contain only lowercase letters.")
        root = (Path(self.base_dir) / username / "repositories").resolve(strict=False)
        return root

    def _resolve_repository_path(self, username: str, repo_name: str) -> tuple[Path, Path]:
        normalized_name = repo_name.removesuffix(".git")
        if not self.is_valid_repo_name(normalized_name):
            raise ValueError("Repository name may contain only letters, numbers, dots, underscores, hyphens.")
        repo_root = self._user_repo_root(username)
        repo_path = (repo_root / normalized_name).resolve(strict=False)
        if repo_path.parent != repo_root:
            raise ValueError("Repository path escapes the user's repository root.")
        return repo_root, repo_path

    def create_repository(self, username: str, repo_name: str) -> dict[str, str]:
        repo_root, repo_path = self._resolve_repository_path(username, repo_name)
        repo_root.mkdir(parents=True, exist_ok=True)
        lock_path = repo_root / ".create.lock"
        with open(lock_path, "a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            if repo_path.exists() or repo_path.is_symlink():
                raise FileExistsError(f"Repository '{repo_path.name}' already exists for user '{username}'.")

            try:
                subprocess.run(["git", "init", "--bare", str(repo_path)], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                if repo_path.exists() and not any(repo_path.iterdir()):
                    shutil.rmtree(repo_path, ignore_errors=True)
                raise

            subprocess.run(["git", "config", "--global", "--add", "safe.directory", str(repo_path)], check=False, capture_output=True, text=True)

            try:
                pwd.getpwnam(username)
                user_info = pwd.getpwnam(username)
                if os.geteuid() == 0:
                    for current_root, dirnames, filenames in os.walk(repo_path):
                        for dirname in dirnames:
                            os.chown(os.path.join(current_root, dirname), user_info.pw_uid, user_info.pw_gid)
                        for filename in filenames:
                            os.chown(os.path.join(current_root, filename), user_info.pw_uid, user_info.pw_gid)
                    os.chown(repo_root, user_info.pw_uid, user_info.pw_gid)
                    os.chown(repo_path, user_info.pw_uid, user_info.pw_gid)
            except KeyError:
                pass

            subprocess.run(["git", "--git-dir", str(repo_path), "config", "core.sharedRepository", "group"], check=True, capture_output=True, text=True)
            for current_root, dirnames, filenames in os.walk(repo_path):
                for dirname in dirnames:
                    os.chmod(os.path.join(current_root, dirname), 0o2775)
                for filename in filenames:
                    os.chmod(os.path.join(current_root, filename), 0o664)
            os.chmod(repo_path, 0o2775)

        return {
            "username": username,
            "repo": repo_path.name,
            "path": str(repo_path),
        }

    def list_repositories(self, username: str) -> list[dict[str, str]]:
        if not is_valid_username(username):
            raise ValueError("Username must contain only lowercase letters.")

        repo_root = self._user_repo_root(username)
        if not repo_root.exists():
            return []

        repos: list[dict[str, str]] = []
        for item in sorted(repo_root.iterdir()):
            if item.is_symlink() or not item.is_dir():
                continue
            if not self.is_valid_repo_name(item.name):
                continue
            if not (item / "HEAD").exists() and not (item / "config").exists():
                continue
            repos.append({
                "username": username,
                "name": item.name,
                "path": str(item),
            })
        return repos

    def get_repository(self, username: str, repo_name: str) -> dict[str, str]:
        _, repo_path = self._resolve_repository_path(username, repo_name)
        if not repo_path.exists() or not repo_path.is_dir():
            raise FileNotFoundError(f"Repository '{repo_path.name}' was not found for user '{username}'.")

        return {
            "username": username,
            "name": repo_path.name,
            "path": str(repo_path),
        }

    def delete_repository(self, username: str, repo_name: str) -> dict[str, str]:
        repo_root, repo_path = self._resolve_repository_path(username, repo_name)
        if not repo_path.exists() or not repo_path.is_dir():
            raise FileNotFoundError(f"Repository '{repo_path.name}' was not found for user '{username}'.")

        shutil.rmtree(repo_path)
        return {
            "username": username,
            "repo": repo_path.name,
            "path": str(repo_path),
            "status": "deleted",
        }


__all__ = [
    "RepositoryService",
    "UserService",
    "addME",
    "add_usr",
    "build_useradd_command",
    "comment_prompt",
    "create_user",
    "hash_password",
    "is_valid_comment",
    "is_valid_password",
    "is_valid_username",
    "passwd_prompt",
    "root_check",
    "username_check",
    "username_prompt",
]

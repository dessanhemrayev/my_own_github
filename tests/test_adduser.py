import os
import pwd
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from simple_own_github.service import adduser
from simple_own_github.web import app


class AddUserValidationTests(unittest.TestCase):
    def test_valid_username_accepts_lowercase_letters_only(self):
        self.assertTrue(adduser.is_valid_username("alex"))
        self.assertFalse(adduser.is_valid_username("Alex"))
        self.assertFalse(adduser.is_valid_username("alex3"))

    def test_valid_comment_accepts_letters_and_commas_and_empty_string(self):
        self.assertTrue(adduser.is_valid_comment(""))
        self.assertTrue(adduser.is_valid_comment("admin,ops"))
        self.assertFalse(adduser.is_valid_comment("admin_ops"))

    def test_valid_password_requires_length_and_complexity(self):
        self.assertTrue(adduser.is_valid_password("Strong1!"))
        self.assertFalse(adduser.is_valid_password("short"))
        self.assertFalse(adduser.is_valid_password("onlyletters"))
        self.assertFalse(adduser.is_valid_password("Onlyletters1"))

    def test_build_useradd_command_profiles_user_data(self):
        command = adduser.build_useradd_command(
            username="alice",
            comment="dev,ops",
            password="Strong1!",
        )

        self.assertIn("--comment dev,ops", command)
        self.assertIn("--home /home/alice", command)
        self.assertIn("alice", command)
        self.assertIn("openssl passwd -1 -stdin", command)

    def test_user_service_exposes_validation_and_creation_logic(self):
        service = adduser.UserService()

        self.assertTrue(service.is_valid_username("alex"))
        self.assertTrue(service.is_valid_password("Strong1!"))
        self.assertEqual(service.normalize_comment("dev,ops"), "dev,ops")

    def test_web_service_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_web_service_serves_repository_dashboard(self):
        client = TestClient(app)
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Репозитории", response.text)
        self.assertIn("Создать репозиторий", response.text)
        self.assertIn('id="repo-search"', response.text)
        self.assertIn('id="sort-order"', response.text)
        self.assertIn('id="repo-detail"', response.text)

    def test_repository_service_creates_bare_git_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            service = adduser.RepositoryService(base_dir=Path(tmpdir))
            result = service.create_repository("alice", "demo")

            self.assertTrue(Path(result["path"]).exists())
            self.assertEqual(
                subprocess.check_output(["git", "rev-parse", "--is-bare-repository"], cwd=result["path"], text=True).strip(),
                "true",
            )

    def test_web_service_allows_repo_creation_for_existing_user(self):
        current_user = pwd.getpwuid(os.getuid()).pw_name
        repo_name = f"demo-{uuid.uuid4().hex[:8]}"
        client = TestClient(app)
        response = client.post(f"/users/{current_user}/repos", json={"name": repo_name})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], current_user)
        self.assertTrue(Path(response.json()["path"]).exists())

    def test_web_service_exposes_repo_listing_detail_and_delete(self):
        current_user = pwd.getpwuid(os.getuid()).pw_name
        repo_name = f"demo-list-{uuid.uuid4().hex[:8]}"
        client = TestClient(app)

        create_response = client.post(f"/users/{current_user}/repos", json={"name": repo_name})
        self.assertEqual(create_response.status_code, 200)

        list_response = client.get(f"/users/{current_user}/repos")
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(any(item["name"] == repo_name for item in list_response.json()))

        detail_response = client.get(f"/users/{current_user}/repos/{repo_name}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["name"], repo_name)

        delete_response = client.delete(f"/users/{current_user}/repos/{repo_name}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["status"], "deleted")


if __name__ == "__main__":
    unittest.main()

import os
from pathlib import Path

try:
    from simple_own_github.service.adduser import RepositoryService, UserService
except ImportError:  # pragma: no cover
    from service.adduser import RepositoryService, UserService

_repository_root = os.environ.get("SIMPLE_OWN_GITHUB_REPO_ROOT")
user_service = UserService()
repository_service = RepositoryService(base_dir=_repository_root if _repository_root else Path("/home"))

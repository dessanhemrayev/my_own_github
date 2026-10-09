try:
    from simple_own_github.service.adduser import RepositoryService, UserService
except ImportError:  # pragma: no cover
    from service.adduser import RepositoryService, UserService

user_service = UserService()
repository_service = RepositoryService()

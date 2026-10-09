A small service-style Python application for managing Linux users and bare Git repositories. It includes a FastAPI service and a browser-based repository dashboard.

## Features

- Validates username, password and comment inputs
- Checks whether the user already exists
- Uses `openssl passwd -1` to generate a hashed password
- Creates the actual system account with `useradd`
- Exposes a service-oriented API via `UserService`
- Runs as a real HTTP service with FastAPI
- Creates, lists, inspects and deletes bare Git repositories
- Provides a web dashboard with repository search and sorting

## Service API

```python
from simple_own_github.service.adduser import UserService

service = UserService()
print(service.is_valid_username("alex"))
print(service.is_valid_password("Strong1!"))
```

## Web service

Install runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the web service and dashboard:

```bash
python -m simple_own_github --web --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000/> for the repository dashboard. Interactive API documentation is available at <http://localhost:8000/docs>.

## HTTP endpoints

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `POST` | `/users/validate` | Validate username, comment and password |
| `POST` | `/users` | Create a Linux user |
| `GET` | `/users/{username}/repos` | List a user's repositories |
| `POST` | `/users/{username}/repos` | Create a bare Git repository |
| `GET` | `/users/{username}/repos/{repo}` | Get repository details |
| `DELETE` | `/users/{username}/repos/{repo}` | Delete a repository |

Example requests:

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"alex","password":"Strong1!","comment":"dev,ops"}'

curl -X POST http://localhost:8000/users/alex/repos \
  -H "Content-Type: application/json" \
  -d '{"name":"demo"}'

curl http://localhost:8000/users/alex/repos
curl http://localhost:8000/users/alex/repos/demo
curl -X DELETE http://localhost:8000/users/alex/repos/demo
```

## Development

Install the project and development tools, then enable the Git hooks:

```bash
python -m pip install -e ".[dev]"
pre-commit install
```

Run the hooks manually and execute the tests with:

```bash
pre-commit run --all-files
python -m unittest tests.test_adduser
```

The web layer is organized by responsibility:

- `simple_own_github/web/app.py` — FastAPI setup, UI and router registration
- `simple_own_github/web/models.py` — request and response schemas
- `simple_own_github/web/routes/users.py` — health, validation and user endpoints
- `simple_own_github/web/routes/repositories.py` — repository endpoints
- `simple_own_github/web/dependencies.py` — shared service instances
- `simple_own_github/web/static/` — dashboard HTML, CSS and JavaScript

> Creating Linux users requires root privileges. Repository management requires the target Linux user to exist.

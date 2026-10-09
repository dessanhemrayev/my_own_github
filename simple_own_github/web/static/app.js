const usernameInput = document.getElementById('username-input');
const repoNameInput = document.getElementById('repo-name');
const repoList = document.getElementById('repo-list');
const repoCount = document.getElementById('repo-count');
const repoDetail = document.getElementById('repo-detail');
const messageBox = document.getElementById('message');
const searchInput = document.getElementById('repo-search');
const sortOrder = document.getElementById('sort-order');
let repositories = [];

const currentUser = () => usernameInput.value.trim() || 'root';

function setMessage(text, type = '') {
  messageBox.textContent = text;
  messageBox.className = `message ${type}`.trim();
}

function makeDetailBlock(label, value) {
  const block = document.createElement('div');
  block.className = 'detail-block';
  const heading = document.createElement('span');
  heading.className = 'detail-label';
  heading.textContent = label;
  const content = document.createElement('p');
  content.className = 'detail-value';
  content.textContent = value;
  block.append(heading, content);
  return block;
}

async function showRepository(repoName) {
  const username = currentUser();
  repoDetail.replaceChildren();
  repoDetail.textContent = 'Загружаем…';
  try {
    const response = await fetch(`/users/${encodeURIComponent(username)}/repos/${encodeURIComponent(repoName)}`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Не удалось загрузить репозиторий.');
    const heading = document.createElement('div');
    heading.className = 'detail-heading';
    const title = document.createElement('h3');
    title.textContent = payload.name;
    heading.append(title);
    repoDetail.replaceChildren(heading,
      makeDetailBlock('Владелец', `@${payload.username}`),
      makeDetailBlock('Расположение', payload.path),
      makeDetailBlock('Тип', 'Пустой bare Git-репозиторий'));
  } catch (error) {
    repoDetail.textContent = error.message;
    setMessage(error.message, 'error');
  }
}

function renderRepositories() {
  const query = searchInput.value.trim().toLocaleLowerCase();
  const direction = sortOrder.value === 'desc' ? -1 : 1;
  const visibleRepos = repositories
    .filter((repo) => repo.name.toLocaleLowerCase().includes(query))
    .sort((first, second) => first.name.localeCompare(second.name) * direction);
  repoCount.textContent = String(visibleRepos.length);
  repoList.replaceChildren();

  if (!visibleRepos.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    const title = document.createElement('strong');
    title.textContent = repositories.length ? 'Ничего не найдено' : 'Пока нет репозиториев';
    const note = document.createElement('span');
    note.textContent = repositories.length ? 'Измените поисковый запрос.' : 'Создайте первый репозиторий в панели слева.';
    empty.append(title, note);
    repoList.append(empty);
    return;
  }

  for (const repo of visibleRepos) {
    const row = document.createElement('article');
    row.className = 'repo-row';
    const icon = document.createElement('span');
    icon.className = 'repo-icon';
    icon.textContent = '⌘';
    icon.setAttribute('aria-hidden', 'true');
    const meta = document.createElement('div');
    meta.className = 'repo-meta';
    const name = document.createElement('span');
    name.className = 'repo-name';
    name.textContent = repo.name;
    const path = document.createElement('span');
    path.className = 'repo-path';
    path.textContent = repo.path;
    meta.append(name, path);
    const actions = document.createElement('div');
    actions.className = 'row-actions';
    const detailsButton = document.createElement('button');
    detailsButton.className = 'row-button';
    detailsButton.type = 'button';
    detailsButton.textContent = 'Детали';
    detailsButton.addEventListener('click', () => showRepository(repo.name));
    const deleteButton = document.createElement('button');
    deleteButton.className = 'row-button delete-btn';
    deleteButton.type = 'button';
    deleteButton.textContent = 'Удалить';
    deleteButton.addEventListener('click', () => deleteRepository(repo.name));
    actions.append(detailsButton, deleteButton);
    row.append(icon, meta, actions);
    repoList.append(row);
  }
}

async function loadRepositories() {
  const username = currentUser();
  usernameInput.value = username;
  document.getElementById('owner-caption').textContent = `Репозитории пользователя @${username}`;
  try {
    const response = await fetch(`/users/${encodeURIComponent(username)}/repos`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `Не удалось загрузить репозитории пользователя ${username}.`);
    repositories = payload;
    renderRepositories();
    setMessage(`Загружено: ${repositories.length}`, 'success');
  } catch (error) {
    repositories = [];
    renderRepositories();
    repoDetail.replaceChildren();
    setMessage(error.message, 'error');
  }
}

async function createRepository(event) {
  event.preventDefault();
  const username = currentUser();
  const repoName = repoNameInput.value.trim();
  if (!repoName) return setMessage('Укажите имя репозитория.', 'error');
  try {
    const response = await fetch(`/users/${encodeURIComponent(username)}/repos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: repoName }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Не удалось создать репозиторий.');
    repoNameInput.value = '';
    await loadRepositories();
    setMessage(`Репозиторий «${payload.repo}» создан.`, 'success');
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

async function deleteRepository(repoName) {
  if (!window.confirm(`Удалить репозиторий «${repoName}»? Это действие нельзя отменить.`)) return;
  const username = currentUser();
  try {
    const response = await fetch(`/users/${encodeURIComponent(username)}/repos/${encodeURIComponent(repoName)}`, { method: 'DELETE' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Не удалось удалить репозиторий.');
    if (repoDetail.querySelector('.detail-heading h3')?.textContent === repoName) {
      const placeholder = document.createElement('div');
      placeholder.className = 'detail-placeholder';
      const glyph = document.createElement('span');
      glyph.className = 'detail-glyph';
      glyph.setAttribute('aria-hidden', 'true');
      glyph.textContent = '⌘';
      const note = document.createElement('p');
      note.innerHTML = 'Выберите репозиторий,<br />чтобы посмотреть подробности.';
      placeholder.append(glyph, note);
      repoDetail.replaceChildren(placeholder);
    }
    await loadRepositories();
    setMessage(`Репозиторий «${payload.repo}» удалён.`, 'success');
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

document.getElementById('load-btn').addEventListener('click', loadRepositories);
document.getElementById('refresh-btn').addEventListener('click', loadRepositories);
document.getElementById('repo-form').addEventListener('submit', createRepository);
searchInput.addEventListener('input', renderRepositories);
sortOrder.addEventListener('change', renderRepositories);
usernameInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault();
    loadRepositories();
  }
});
loadRepositories();

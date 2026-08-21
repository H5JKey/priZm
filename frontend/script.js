// ===== API КОНФИГ =====
const API_BASE = '/api/v1'; // Nginx проксирует на бэкенд

// ===== ХРАНЕНИЕ ТОКЕНОВ =====
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ТОКЕНАМИ =====
function setTokens(accessToken, refreshToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
}

function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function removeTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function isAuthenticated() {
    return !!getAccessToken();
}

// ===== ОБЩИЙ ЗАПРОС К API =====
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    const token = getAccessToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers
    };

    try {
        const response = await fetch(url, config);

        // Если 401 - пробуем обновить токен
        if (response.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Повторяем запрос с новым токеном
                headers['Authorization'] = `Bearer ${getAccessToken()}`;
                const retryResponse = await fetch(url, { ...config, headers });
                const retryData = await retryResponse.json();
                if (!retryResponse.ok) {
                    throw new Error(retryData.detail || retryData.message || 'Ошибка запроса');
                }
                return retryData;
            } else {
                // Не удалось обновить - редирект на логин
                removeTokens();
                if (!window.location.pathname.includes('login.html') &&
                    !window.location.pathname.includes('register.html')) {
                    window.location.href = 'login.html';
                }
                throw new Error('Сессия истекла');
            }
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Ошибка запроса');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ===== ОБНОВЛЕНИЕ ТОКЕНА =====
async function refreshAccessToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.access_token) {
                setTokens(data.access_token, data.refresh_token || refreshToken);
                return true;
            }
        }
        return false;
    } catch (error) {
        console.error('Refresh token error:', error);
        return false;
    }
}

// ===== АВТОРИЗАЦИЯ =====

// Регистрация
async function register(surname, name, username, email, password) {
    const data = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
            surname,
            name,
            username,
            email,
            password
        })
    });

    // После регистрации сразу логинимся
    if (data.access_token) {
        setTokens(data.access_token, data.refresh_token);
    }

    return data;
}

// Логин
async function login(email, password) {
    const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });

    if (data.access_token) {
        setTokens(data.access_token, data.refresh_token);
    }

    return data;
}

// Выход
function logout() {
    removeTokens();
    window.location.href = 'login.html';
}

// ===== ПРОЕКТЫ =====
async function getProjects(page = 1, size = 10) {
    return await apiRequest(`/projects/?page=${page}&size=${size}`);
}

async function getProject(id) {
    return await apiRequest(`/projects/${id}`);
}

async function createProject(formData) {
    const token = getAccessToken();
    const response = await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка создания проекта');
    }

    return await response.json();
}

async function getUserProjects(userId) {
    return await apiRequest(`/users/${userId}/projects`);
}

async function getUserProfile(userId) {
    return await apiRequest(`/users/${userId}`);
}

async function getCurrentUser() {
    return await apiRequest('/users/me');
}

// ===== ЗАГРУЗЧИКИ =====
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i> Загрузка...
            </div>
        `;
    }
}

function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        const loadingEl = container.querySelector('.loading');
        if (loadingEl) loadingEl.remove();
    }
}

// ===== РЕНДЕР КАРТОЧКИ ПРОЕКТА =====
function renderProjectCard(project) {
    // Статус проекта
    const statusMap = {
        'pending': '⏳ В очереди',
        'processing': '🔄 Рендеринг...',
        'completed': '✅ Готов',
        'failed': '❌ Ошибка'
    };
    const statusText = statusMap[project.status] || project.status || 'Неизвестно';

    // Статус-класс для цвета
    const statusClass = project.status || 'pending';

    return `
        <div class="project-card" data-id="${project.id}">
            <div class="project-thumbnail">
                <div class="thumbnail-placeholder">
                    <i class="fas fa-cube"></i>
                    <span>3D</span>
                </div>
                ${project.visibility === 'private' ? 
                    `<span class="badge-private"><i class="fas fa-lock"></i></span>` : 
                    `<span class="badge-public"><i class="fas fa-globe"></i></span>`
                }
                <div class="project-status-badge status-${statusClass}">${statusText}</div>
            </div>
            <div class="project-info">
                <h3>${project.name}</h3>
                <p class="project-description">${project.description || 'Нет описания'}</p>
                <div class="project-meta">
                    <span class="project-author">
                        <i class="fas fa-user"></i> Пользователь #${project.user_id}
                    </span>
                    <span class="project-id">
                        <i class="fas fa-hashtag"></i> ID: ${project.id}
                    </span>
                </div>
            </div>
        </div>
    `;
}

// ===== ПЕРЕМЕННЫЕ =====
let currentPage = 1;
const PAGE_SIZE = 10;

// ===== ЗАГРУЗКА ПРОЕКТОВ =====
async function loadProjects(page = 1) {
    const container = document.getElementById('projectsGrid');
    if (!container) return;

    try {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'block';

        const data = await getProjects(page, PAGE_SIZE);
        console.log('📦 Получены проекты:', data);

        if (data.project_list && data.project_list.length > 0) {
            container.innerHTML = data.project_list.map(p => renderProjectCard(p)).join('');

            document.querySelectorAll('.project-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = card.dataset.id;
                    window.location.href = `project.html?id=${id}`;
                });
            });
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-box-open"></i>
                    <p>Нет проектов</p>
                    <small>Создайте первый проект!</small>
                </div>
            `;
        }

        // Определяем общее количество страниц
        let totalPages = page;
        if (data.total_pages) {
            totalPages = data.total_pages;
        } else if (data.total) {
            totalPages = Math.ceil(data.total / PAGE_SIZE);
        } else if (data.project_list.length === PAGE_SIZE) {
            // Если получили полную страницу — предполагаем, что есть еще
            totalPages = page + 1;
        }

        updatePagination(page, totalPages);

    } catch (error) {
        console.error('❌ Ошибка загрузки проектов:', error);
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Ошибка загрузки: ${error.message}</p>
                <button onclick="loadProjects(${currentPage})" class="btn btn-secondary">
                    <i class="fas fa-redo"></i> Повторить
                </button>
            </div>
        `;
    } finally {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

// ===== ПАГИНАЦИЯ =====
function updatePagination(current, total) {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');

    // Обновляем глобальную переменную
    currentPage = current;

    console.log(`📄 Пагинация: страница ${current} из ${total}`);

    if (prevBtn) {
        prevBtn.disabled = current <= 1;
        prevBtn.onclick = () => {
            if (current > 1) {
                const newPage = current - 1;
                console.log(`⬅️ Переход на страницу ${newPage}`);
                loadProjects(newPage);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };
    }

    if (nextBtn) {
        nextBtn.disabled = current >= total;
        nextBtn.onclick = () => {
            if (current < total) {
                const newPage = current + 1;
                console.log(`➡️ Переход на страницу ${newPage}`);
                loadProjects(newPage);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };
    }

    if (pageInfo) {
        pageInfo.textContent = `Страница ${current} из ${total || 1}`;
    }
}

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    const publicPages = ['login.html', 'register.html'];
    const currentPage = window.location.pathname.split('/').pop();

    // Проверка авторизации
    if (!isAuthenticated() && !publicPages.includes(currentPage)) {
        window.location.href = 'login.html';
        return;
    }

    // Если авторизованы и на странице логина/регистрации - редирект
    if (isAuthenticated() && publicPages.includes(currentPage)) {
        window.location.href = 'index.html';
        return;
    }

    // Кнопка выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Загрузка проектов на главной
    if (currentPage === '' || currentPage === 'index.html') {
        loadProjects();
    }

    // ===== ОБРАБОТЧИК РЕГИСТРАЦИИ =====
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const surname = document.getElementById('surname').value;
            const name = document.getElementById('name').value;
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            const errorDiv = document.getElementById('registerError');

            // Валидация
            if (password !== confirmPassword) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Пароли не совпадают';
                return;
            }

            if (password.length < 6) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Пароль должен быть минимум 6 символов';
                return;
            }

            try {
                errorDiv.style.display = 'none';
                const result = await register(surname, name, username, email, password);

                // После успешной регистрации и получения токена
                if (result.access_token) {
                    window.location.href = 'index.html';
                } else {
                    // Если токен не пришел, но регистрация успешна - идем на логин
                    window.location.href = 'login.html?registered=true';
                }
            } catch (error) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = error.message || 'Ошибка регистрации';
            }
        });
    }

    // ===== ОБРАБОТЧИК ЛОГИНА =====
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('loginError');

            try {
                errorDiv.style.display = 'none';
                await login(email, password);
                window.location.href = 'index.html';
            } catch (error) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = error.message || 'Неверный email или пароль';
            }
        });
    }

    // ===== ОБРАБОТЧИК СОЗДАНИЯ ПРОЕКТА =====
    const createForm = document.getElementById('createProjectForm');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData();
            const name = document.getElementById('projectName').value;
            const description = document.getElementById('projectDescription').value;
            const file = document.getElementById('glbFile').files[0];
            const visibility = document.querySelector('input[name="visibility"]:checked').value;
            const quality = document.getElementById('quality').value;
            const resolution = document.getElementById('resolution').value;
            const background = document.getElementById('background').value;

            // Валидация
            if (!file) {
                const errorDiv = document.getElementById('createError');
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Пожалуйста, выберите GLB-файл';
                return;
            }

            formData.append('name', name);
            formData.append('description', description);
            formData.append('file', file);
            formData.append('visibility', visibility);
            formData.append('settings', JSON.stringify({ quality, resolution, background }));

            const errorDiv = document.getElementById('createError');
            const successDiv = document.getElementById('createSuccess');

            try {
                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';

                const result = await createProject(formData);

                successDiv.style.display = 'block';
                successDiv.textContent = '✅ Проект успешно создан!';

                setTimeout(() => {
                    window.location.href = `project.html?id=${result.id}`;
                }, 1500);
            } catch (error) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = error.message || 'Ошибка создания проекта';
            }
        });
    }

    // ===== ЗАГРУЗКА ПРОЕКТА =====
    if (currentPage === 'project.html') {
        const params = new URLSearchParams(window.location.search);
        const projectId = params.get('id');
        if (projectId) {
            loadProjectDetail(projectId);
        }
    }

    // ===== ЗАГРУЗКА ПРОФИЛЯ =====
    if (currentPage === 'profile.html') {
        const params = new URLSearchParams(window.location.search);
        const userId = params.get('id');
        loadProfile(userId);
    }
});

// ===== ЗАГРУЗКА ДЕТАЛЕЙ ПРОЕКТА =====
async function loadProjectDetail(projectId) {
    const container = document.getElementById('projectDetail');
    if (!container) return;

    try {
        showLoading('projectDetail');
        const project = await getProject(projectId);

        container.innerHTML = `
            <div class="project-detail-content">
                <div class="project-detail-header">
                    <h1>${project.name}</h1>
                    <div class="project-detail-meta">
                        <span class="badge ${project.visibility === 'private' ? 'badge-private' : 'badge-public'}">
                            ${project.visibility === 'private' ? '🔒 Приватный' : '🌍 Публичный'}
                        </span>
                        <span class="project-status">Статус: ${project.status || 'Готов'}</span>
                    </div>
                </div>

                <div class="project-detail-body">
                    <div class="project-detail-left">
                        <div class="project-description">
                            <h3>📝 Описание</h3>
                            <p>${project.description || 'Нет описания'}</p>
                        </div>

                        <div class="project-files">
                            <h3>📁 Файлы</h3>
                            <div class="file-item">
                                <i class="fas fa-file-archive"></i>
                                <span>Исходный GLB: ${project.file_name || 'model.glb'}</span>
                                <a href="${project.file_url}" class="btn btn-sm btn-secondary" download>
                                    <i class="fas fa-download"></i> Скачать
                                </a>
                            </div>
                            <div class="file-item">
                                <i class="fas fa-image"></i>
                                <span>Рендер: ${project.render_file_name || 'render.png'}</span>
                                <a href="${project.render_url}" class="btn btn-sm btn-primary" target="_blank">
                                    <i class="fas fa-eye"></i> Просмотреть
                                </a>
                            </div>
                        </div>

                        <div class="project-render-settings">
                            <h3>⚙️ Настройки рендера</h3>
                            <ul>
                                <li><strong>Качество:</strong> ${project.settings?.quality || 'medium'}</li>
                                <li><strong>Разрешение:</strong> ${project.settings?.resolution || '1024'}x${project.settings?.resolution || '1024'}</li>
                                <li><strong>Фон:</strong> ${project.settings?.background || 'black'}</li>
                            </ul>
                        </div>
                    </div>

                    <div class="project-detail-right">
                        <div class="render-preview">
                            <h3>🖼️ Результат рендера</h3>
                            ${project.render_url ? 
                                `<img src="${project.render_url}" alt="Render" class="render-image">` :
                                `<div class="no-render">
                                    <i class="fas fa-image"></i>
                                    <p>Рендер еще не готов</p>
                                </div>`
                            }
                        </div>
                    </div>
                </div>

                <div class="project-detail-footer">
                    <div class="project-author-info" onclick="window.location.href='profile.html?id=${project.author_id}'">
                        <h3>👤 Владелец</h3>
                        <div class="author-card">
                            <div class="author-avatar">
                                ${project.author?.avatar ? 
                                    `<img src="${project.author.avatar}" alt="${project.author.username}">` :
                                    `<i class="fas fa-user-circle"></i>`
                                }
                            </div>
                            <div class="author-details">
                                <strong>${project.author?.username || 'Аноним'}</strong>
                                <small>${project.author?.email || ''}</small>
                                <span class="click-hint">Нажмите для просмотра профиля →</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Ошибка загрузки проекта: ${error.message}</p>
                <button onclick="history.back()" class="btn btn-secondary">Назад</button>
            </div>
        `;
    }
}

// ===== ЗАГРУЗКА ПРОФИЛЯ =====
async function loadProfile(userId) {
    const container = document.getElementById('profileContent');
    if (!container) return;

    try {
        showLoading('profileContent');
        const user = userId ? await getUserProfile(userId) : await getCurrentUser();
        const projects = userId ? await getUserProjects(userId) : await getUserProjects(user.id);

        container.innerHTML = `
            <div class="profile-header">
                <div class="profile-avatar">
                    ${user.avatar ? 
                        `<img src="${user.avatar}" alt="${user.username}">` :
                        `<i class="fas fa-user-circle"></i>`
                    }
                </div>
                <div class="profile-info">
                    <h1>${user.username}</h1>
                    <p class="profile-name">${user.name} ${user.surname}</p>
                    <p class="profile-email"><i class="fas fa-envelope"></i> ${user.email}</p>
                    <p class="profile-bio">${user.bio || 'Пользователь 3D Render'}</p>
                    <div class="profile-stats">
                        <span><i class="fas fa-project-diagram"></i> ${projects.length} проектов</span>
                        <span><i class="fas fa-calendar"></i> С нами с ${new Date(user.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                </div>
                ${!userId ? `
                    <div class="profile-actions">
                        <button class="btn btn-secondary" onclick="editProfile()">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                    </div>
                ` : ''}
            </div>

            <div class="profile-projects">
                <h2>📦 Проекты пользователя</h2>
                ${projects.length > 0 ? `
                    <div class="projects-grid">
                        ${projects.map(p => renderProjectCard(p)).join('')}
                    </div>
                ` : `
                    <div class="empty-state">
                        <i class="fas fa-box-open"></i>
                        <p>У пользователя нет проектов</p>
                    </div>
                `}
            </div>
        `;

        document.querySelectorAll('.project-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.id;
                window.location.href = `project.html?id=${id}`;
            });
        });

    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Ошибка загрузки профиля: ${error.message}</p>
            </div>
        `;
    }
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
function editProfile() {
    alert('Функция редактирования профиля (будет добавлена)');
}

// Экспорт для использования в других скриптах
window.api = {
    login,
    register,
    logout,
    getProjects,
    getProject,
    createProject,
    getUserProjects,
    getUserProfile,
    getCurrentUser,
    isAuthenticated,
    getAccessToken,
    getRefreshToken,
    refreshAccessToken
};
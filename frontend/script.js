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

// ===== ЛОГИН =====
async function login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
    });

    if (!response.ok) {
        let errorMessage = 'Ошибка входа';
        try {
            const error = await response.json();
            errorMessage = error.detail || errorMessage;
        } catch (e) {
            errorMessage = `Ошибка ${response.status}`;
        }
        throw new Error(errorMessage);
    }

    const data = await response.json();

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

// ===== ПОЛЬЗОВАТЕЛЬ =====
async function getCurrentUserProfile() {
    return await apiRequest('/users/about-me');
}

async function updateCurrentUserProfile(surname, name, username, email) {
    return await apiRequest('/users/about-me', {
        method: 'PUT',
        body: JSON.stringify({
            surname,
            name,
            username,
            email
        })
    });
}



// ===== МОИ ПРОЕКТЫ =====
async function getMyProjects(page = 1, size = 10) {
    return await apiRequest(`/projects/about-me?page=${page}&size=${size}`);
}

// ===== ЗАГРУЗКА МОИХ ПРОЕКТОВ =====
let myProjectsPage = 1;
const MY_PROJECTS_SIZE = 10;

async function loadMyProjects(page = 1) {
    const container = document.getElementById('myProjectsGrid');
    if (!container) return;

    try {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'block';

        console.log(`📥 Загрузка моих проектов: страница ${page}`);
        const data = await getMyProjects(page, MY_PROJECTS_SIZE);
        console.log('📦 Мои проекты:', data);

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
                    <p>У вас нет проектов</p>
                    <small>Создайте свой первый проект!</small>
                    <br><br>
                    <a href="create.html" class="btn btn-primary">
                        <i class="fas fa-plus-circle"></i> Создать проект
                    </a>
                </div>
            `;
        }

        // Определяем общее количество страниц
        let totalPages = page;
        if (data.total_pages) {
            totalPages = data.total_pages;
        } else if (data.total) {
            totalPages = Math.ceil(data.total / MY_PROJECTS_SIZE);
        } else if (data.project_list.length === MY_PROJECTS_SIZE) {
            totalPages = page + 1;
        }

        updateMyProjectsPagination(page, totalPages);

    } catch (error) {
        console.error('❌ Ошибка загрузки моих проектов:', error);
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Ошибка загрузки: ${error.message}</p>
                <button onclick="loadMyProjects(${myProjectsPage})" class="btn btn-secondary">
                    <i class="fas fa-redo"></i> Повторить
                </button>
            </div>
        `;
    } finally {
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

// ===== ПАГИНАЦИЯ ДЛЯ МОИХ ПРОЕКТОВ =====
function updateMyProjectsPagination(current, total) {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    myProjectsPage = current;

    if (prevBtn) {
        prevBtn.disabled = current <= 1;
        prevBtn.onclick = () => {
            if (current > 1) {
                const newPage = current - 1;
                loadMyProjects(newPage);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };
    }

    if (nextBtn) {
        nextBtn.disabled = current >= total;
        nextBtn.onclick = () => {
            if (current < total) {
                const newPage = current + 1;
                loadMyProjects(newPage);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        };
    }
}

// ===== ПРОЕКТЫ =====
async function getProjects(page = 1, size = 10) {
    return await apiRequest(`/projects/?page=${page}&size=${size}`);
}

async function getProject(id) {
    return await apiRequest(`/projects/${id}`);
}

// ===== УДАЛЕНИЕ ПРОЕКТА =====
async function deleteProject(projectId) {
    const token = getAccessToken();
    const response = await fetch(`${API_BASE}/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        let errorMessage = 'Ошибка удаления';
        try {
            const error = await response.json();
            errorMessage = error.detail || errorMessage;
        } catch (e) {
            // Если ответ не JSON
            const text = await response.text();
            if (text) errorMessage = text;
        }
        throw new Error(errorMessage);
    }

    // DELETE может возвращать пустой ответ
    return null;
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

// ===== НАСТРОЙКА ДРОПДАУНА =====
function setupDropdown() {
    const avatarBtn = document.getElementById('avatarBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');

    if (avatarBtn && dropdownMenu) {
        // Клик по аватарке
        avatarBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        // Закрытие при клике вне меню
        document.addEventListener('click', function(e) {
            if (!dropdownMenu.contains(e.target) && e.target !== avatarBtn) {
                dropdownMenu.classList.remove('show');
            }
        });

        // Закрытие при клике на пункт меню
        dropdownMenu.querySelectorAll('.dropdown-item').forEach(function(item) {
            item.addEventListener('click', function() {
                dropdownMenu.classList.remove('show');
            });
        });
    }
}

// ===== ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЯ ПО ID =====
async function getUserById(userId) {
    return await apiRequest(`/users/${userId}`);
}

// ===== ПОЛУЧЕНИЕ ПРОЕКТОВ ПОЛЬЗОВАТЕЛЯ =====
async function getUserProjectsById(userId, page = 1, size = 10) {
    return await apiRequest(`/projects/user/${userId}?page=${page}&size=${size}`);
}

// ===== РЕДАКТИРОВАНИЕ ПРОЕКТА =====
function toggleEditProject(projectId) {
    const form = document.getElementById('editProjectForm');
    if (form) {
        if (form.style.display === 'none' || form.style.display === '') {
            form.style.display = 'block';
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            form.style.display = 'none';
        }
    }
}

function cancelEditProject() {
    const form = document.getElementById('editProjectForm');
    if (form) {
        form.style.display = 'none';
    }
}

// ===== ЗАГРУЗКА ФАЙЛА =====
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('uploaded_file', file);

    const token = getAccessToken();
    const response = await fetch(`${API_BASE}/files/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка загрузки файла');
    }

    return await response.json();
}

// ===== УДАЛЕНИЕ ПРОЕКТА С МОДАЛЬНЫМ ОКНОМ =====
let projectToDelete = null;

function deleteProjectHandler(projectId) {
    // Сохраняем ID проекта для удаления
    projectToDelete = projectId;

    // Показываем модальное окно
    const modal = document.getElementById('deleteProjectModal');
    const nameDisplay = document.getElementById('modalProjectNameDisplay');
    const confirmInput = document.getElementById('modalProjectConfirmInput');
    const confirmBtn = document.getElementById('modalConfirmDeleteProject');
    const errorDiv = document.getElementById('modalProjectError');

    // Получаем название проекта
    getProject(projectId).then(project => {
        if (project && project.name) {
            nameDisplay.textContent = project.name;
        }
    }).catch(() => {
        nameDisplay.textContent = 'проект';
    });

    // Сбрасываем состояние
    confirmInput.value = '';
    errorDiv.style.display = 'none';
    confirmBtn.disabled = true;
    modal.style.display = 'flex';

    // Слушаем ввод
    confirmInput.oninput = function() {
        const projectName = nameDisplay.textContent;
        if (this.value === projectName) {
            errorDiv.style.display = 'none';
            confirmBtn.disabled = false;
        } else {
            errorDiv.style.display = 'block';
            confirmBtn.disabled = true;
        }
    };

    // Подтверждение удаления
    confirmBtn.onclick = async function() {
        const projectName = nameDisplay.textContent;
        if (confirmInput.value === projectName) {
            try {
                await deleteProject(projectToDelete);

                // Закрываем модалку
                closeDeleteProjectModal();

                // Редирект на главную
                window.location.href = 'index.html';

            } catch (error) {
                const errorDiv = document.getElementById('modalProjectError');
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Ошибка удаления: ' + error.message;
                errorDiv.style.color = '#e74c3c';
            }
        }
    };
}

// ===== ЗАКРЫТИЕ МОДАЛЬНОГО ОКНА УДАЛЕНИЯ ПРОЕКТА =====
function closeDeleteProjectModal() {
    const modal = document.getElementById('deleteProjectModal');
    if (modal) {
        modal.style.display = 'none';
    }
    projectToDelete = null;
}

// Закрытие по клику вне окна
document.addEventListener('click', function(e) {
    const modal = document.getElementById('deleteProjectModal');
    if (e.target === modal) {
        closeDeleteProjectModal();
    }
});

// Закрытие по Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDeleteProjectModal();
    }
});

// ===== ОТКРЫТИЕ МЕНЮ АВАТАРКИ =====
function toggleMenu() {
    const menu = document.getElementById('dropdownMenu');
    if (menu) {
        menu.classList.toggle('show');
        console.log('Меню переключено:', menu.classList.contains('show'));
    }
}

// ===== СОЗДАНИЕ ПРОЕКТА =====
async function createProjectData(projectData) {
    return await apiRequest('/projects/create', {
        method: 'POST',
        body: JSON.stringify(projectData)
    });
}

// ===== ЗАГРУЗКА ДЕТАЛЕЙ ПРОЕКТА =====
async function loadProjectDetail(projectId) {
    console.log('🔵 loadProjectDetail вызвана, projectId:', projectId);

    const container = document.getElementById('projectDetail');
    if (!container) {
        console.error('❌ Элемент projectDetail не найден');
        return;
    }

    try {
        container.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i> Загрузка...
            </div>
        `;

        // 1. Получаем проект
        const project = await getProject(projectId);
        console.log('📦 Детали проекта:', project);

        // 2. Получаем текущего пользователя
        let currentUser = null;
        let isOwner = false;
        try {
            currentUser = await getCurrentUserProfile();
            isOwner = currentUser && currentUser.id === project.user_id;
            console.log('👤 Текущий пользователь:', currentUser);
            console.log('🔑 Владелец:', isOwner);
        } catch (e) {
            console.warn('⚠️ Не удалось загрузить текущего пользователя');
        }

        // 3. Получаем владельца проекта
        let owner = null;
        try {
            owner = await getUserById(project.user_id);
            console.log('👤 Владелец проекта:', owner);
        } catch (e) {
            console.warn('⚠️ Не удалось загрузить владельца');
        }

        // Статус
        const statusMap = {
            'pending': '⏳ В очереди',
            'processing': '🔄 Рендеринг...',
            'rendering': '🔄 Рендеринг...',
            'completed': '✅ Готов',
            'failed': '❌ Ошибка'
        };
        const statusText = statusMap[project.status] || project.status || 'Неизвестно';
        const statusClass = project.status || 'pending';

        // Видимость
        const visibilityText = project.visibility === 'private' ? '🔒 Приватный' : '🌍 Публичный';
        const visibilityClass = project.visibility === 'private' ? 'badge-private' : 'badge-public';

        // Рендер
        const renderUrl = project.render?.url || null;
        const isRendered = renderUrl !== null && project.status === 'completed';

        // GLB
        const glbUrl = project.url || null;
        const glbName = glbUrl ? glbUrl.split('/').pop().split('?')[0] : 'model.glb';

        // Информация о владельце
        const ownerName = owner ? owner.username : `Пользователь #${project.user_id}`;
        const ownerFullName = owner ? `${owner.name} ${owner.surname}` : '';
        const ownerId = owner ? owner.id : project.user_id;

        container.innerHTML = `
            <div class="project-detail-content">
                <div class="project-detail-header">
                    <div class="project-detail-header-top">
                        <h1>${project.name || 'Без названия'}</h1>
                        ${currentUser && currentUser.id === project.user_id ? `
                            <div class="project-actions">
                                <button class="btn btn-secondary" onclick="toggleEditProject(${project.id})">
                                    <i class="fas fa-edit"></i> Редактировать
                                </button>
                                <button class="btn btn-danger" onclick="deleteProjectHandler(${project.id})">
                                    <i class="fas fa-trash"></i> Удалить
                                </button>
                            </div>
                        ` : ''}
                    </div>
                    <div class="project-detail-meta">
                        <span class="badge ${visibilityClass}">${visibilityText}</span>
                        <span class="status-badge status-${statusClass}">${statusText}</span>
                    </div>
                </div>
                
                

                <!-- Форма редактирования (скрыта по умолчанию) -->
                ${isOwner ? `
                <div id="editProjectForm" style="display:none;" class="edit-project-form">
                    <h3>✏️ Редактировать проект</h3>
                    <form id="updateProjectForm">
                        <div class="form-group">
                            <label>Название</label>
                            <input type="text" id="editProjectName" value="${project.name}" required>
                        </div>
                        <div class="form-group">
                            <label>Описание</label>
                            <textarea id="editProjectDescription" rows="3">${project.description || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label>Доступ</label>
                            <select id="editProjectVisibility">
                                <option value="public" ${project.visibility === 'public' ? 'selected' : ''}>Публичный</option>
                                <option value="private" ${project.visibility === 'private' ? 'selected' : ''}>Приватный</option>
                            </select>
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Сохранить
                            </button>
                            <button type="button" class="btn btn-secondary" onclick="cancelEditProject()">
                                <i class="fas fa-times"></i> Отмена
                            </button>
                        </div>
                    </form>
                    <div id="updateProjectError" class="error-message" style="display:none;"></div>
                    <div id="updateProjectSuccess" class="success-message" style="display:none;"></div>
                </div>
                ` : ''}

                <div class="project-detail-body">
                    <!-- Левая колонка -->
                    <div class="project-detail-left">
                        <!-- Описание -->
                        <div class="detail-section">
                            <h3>📝 Описание</h3>
                            <p>${project.description || 'Нет описания'}</p>
                        </div>

                        <!-- Файлы -->
                        <div class="detail-section">
                            <h3>📁 Файлы</h3>
                            <div class="file-item">
                                <i class="fas fa-file-archive"></i>
                                <span>${glbName}</span>
                                ${glbUrl ? `<a href="${glbUrl}" class="btn btn-sm btn-secondary" download>
                                    <i class="fas fa-download"></i> Скачать GLB
                                </a>` : '<span class="file-missing">Файл недоступен</span>'}
                            </div>
                            <div class="file-item">
                                <i class="fas fa-image"></i>
                                <span>${project.render?.file?.name || 'Рендер'}</span>
                                ${isRendered && renderUrl ? 
                                    `<a href="${renderUrl}" class="btn btn-sm btn-primary" target="_blank">
                                        <i class="fas fa-eye"></i> Смотреть
                                    </a>` : 
                                    `<span class="file-missing">${project.status === 'rendering' ? '⏳ Рендерится...' : 'Не готов'}</span>`
                                }
                            </div>
                        </div>

                        <!-- Настройки рендера -->
                        ${project.render ? `
                        <div class="detail-section">
                            <h3>⚙️ Настройки рендера</h3>
                            <ul class="render-settings-list">
                                <li><span>Разрешение</span> <span>${project.render.width || '—'} × ${project.render.height || '—'}</span></li>
                                <li><span>Сэмплы</span> <span>${project.render.samples || '—'}</span></li>
                                <li><span>Денойзер</span> <span>${project.render.denoiser ? '✅ Включен' : '❌ Выключен'}</span></li>
                                <li><span>GPU</span> <span>${project.render.gpu ? '✅ Включен' : '❌ Выключен'}</span></li>
                            </ul>
                        </div>
                        ` : ''}
                    </div>

                    <!-- Правая колонка -->
                    <div class="project-detail-right">
                        <!-- Превью -->
                        <div class="render-preview">
                            <h3>🖼️ Результат</h3>
                            ${isRendered && renderUrl ? 
                                `<img src="${renderUrl}" alt="Render" class="render-image">` :
                                `<div class="no-render">
                                    <i class="fas fa-image"></i>
                                    <p>${project.status === 'rendering' ? '⏳ Рендерится...' : 'Рендер не готов'}</p>
                                    ${project.status === 'rendering' ? '<small>Обновите страницу через несколько минут</small>' : ''}
                                </div>`
                            }
                        </div>
                        
                        <!-- Владелец -->
                        <div class="owner-card" onclick="window.location.href='profile.html?id=${ownerId}'">
                            <div class="owner-avatar">
                                <i class="fas fa-user-circle"></i>
                            </div>
                            <div class="owner-info">
                                <div class="owner-name">${ownerFullName || ownerName}</div>
                                <div class="owner-username">@${ownerName}</div>
                                <div class="owner-hint">Нажмите для просмотра профиля →</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // ===== ОБРАБОТЧИК ОБНОВЛЕНИЯ ПРОЕКТА =====
        const updateProjectForm = document.getElementById('updateProjectForm');
        if (updateProjectForm) {
            updateProjectForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const name = document.getElementById('editProjectName').value.trim();
                const description = document.getElementById('editProjectDescription').value.trim();
                const visibility = document.getElementById('editProjectVisibility').value;

                const errorDiv = document.getElementById('updateProjectError');
                const successDiv = document.getElementById('updateProjectSuccess');

                if (!name) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'Введите название проекта';
                    return;
                }

                try {
                    errorDiv.style.display = 'none';
                    successDiv.style.display = 'none';

                    await updateProject(projectId, name, description, visibility);

                    successDiv.style.display = 'block';
                    successDiv.textContent = '✅ Проект успешно обновлен!';

                    setTimeout(() => {
                        loadProjectDetail(projectId);
                    }, 1500);
                } catch (error) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = error.message || 'Ошибка обновления проекта';
                }
            });
        }

    } catch (error) {
        console.error('❌ Ошибка загрузки проекта:', error);
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Ошибка загрузки проекта: ${error.message}</p>
                <button onclick="history.back()" class="btn btn-secondary">
                    <i class="fas fa-arrow-left"></i> Назад
                </button>
            </div>
        `;
    }
}
// ===== ОБНОВЛЕНИЕ ПРОЕКТА =====
async function updateProject(projectId, name, description, visibility) {
    return await apiRequest(`/projects/${projectId}`, {
        method: 'PATCH',
        body: JSON.stringify({
            name: name,
            description: description,
            visibility: visibility
        })
    });
}

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    const publicPages = ['login.html', 'register.html'];
    const currentPage = window.location.pathname.split('/').pop();

    console.log(`🔵 Текущая страница: ${currentPage || 'index'}`);

    // Проверка авторизации
    if (!isAuthenticated() && !publicPages.includes(currentPage)) {
        console.log('🔴 Не авторизован, редирект на логин');
        window.location.href = 'login.html';
        return;
    }

    // Если авторизованы и на странице логина/регистрации - редирект
    if (isAuthenticated() && publicPages.includes(currentPage)) {
        console.log('🟢 Авторизован, редирект на главную');
        window.location.href = 'index.html';
        return;
    }

    // Настройка дропдауна
    setupDropdown();

    // Кнопка выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // ===== ЗАГРУЗКА ПРОЕКТОВ НА ГЛАВНОЙ =====
    if (currentPage === '' || currentPage === 'index.html') {
        console.log('🏠 Загрузка главной страницы');
        loadProjects(1);
    }

    // ===== МОИ ПРОЕКТЫ =====
    if (currentPage === 'my-projects.html') {
        console.log('📁 Загрузка моих проектов');
        loadMyProjects(1);
    }

    // ===== ЗАГРУЗКА ПРОФИЛЯ =====
    if (currentPage === 'profile.html') {
        const params = new URLSearchParams(window.location.search);
        const userId = params.get('id');
        const page = parseInt(params.get('page')) || 1;
        profilePage = page;
        if (userId) {
            loadProfile(userId, page);
        } else {
            loadProfile(null, page);
        }
    }

    // ===== АВАТАРКА И ДРОПДАУН =====
    const avatarBtn = document.getElementById('avatarBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');

    if (avatarBtn && dropdownMenu) {
        avatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!dropdownMenu.contains(e.target) && e.target !== avatarBtn) {
                dropdownMenu.classList.remove('show');
            }
        });

        dropdownMenu.querySelectorAll('.dropdown-item').forEach(item => {
            item.addEventListener('click', () => {
                dropdownMenu.classList.remove('show');
            });
        });
    }

    // ===== КНОПКА "МОИ ПРОЕКТЫ" =====
    const myProjectsBtn = document.getElementById('myProjectsBtn');
    if (myProjectsBtn) {
        myProjectsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = 'profile.html?tab=projects';
        });
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

                if (result.access_token) {
                    window.location.href = 'index.html';
                } else {
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

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('loginError');

            try {
                errorDiv.style.display = 'none';
                await login(username, password);
                window.location.href = 'index.html';
            } catch (error) {
                errorDiv.style.display = 'block';
                errorDiv.textContent = error.message || 'Неверный username или пароль';
            }
        });
    }

    // ===== ОБРАБОТЧИК СОЗДАНИЯ ПРОЕКТА =====
    const createForm = document.getElementById('createProjectForm');
    if (createForm) {
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const errorDiv = document.getElementById('createError');
            const successDiv = document.getElementById('createSuccess');

            // Скрываем старые сообщения
            errorDiv.style.display = 'none';
            successDiv.style.display = 'none';

            try {
                // 1. Получаем данные из формы
                const name = document.getElementById('projectName').value.trim();
                const description = document.getElementById('projectDescription').value.trim();
                const file = document.getElementById('glbFile').files[0];
                const visibility = document.querySelector('input[name="visibility"]:checked').value;

                const width = parseInt(document.getElementById('width').value);
                const height = parseInt(document.getElementById('height').value);
                const samples = parseInt(document.getElementById('samples').value);
                const denoiser = document.getElementById('denoiser').value === 'true';
                const gpu = document.getElementById('gpu').value === 'true';

                // ===== КООРДИНАТЫ СОЛНЦА =====
                const sunX = parseFloat(document.getElementById('sunX').value) || 0;
                const sunY = parseFloat(document.getElementById('sunY').value) || 1;
                const sunZ = parseFloat(document.getElementById('sunZ').value) || 0;

                // ===== НАСТРОЙКИ ЦВЕТА =====
                const sunColor = document.getElementById('sunColor').value;
                const bgColor = document.getElementById('bgColor').value;
                const sunSize = parseFloat(document.getElementById('sunSize').value) || 0.1;

                // 2. Валидация
                if (!name) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'Введите название проекта';
                    return;
                }

                if (!file) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'Выберите GLB-файл';
                    return;
                }

                if (file.size > 50 * 1024 * 1024) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'Файл слишком большой. Максимум 50 МБ';
                    return;
                }

                // 3. Загружаем файл
                console.log('📤 Загрузка файла...');
                const fileData = await uploadFile(file);
                console.log('✅ Файл загружен:', fileData);

                // 4. Создаем проект
                const projectData = {
                    render: {
                        width: width,
                        height: height,
                        samples: samples,
                        denoiser: denoiser,
                        gpu: gpu,
                        background: [
                            parseFloat((parseInt(bgColor.slice(1, 3), 16) / 255).toFixed(3)),
                            parseFloat((parseInt(bgColor.slice(3, 5), 16) / 255).toFixed(3)),
                            parseFloat((parseInt(bgColor.slice(5, 7), 16) / 255).toFixed(3))
                        ],
                        sun: {
                            direction: (() => {
                                // Нормализуем координаты точки (радиус сферы = 1.5)
                                const nx = sunX / 1.5;
                                const ny = sunY / 1.5;
                                const nz = sunZ / 1.5;

                                // Получаем полярные углы
                                const theta = Math.acos(Math.max(-1, Math.min(1, ny)));
                                const phi = Math.atan2(nz, nx);

                                // Вычисляем x, y, z при r = 1
                                const x = Math.sin(theta) * Math.cos(phi);
                                const y = Math.cos(theta);
                                const z = Math.sin(theta) * Math.sin(phi);

                                return [
                                    parseFloat(x.toFixed(6)),
                                    parseFloat(y.toFixed(6)),
                                    parseFloat(z.toFixed(6))
                                ];
                            })(),
                            color: [
                                parseFloat((parseInt(sunColor.slice(1, 3), 16) / 255).toFixed(3)),
                                parseFloat((parseInt(sunColor.slice(3, 5), 16) / 255).toFixed(3)),
                                parseFloat((parseInt(sunColor.slice(5, 7), 16) / 255).toFixed(3))
                            ],
                            exponent: Math.round(sunSize * 600)
                        }
                    },
                    project: {
                        name: name,
                        description: description || '',
                        source_file_id: fileData.id,
                        visibility: visibility
                    }
                };

                console.log('📦 Создание проекта:', projectData);
                const result = await createProjectData(projectData);
                console.log('✅ Проект создан:', result);

                // 5. Успех
                successDiv.style.display = 'block';
                successDiv.textContent = '✅ Проект успешно создан! Перенаправление...';

                // 6. Переход на страницу проекта
                setTimeout(() => {
                    window.location.href = `project.html?id=${result.id}`;
                }, 2000);

            } catch (error) {
                console.error('❌ Ошибка:', error);
                errorDiv.style.display = 'block';
                errorDiv.textContent = error.message || 'Ошибка создания проекта';
            }
        });
    }

    // ===== ЗАГРУЗКА ПРОЕКТА =====
    if (currentPage === 'project.html') {
        console.log('🔵 Мы на project.html');
        const params = new URLSearchParams(window.location.search);
        const projectId = params.get('id');
        console.log('🔵 projectId из URL:', projectId);
        if (projectId) {
            console.log('🔵 Вызываю loadProjectDetail с ID:', projectId);
            loadProjectDetail(projectId);
        } else {
            console.error('❌ projectId не найден в URL');
            document.getElementById('projectDetail').innerHTML = `
                <div class="error-message">
                    <p>ID проекта не указан</p>
                    <a href="index.html" class="btn btn-primary">На главную</a>
                </div>
            `;
        }
    }
});



// ===== ЗАГРУЗКА ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ =====
let profilePage = 1;
const PROFILE_PAGE_SIZE = 10;

async function loadProfile(userId = null, page = 1) {
    const container = document.getElementById('profileContent');
    if (!container) return;

    try {
        showLoading('profileContent');

        let user;
        let isOwnProfile = false;

        if (userId) {
            user = await getUserById(userId);
            console.log('👤 Профиль пользователя (чужой):', user);
            isOwnProfile = false;
        } else {
            user = await getCurrentUserProfile();
            console.log('👤 Мой профиль:', user);
            isOwnProfile = true;
        }

        // Загружаем проекты пользователя с пагинацией
        const projectsData = await getUserProjectsById(user.id, page, PROFILE_PAGE_SIZE);
        console.log('📦 Проекты пользователя:', projectsData);

        const allProjects = projectsData.project_list || [];
        const total = projectsData.total || allProjects.length;

        // Определяем количество страниц
        let totalPages = 1;
        if (projectsData.total_pages) {
            totalPages = projectsData.total_pages;
        } else if (projectsData.total) {
            totalPages = Math.ceil(projectsData.total / PROFILE_PAGE_SIZE);
        } else if (allProjects.length === PROFILE_PAGE_SIZE) {
            totalPages = page + 1;
        } else {
            totalPages = page;
        }

        // ВАЖНО: создаем переменную projects для использования в HTML
        const projects = allProjects.slice(0, PROFILE_PAGE_SIZE);

        console.log(`📄 Всего страниц: ${totalPages}, текущая: ${page}, показано проектов: ${projects.length}`);

        container.innerHTML = `
            <div class="profile-page">
                <!-- Карточка пользователя -->
                <div class="profile-card">
                    <div class="profile-header">
                        <div class="profile-avatar-large">
                            <i class="fas fa-user-circle"></i>
                        </div>
                        <div class="profile-info">
                            <h1>${user.username}</h1>
                            <p class="profile-name">${user.name} ${user.surname}</p>
                            ${isOwnProfile ? `<p class="profile-email"><i class="fas fa-envelope"></i> ${user.email}</p>` : ''}
                            <p class="profile-date">
                                <i class="fas fa-calendar"></i> 
                                Зарегистрирован: ${new Date(user.registration_date).toLocaleDateString('ru-RU')}
                            </p>
                            <div class="profile-stats">
                                <span><i class="fas fa-project-diagram"></i> ${projectsData.total || projects.length} проектов</span>
                            </div>
                        </div>
                    </div>

                    ${isOwnProfile ? `
                    <div class="profile-actions">
                        <button class="btn btn-primary" onclick="editProfile()">
                            <i class="fas fa-edit"></i> Редактировать
                        </button>
                        <button class="btn btn-danger" onclick="deleteAccount()">
                            <i class="fas fa-trash"></i> Удалить аккаунт
                        </button>
                    </div>

                    <div id="editForm" style="display:none;" class="edit-form">
                        <h3>✏️ Редактировать профиль</h3>
                        <form id="updateProfileForm">
                            <div class="form-group">
                                <label>Фамилия</label>
                                <input type="text" id="editSurname" value="${user.surname}" required>
                            </div>
                            <div class="form-group">
                                <label>Имя</label>
                                <input type="text" id="editName" value="${user.name}" required>
                            </div>
                            <div class="form-group">
                                <label>Имя пользователя</label>
                                <input type="text" id="editUsername" value="${user.username}" required>
                            </div>
                            <div class="form-group">
                                <label>Email</label>
                                <input type="email" id="editEmail" value="${user.email}" required>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-save"></i> Сохранить
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="cancelEdit()">
                                    <i class="fas fa-times"></i> Отмена
                                </button>
                            </div>
                        </form>
                        <div id="updateError" class="error-message" style="display:none;"></div>
                        <div id="updateSuccess" class="success-message" style="display:none;"></div>
                    </div>
                    ` : `
                    <div class="profile-actions">
                        <span class="profile-note">Публичный профиль</span>
                    </div>
                    `}
                </div>

                <!-- Проекты пользователя -->
                <div class="profile-projects-section">
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
                    
                    <!-- Пагинация -->
                    ${totalPages > 1 ? `
                    <div class="pagination" id="profilePagination">
                        <button class="btn btn-secondary" id="profilePrevPage" ${page <= 1 ? 'disabled' : ''}>
                            <i class="fas fa-chevron-left"></i> Назад
                        </button>
                        <button class="btn btn-secondary" id="profileNextPage" ${page >= totalPages ? 'disabled' : ''}>
                            Вперед <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;

        // Клики на проекты
        document.querySelectorAll('.project-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.id;
                window.location.href = `project.html?id=${id}`;
            });
        });

        // ===== ПАГИНАЦИЯ В ПРОФИЛЕ =====
        const prevBtn = document.getElementById('profilePrevPage');
        const nextBtn = document.getElementById('profileNextPage');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (page > 1) {
                    const newPage = page - 1;
                    profilePage = newPage;
                    loadProfile(userId, newPage);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (page < totalPages) {
                    const newPage = page + 1;
                    profilePage = newPage;
                    loadProfile(userId, newPage);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        }

        // Обработчик обновления профиля (только для своего профиля)
        const updateForm = document.getElementById('updateProfileForm');
        if (updateForm) {
            updateForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const surname = document.getElementById('editSurname').value.trim();
                const name = document.getElementById('editName').value.trim();
                const username = document.getElementById('editUsername').value.trim();
                const email = document.getElementById('editEmail').value.trim();

                const errorDiv = document.getElementById('updateError');
                const successDiv = document.getElementById('updateSuccess');

                if (!surname || !name || !username || !email) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = 'Все поля обязательны для заполнения';
                    return;
                }

                try {
                    errorDiv.style.display = 'none';
                    successDiv.style.display = 'none';

                    await updateCurrentUserProfile(surname, name, username, email);

                    successDiv.style.display = 'block';
                    successDiv.textContent = '✅ Профиль успешно обновлен!';

                    setTimeout(() => {
                        loadProfile();
                    }, 1500);
                } catch (error) {
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = error.message || 'Ошибка обновления профиля';
                }
            });
        }

        setupDropdown();

    } catch (error) {
        console.error('❌ Ошибка загрузки профиля:', error);
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-circle"></i>
                <p>Ошибка загрузки профиля: ${error.message}</p>
                <button onclick="loadProfile(${userId || ''})" class="btn btn-secondary">
                    <i class="fas fa-redo"></i> Повторить
                </button>
            </div>
        `;
    }
}

// ===== ОБНОВЛЕНИЕ ПРОФИЛЯ =====
async function updateCurrentUserProfile(surname, name, username, email) {
    return await apiRequest('/users/about-me', {
        method: 'PUT',
        body: JSON.stringify({
            surname: surname,
            name: name,
            username: username,
            email: email
        })
    });
}

// ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
function setupDropdownHandlers() {
    const avatarBtn = document.getElementById('avatarBtn');
    const dropdownMenu = document.getElementById('dropdownMenu');

    if (avatarBtn && dropdownMenu) {
        avatarBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!dropdownMenu.contains(e.target) && e.target !== avatarBtn) {
                dropdownMenu.classList.remove('show');
            }
        });
    }
}

function editProfile() {
    const form = document.getElementById('editForm');
    if (form) {
        if (form.style.display === 'none' || form.style.display === '') {
            form.style.display = 'block';
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            form.style.display = 'none';
        }
    }
}

function cancelEdit() {
    const form = document.getElementById('editForm');
    if (form) {
        form.style.display = 'none';
    }
}

// ===== УДАЛЕНИЕ АККАУНТА =====
async function deleteCurrentUserProfile() {
    return await apiRequest('/users/about-me', {
        method: 'DELETE'
    });
}

// ===== УДАЛЕНИЕ АККАУНТА С МОДАЛЬНЫМ ОКНОМ =====
function deleteAccount() {
    // Показываем модальное окно
    const modal = document.getElementById('deleteModal');
    const usernameDisplay = document.getElementById('modalUsernameDisplay');
    const confirmInput = document.getElementById('modalConfirmInput');
    const confirmBtn = document.getElementById('modalConfirmDelete');
    const errorDiv = document.getElementById('modalError');

    // Получаем текущего пользователя
    getCurrentUserProfile().then(user => {
        if (user && user.username) {
            usernameDisplay.textContent = user.username;
        }
    }).catch(() => {
        usernameDisplay.textContent = 'username';
    });

    // Сбрасываем состояние
    confirmInput.value = '';
    errorDiv.style.display = 'none';
    confirmBtn.disabled = true;
    modal.style.display = 'flex';

    // Слушаем ввод
    confirmInput.oninput = function() {
        const username = usernameDisplay.textContent;
        if (this.value === username) {
            errorDiv.style.display = 'none';
            confirmBtn.disabled = false;
        } else {
            errorDiv.style.display = 'block';
            confirmBtn.disabled = true;
        }
    };

    // Подтверждение удаления
    confirmBtn.onclick = async function() {
    const username = usernameDisplay.textContent;
    if (confirmInput.value === username) {
        try {
            await deleteCurrentUserProfile();

            // === ПРИНУДИТЕЛЬНЫЙ ВЫХОД ===
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');

            // Закрываем модалку
            const modal = document.getElementById('deleteModal');
            if (modal) modal.style.display = 'none';

            // === ПРИНУДИТЕЛЬНЫЙ РЕДИРЕКТ ===
            window.location.replace('/login.html');

        } catch (error) {
            const errorDiv = document.getElementById('modalError');
            errorDiv.style.display = 'block';
            errorDiv.textContent = 'Ошибка удаления: ' + error.message;
            errorDiv.style.color = '#e74c3c';
        }
    }
    };
}


// ===== ЗАКРЫТИЕ МОДАЛЬНОГО ОКНА =====
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Закрытие по клику вне окна
document.addEventListener('click', function(e) {
    const modal = document.getElementById('deleteModal');
    if (e.target === modal) {
        closeDeleteModal();
    }
});

// Закрытие по Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeDeleteModal();
    }
});



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
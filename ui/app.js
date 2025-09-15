/* app.js — Default login admin/admin */

/* ========================= Globals and API base ========================= */
let authToken = null;

// Определяем базовый URL в зависимости от окружения
const API_BASE_URL = (window.location.hostname === "localhost" && window.location.port !== "3000")
    ? "http://localhost:8003/api/v1"  // Прямое обращение к API Gateway
    : "/api/v1";  // Через nginx proxy (UI контейнер)

console.log('API_BASE_URL:', API_BASE_URL);
console.log('Current location:', window.location.href);

/* ========================= UI helpers ========================= */
function createMessageContainer() {
    const el = document.createElement("div");
    el.id = "message-container";
    el.className = "toast";
    document.body.appendChild(el);
    return el;
}

function showMessage(message, type = "success") {
    const el = document.getElementById("message-container") || createMessageContainer();
    el.textContent = message;
    el.className = `toast ${type}`;
    el.classList.add("show");
    setTimeout(() => {
        el.classList.remove("show");
    }, 3000);
}

/* ========================= HTTP helper ========================= */
async function apiCall(path, method = "GET", body = null) {
    const headers = { "Content-Type": "application/json" };

    // Используем authToken если он установлен
    if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
    }

    const url = `${API_BASE_URL}${path}`;
    console.log(`API Call: ${method} ${url}`);

    try {
        const res = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });

        console.log(`API Response: ${res.status} ${res.statusText}`);

        if (!res.ok) {
            const text = await res.text().catch(() => "");
            throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
        }

        const contentType = res.headers.get("content-type") || "";
        const result = contentType.includes("application/json") ? await res.json() : await res.text();
        console.log('API Result:', result);
        return result;
    } catch (error) {
        console.error('API Call Error:', error);
        throw error;
    }
}

/* ========================= Authentication ========================= */
function showDashboard() {
    console.log('Showing dashboard...');

    const authSection = document.getElementById("auth-section");
    const mainDashboard = document.getElementById("main-dashboard");
    const userInfo = document.getElementById("user-info");
    const userEmailEl = document.getElementById("user-email");

    if (authSection) {
        authSection.classList.add("hidden");
        console.log('Auth section hidden');
    }
    if (mainDashboard) {
        mainDashboard.classList.remove("hidden");
        console.log('Main dashboard shown');
    }
    if (userInfo) {
        userInfo.classList.remove("hidden");
        console.log('User info shown');
    }
    if (userEmailEl) {
        userEmailEl.textContent = "admin@admin.com";
    }

    // Load lists
    Promise.allSettled([
        loadPrompts(),
        loadKnowledgeBases(),
        loadChatbots(),
        loadConversations()
    ]).then(() => showMessage("Dashboard готов", "success"));
}

// Дефолтный логин admin/admin
async function defaultLogin() {
    try {
        console.log('Default login starting...');
        // Устанавливаем токен для админа
        authToken = "admin-token";
        showMessage("Вход выполнен как admin", "success");
        showDashboard();
    } catch (e) {
        console.error('Login error:', e);
        showMessage("Ошибка входа: " + e.message, "error");
    }
}

// Автоматический вход при загрузке страницы
function initApp() {
    console.log('Initializing app...');
    console.log('Document ready state:', document.readyState);
    setTimeout(() => {
        defaultLogin();
    }, 1000);
}

// Запускаем инициализацию
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}

/* Остальной код остается без изменений... */
/* ========================= Auth buttons ========================= */
async function loginWithEmail() {
    const email = document.getElementById("email")?.value || "";
    const password = document.getElementById("password")?.value || "";

    // Проверка на admin/admin
    if (email === "admin" && password === "admin") {
        authToken = "admin-token";
        showMessage("Вход выполнен как admin", "success");
        showDashboard();
    } else {
        showMessage("Неверный логин или пароль", "error");
    }
}

async function registerWithEmail() {
    showMessage("Регистрация симулирована", "success");
    defaultLogin();
}

async function logout() {
    authToken = null;
    showMessage("Выход выполнен", "success");
    document.getElementById("auth-section")?.classList.remove("hidden");
    document.getElementById("main-dashboard")?.classList.add("hidden");
    document.getElementById("user-info")?.classList.add("hidden");
}

/* ========================= Prompts ========================= */
async function createPrompt() {
    const text = document.getElementById("prompt-text")?.value.trim();
    if (!text) return showMessage("Введите текст промпта", "error");

    try {
        await apiCall("/prompts", "POST", { prompt_text: text });
        showMessage("Промпт создан", "success");
        document.getElementById("prompt-text").value = "";
        await loadPrompts();
    } catch (e) {
        showMessage(`Ошибка создания промпта: ${e.message}`, "error");
    }
}

async function loadPrompts() {
    try {
        const result = await apiCall("/prompts", "GET");
        const prompts = result.prompts || result || [];
        const list = document.getElementById("prompts-list");
        if (!list) return;

        list.innerHTML = "";
        if (Array.isArray(prompts) && prompts.length) {
            prompts.forEach((p) => {
                const item = document.createElement("div");
                item.className = "list-item";
                item.innerHTML = `
                    <div class="list-content">
                        <div class="list-title">ID: ${p.id || 'N/A'}</div>
                        <div class="list-meta">Text: ${p.prompt_text || p.text || 'N/A'}</div>
                    </div>
                    <div class="list-actions">
                        <button class="btn btn-danger btn-sm" onclick="deletePrompt('${p.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-magic"></i>
                    <p>Промпты не найдены</p>
                </div>
            `;
        }
    } catch (e) {
        showMessage(`Ошибка загрузки промптов: ${e.message}`, "error");
    }
}

async function deletePrompt(id) {
    try {
        await apiCall(`/prompts/${id}`, "DELETE");
        showMessage("Промпт удален", "success");
        await loadPrompts();
    } catch (e) {
        showMessage(`Ошибка удаления: ${e.message}`, "error");
    }
}

/* ========================= Knowledge Bases ========================= */
async function createKnowledgeBase() {
    const name = document.getElementById("kb-name")?.value.trim();
    if (!name) return showMessage("Введите название базы знаний", "error");

    try {
        await apiCall("/knowledge-bases", "POST", { name });
        showMessage("База знаний создана", "success");
        document.getElementById("kb-name").value = "";
        await loadKnowledgeBases();
    } catch (e) {
        showMessage(`Ошибка создания базы знаний: ${e.message}`, "error");
    }
}

async function loadKnowledgeBases() {
    try {
        const result = await apiCall("/knowledge-bases", "GET");
        const kbs = result.knowledge_bases || result || [];
        const list = document.getElementById("knowledge-bases-list");
        const select = document.getElementById("resource-kb");

        if (list) {
            list.innerHTML = "";
            if (Array.isArray(kbs) && kbs.length) {
                kbs.forEach((kb) => {
                    const item = document.createElement("div");
                    item.className = "list-item";
                    item.innerHTML = `
                        <div class="list-content">
                            <div class="list-title">ID: ${kb.id || 'N/A'}</div>
                            <div class="list-meta">Name: ${kb.name || 'N/A'}</div>
                        </div>
                        <div class="list-actions">
                            <button class="btn btn-danger btn-sm" onclick="deleteKnowledgeBase('${kb.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                    list.appendChild(item);
                });
            } else {
                list.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-database"></i>
                        <p>Базы знаний не найдены</p>
                    </div>
                `;
            }
        }

        if (select) {
            select.innerHTML = '<option value="">Выберите базу знаний</option>';
            if (Array.isArray(kbs)) {
                kbs.forEach((kb) => {
                    const option = document.createElement("option");
                    option.value = kb.id;
                    option.textContent = kb.name;
                    select.appendChild(option);
                });
            }
        }
    } catch (e) {
        showMessage(`Ошибка загрузки баз знаний: ${e.message}`, "error");
    }
}

async function deleteKnowledgeBase(id) {
    try {
        await apiCall(`/knowledge-bases/${id}`, "DELETE");
        showMessage("База знаний удалена", "success");
        await loadKnowledgeBases();
    } catch (e) {
        showMessage(`Ошибка удаления: ${e.message}`, "error");
    }
}

/* ========================= Resources ========================= */
async function createResource() {
    const kbId = document.getElementById("resource-kb")?.value;
    const type = document.getElementById("resource-type")?.value;
    const fileType = document.getElementById("file-type")?.value;

    if (!kbId) return showMessage("Выберите базу знаний", "error");
    if (!type) return showMessage("Выберите тип ресурса", "error");

    try {
        await apiCall("/resources", "POST", {
            knowledge_base_id: kbId,
            resource_type: type,
            file_type: fileType || null
        });
        showMessage("Ресурс создан", "success");
        await loadResources();
    } catch (e) {
        showMessage(`Ошибка создания ресурса: ${e.message}`, "error");
    }
}

async function loadResources() {
    try {
        const result = await apiCall("/resources", "GET");
        const resources = result.resources || result || [];
        const list = document.getElementById("resources-list");
        if (!list) return;

        list.innerHTML = "";
        if (Array.isArray(resources) && resources.length) {
            resources.forEach((r) => {
                const item = document.createElement("div");
                item.className = "list-item";
                item.innerHTML = `
                    <div class="list-content">
                        <div class="list-title">ID: ${r.id || 'N/A'}</div>
                        <div class="list-meta">Type: ${r.resource_type || 'N/A'} | KB ID: ${r.knowledge_base_id || 'N/A'}</div>
                    </div>
                    <div class="list-actions">
                        <button class="btn btn-danger btn-sm" onclick="deleteResource('${r.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <p>Ресурсы не найдены</p>
                </div>
            `;
        }
    } catch (e) {
        showMessage(`Ошибка загрузки ресурсов: ${e.message}`, "error");
    }
}

async function deleteResource(id) {
    try {
        await apiCall(`/resources/${id}`, "DELETE");
        showMessage("Ресурс удален", "success");
        await loadResources();
    } catch (e) {
        showMessage(`Ошибка удаления: ${e.message}`, "error");
    }
}

/* ========================= Chatbots ========================= */
async function createChatbot() {
    const name = document.getElementById("chatbot-name")?.value.trim();
    const model = document.getElementById("chatbot-model")?.value;
    const temperature = parseFloat(document.getElementById("temperature")?.value || "0.7");
    const maxTokens = parseInt(document.getElementById("max-tokens")?.value || "1000");
    const systemPrompt = document.getElementById("system-prompt")?.value.trim();

    if (!name) return showMessage("Введите название чатбота", "error");

    try {
        await apiCall("/chatbots", "POST", {
            name,
            model,
            temperature,
            max_tokens: maxTokens,
            system_prompt: systemPrompt
        });
        showMessage("Чатбот создан", "success");
        document.getElementById("chatbot-name").value = "";
        document.getElementById("system-prompt").value = "";
        await loadChatbots();
    } catch (e) {
        showMessage(`Ошибка создания чатбота: ${e.message}`, "error");
    }
}

async function loadChatbots() {
    try {
        const result = await apiCall("/chatbots", "GET");
        const chatbots = result.chatbots || result || [];
        const list = document.getElementById("chatbots-list");
        const select = document.getElementById("chat-chatbot");

        if (list) {
            list.innerHTML = "";
            if (Array.isArray(chatbots) && chatbots.length) {
                chatbots.forEach((cb) => {
                    const item = document.createElement("div");
                    item.className = "list-item";
                    item.innerHTML = `
                        <div class="list-content">
                            <div class="list-title">ID: ${cb.id || 'N/A'}</div>
                            <div class="list-meta">Name: ${cb.name || 'N/A'} | Model: ${cb.model || 'N/A'}</div>
                        </div>
                        <div class="list-actions">
                            <button class="btn btn-danger btn-sm" onclick="deleteChatbot('${cb.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    `;
                    list.appendChild(item);
                });
            } else {
                list.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-robot"></i>
                        <p>Чатботы не найдены</p>
                    </div>
                `;
            }
        }

        if (select) {
            select.innerHTML = '<option value="">Выберите чатбота</option>';
            if (Array.isArray(chatbots)) {
                chatbots.forEach((cb) => {
                    const option = document.createElement("option");
                    option.value = cb.id;
                    option.textContent = cb.name;
                    select.appendChild(option);
                });
            }
        }
    } catch (e) {
        showMessage(`Ошибка загрузки чатботов: ${e.message}`, "error");
    }
}

async function deleteChatbot(id) {
    try {
        await apiCall(`/chatbots/${id}`, "DELETE");
        showMessage("Чатбот удален", "success");
        await loadChatbots();
    } catch (e) {
        showMessage(`Ошибка удаления: ${e.message}`, "error");
    }
}

/* ========================= Chat/Conversations ========================= */
async function newConversation() {
    const chatbotId = document.getElementById("chat-chatbot")?.value;
    if (!chatbotId) return showMessage("Выберите чатбота", "error");

    try {
        await apiCall("/conversations", "POST", { chatbot_id: chatbotId });
        showMessage("Новая беседа создана", "success");
        await loadConversations();
    } catch (e) {
        showMessage(`Ошибка создания беседы: ${e.message}`, "error");
    }
}

async function loadConversations() {
    try {
        const result = await apiCall("/conversations", "GET");
        const conversations = result.conversations || result || [];
        const list = document.getElementById("conversations-list");
        if (!list) return;

        list.innerHTML = "";
        if (Array.isArray(conversations) && conversations.length) {
            conversations.forEach((conv) => {
                const item = document.createElement("div");
                item.className = "list-item";
                item.innerHTML = `
                    <div class="list-content">
                        <div class="list-title">ID: ${conv.id || 'N/A'}</div>
                        <div class="list-meta">Chatbot ID: ${conv.chatbot_id || 'N/A'}</div>
                    </div>
                    <div class="list-actions">
                        <button class="btn btn-primary btn-sm" onclick="loadMessages('${conv.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteConversation('${conv.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>Диалоги не найдены</p>
                </div>
            `;
        }
    } catch (e) {
        showMessage(`Ошибка загрузки бесед: ${e.message}`, "error");
    }
}

async function deleteConversation(id) {
    try {
        await apiCall(`/conversations/${id}`, "DELETE");
        showMessage("Беседа удалена", "success");
        await loadConversations();
    } catch (e) {
        showMessage(`Ошибка удаления: ${e.message}`, "error");
    }
}

async function loadMessages(conversationId) {
    try {
        const result = await apiCall(`/conversations/${conversationId}/messages`, "GET");
        const messages = result.messages || result || [];
        const container = document.getElementById("chat-messages");
        if (!container) return;

        container.innerHTML = "";
        if (Array.isArray(messages) && messages.length) {
            messages.forEach((msg) => {
                const item = document.createElement("div");
                item.className = "list-item";
                item.innerHTML = `
                    <div class="list-content">
                        <div class="list-title">${msg.role || 'unknown'}</div>
                        <div class="list-meta">${msg.content || msg.message || 'N/A'}</div>
                    </div>
                `;
                container.appendChild(item);
            });
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comment-dots"></i>
                    <p>Нет сообщений</p>
                </div>
            `;
        }

        // Сохраняем ID беседы для отправки сообщений
        window.currentConversationId = conversationId;
        showMessage("Диалог загружен", "success");
    } catch (e) {
        showMessage(`Ошибка загрузки сообщений: ${e.message}`, "error");
    }
}

async function sendMessage() {
    const content = document.getElementById("chat-input")?.value.trim();
    const conversationId = window.currentConversationId;

    if (!content) return showMessage("Введите сообщение", "error");
    if (!conversationId) return showMessage("Выберите беседу", "error");

    try {
        await apiCall(`/conversations/${conversationId}/messages`, "POST", {
            role: "user",
            content
        });
        showMessage("Сообщение отправлено", "success");
        document.getElementById("chat-input").value = "";
        await loadMessages(conversationId);
    } catch (e) {
        showMessage(`Ошибка отправки: ${e.message}`, "error");
    }
}

// Инициализация при загрузке
console.log('App script loaded');

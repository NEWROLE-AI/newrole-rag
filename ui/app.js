/* Ragnarök UI - Firebase Auth Integration */

/* ========================= Globals and Firebase ========================= */
let authToken = null;
let currentUser = null;
let firebase = null;
let auth = null;
let tokenRefreshInterval = null;
let currentSection = 'chat';

// API Configuration
const API_CONFIG = window.API_CONFIG || {
    GATEWAY_URL: "/api/v1",
    ENVIRONMENT: "production"
};

const API_BASE_URL = API_CONFIG.GATEWAY_URL;
console.log('Ragnarök API_BASE_URL:', API_BASE_URL);
console.log('Config loaded:', API_CONFIG);

/* ========================= UI Navigation ========================= */
function showContent(section, clickedElement = null) {
    console.log('Showing content section:', section);
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // If clicked element provided, make it active
    if (clickedElement) {
        clickedElement.classList.add('active');
    } else {
        // Find nav item by section name
        document.querySelectorAll('.nav-item').forEach(item => {
            const span = item.querySelector('span');
            if (span && span.textContent.toLowerCase().includes(section)) {
                item.classList.add('active');
            }
        });
    }
    
    // Hide all content sections
    document.querySelectorAll('.content-section').forEach(contentSection => {
        contentSection.classList.add('hidden');
    });
    
    // Show selected section
    const contentSection = document.getElementById(`${section}-content`);
    if (contentSection) {
        contentSection.classList.remove('hidden');
        currentSection = section;
        
        // Load data for the section (with error handling)
        try {
            switch(section) {
                case 'chat':
                    loadConversations();
                    break;
                case 'bots':
                    loadChatbots();
                    break;
                case 'prompts':
                    loadPrompts();
                    break;
                case 'knowledge':
                    loadKnowledgeBases();
                    break;
                case 'resources':
                    loadResources();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${section} data:`, error);
            showMessage(`Failed to load ${section} data`, "error");
        }
    }
}

function toggleUserMenu() {
    const menu = document.getElementById('user-menu');
    menu.classList.toggle('hidden');
}

/* ========================= Auth Screens Navigation ========================= */
function showAuthChoice() {
    console.log('Showing auth choice screen');
    hideAllAuthScreens();
    document.getElementById('auth-choice-screen').classList.remove('hidden');
}

function showLoginScreen() {
    console.log('Showing login screen');
    hideAllAuthScreens();
    document.getElementById('login-screen').classList.remove('hidden');
    
    // Clear any previous errors
    hideError('login-error');
}

function showRegisterScreen() {
    console.log('Showing register screen');
    hideAllAuthScreens();
    document.getElementById('register-screen').classList.remove('hidden');
    
    // Clear any previous errors
    hideError('register-error');
}

function hideAllAuthScreens() {
    document.getElementById('auth-choice-screen').classList.add('hidden');
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('register-screen').classList.add('hidden');
}

function showMainApp() {
    console.log('Showing main app');
    hideAllAuthScreens();
    document.getElementById('main-app').classList.remove('hidden');
}

/* ========================= Error Handling ========================= */
function showError(errorId, message) {
    const errorDiv = document.getElementById(errorId);
    const errorText = document.getElementById(errorId + '-text');
    
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');
    }
}

function hideError(errorId) {
    const errorDiv = document.getElementById(errorId);
    if (errorDiv) {
        errorDiv.classList.add('hidden');
    }
}

/* ========================= Toast Messages ========================= */
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

/* ========================= Firebase Initialization ========================= */
async function initializeFirebase() {
    const firebaseConfig = window.FIREBASE_CONFIG || {
        apiKey: "demo-key",
        authDomain: "demo.firebaseapp.com",
        projectId: "demo-project",
        storageBucket: "demo.appspot.com",
        messagingSenderId: "123456789",
        appId: "1:123456789:web:demo"
    };

    try {
        // Load Firebase SDK if not already loaded
        if (!window.firebase) {
            await loadFirebaseSDK();
        }

        firebase = window.firebase;
        
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        
        auth = firebase.auth();
        
        // Setup auth state listener for session restoration (NOT auto-login)
        auth.onAuthStateChanged(async (user) => {
            const wasLoggedIn = localStorage.getItem('ragnarok_was_logged_in') === 'true';
            
            if (user && wasLoggedIn) {
                // User has valid session and was previously logged in - restore session
                console.log('Restoring user session:', user.email);
                currentUser = user;
                authToken = await user.getIdToken();
                await handleAuthSuccess(user);
                showMessage("Session restored", "success");
            } else if (user && !wasLoggedIn) {
                // User is authenticated but this is a new login (not restoration)
                console.log('New user login detected:', user.email);
                localStorage.setItem('ragnarok_was_logged_in', 'true');
                // Don't auto-show dashboard - let login functions handle it
            } else {
                // No user or session expired
                console.log('No active session or user signed out');
                localStorage.removeItem('ragnarok_was_logged_in');
                if (document.getElementById('main-app') && !document.getElementById('main-app').classList.contains('hidden')) {
                    // User was logged in but now isn't - show auth screen
                    handleAuthSignOut();
                }
            }
        });
        
        console.log('Firebase initialized successfully - ready for manual login');
        return true;
    } catch (error) {
        console.error('Failed to initialize Firebase:', error);
        throw error;
    }
}

async function loadFirebaseSDK() {
    return new Promise((resolve, reject) => {
        // Firebase App
        const appScript = document.createElement('script');
        appScript.src = 'https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js';
        appScript.onload = () => {
            // Firebase Auth
            const authScript = document.createElement('script');
            authScript.src = 'https://www.gstatic.com/firebasejs/10.7.0/firebase-auth-compat.js';
            authScript.onload = resolve;
            authScript.onerror = reject;
            document.head.appendChild(authScript);
        };
        appScript.onerror = reject;
        document.head.appendChild(appScript);
    });
}

/* ========================= HTTP helper ========================= */
async function apiCall(path, method = "GET", body = null) {
    const headers = { "Content-Type": "application/json" };

    // Проверяем наличие пользователя и токена
    if (!currentUser || !authToken) {
        console.error('No authenticated user or token');
        throw new Error('Authentication required. Please login first.');
    }

    // Получаем актуальный токен
    try {
        authToken = await currentUser.getIdToken();
        headers["Authorization"] = `Bearer ${authToken}`;
    } catch (error) {
        console.error('Failed to get token:', error);
        handleAuthSignOut();
        throw new Error('Authentication expired. Please login again.');
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

        // Handle 401 - token expired or invalid
        if (res.status === 401) {
            console.warn('Authentication failed, token may be expired');
            
            // Try to refresh token if user is authenticated
            if (currentUser) {
                try {
                    authToken = await currentUser.getIdToken(true); // Force refresh
                    // Retry request with new token
                    headers["Authorization"] = `Bearer ${authToken}`;
                    const retryRes = await fetch(url, { 
                        method, 
                        headers, 
                        body: body ? JSON.stringify(body) : null 
                    });
                    
                    if (retryRes.ok) {
                        const contentType = retryRes.headers.get("content-type") || "";
                        return contentType.includes("application/json") 
                            ? await retryRes.json() 
                            : await retryRes.text();
                    }
                } catch (error) {
                    console.error('Failed to refresh token:', error);
                }
            }
            
            // If can't refresh token - logout
            handleAuthSignOut();
            throw new Error('Authentication required');
        }

        if (!res.ok) {
            const text = await res.text().catch(() => "");
            throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
        }

        const contentType = res.headers.get("content-type") || "";
        const result = contentType.includes("application/json") 
            ? await res.json() 
            : await res.text();
        console.log('API Result:', result);
        return result;
    } catch (error) {
        console.error('API Call Error:', error);
        throw error;
    }
}

/* ========================= Authentication ========================= */
async function handleAuthSuccess(user) {
    console.log('Handling auth success for:', user.email);
    
    // Update user info in sidebar
    const userNameEl = document.getElementById("user-name");
    const userEmailEl = document.getElementById("user-email-display");
    const userAvatarEl = document.getElementById("user-avatar");
    
    if (userNameEl) {
        userNameEl.textContent = user.displayName || user.email.split('@')[0];
    }
    if (userEmailEl) {
        userEmailEl.textContent = user.email;
    }
    if (userAvatarEl) {
        const initial = (user.displayName || user.email)[0].toUpperCase();
        userAvatarEl.textContent = initial;
    }

    // Show main app
    showMainApp();
    
    // Setup token auto-refresh
    if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval);
    }
    tokenRefreshInterval = setInterval(async () => {
        if (currentUser) {
            try {
                authToken = await currentUser.getIdToken(true);
                console.log('Token refreshed for:', currentUser.email);
            } catch (error) {
                console.error('Failed to refresh token:', error);
                handleAuthSignOut();
            }
        }
    }, 55 * 60 * 1000); // Every 55 minutes
    
    // Load initial data without navigation element
    showContent('chat', null);
}

function handleAuthSignOut() {
    console.log('Handling auth sign out');
    
    // Clear token refresh interval
    if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval);
        tokenRefreshInterval = null;
    }
    
    // Clear user state and session restoration flag
    authToken = null;
    currentUser = null;
    localStorage.removeItem('ragnarok_was_logged_in');
    
    // Hide main app and show auth choice
    document.getElementById('main-app').classList.add('hidden');
    showAuthChoice();
    
    // Clear all form fields
    clearAllForms();
    
    // Hide user menu if open
    document.getElementById('user-menu').classList.add('hidden');
}

function clearAllForms() {
    // Clear login form
    const loginEmail = document.getElementById("login-email");
    const loginPassword = document.getElementById("login-password");
    if (loginEmail) loginEmail.value = "";
    if (loginPassword) loginPassword.value = "";
    
    // Clear register form
    const registerEmail = document.getElementById("register-email");
    const registerPassword = document.getElementById("register-password");
    const registerConfirm = document.getElementById("register-password-confirm");
    if (registerEmail) registerEmail.value = "";
    if (registerPassword) registerPassword.value = "";
    if (registerConfirm) registerConfirm.value = "";
    
    // Clear all errors
    hideError('login-error');
    hideError('register-error');
}

// These functions are replaced by new navigation system

// App initialization
async function initApp() {
    console.log('Initializing Ragnarök app...');
    
    // Show auth choice screen initially - Firebase onAuthStateChanged will handle session restoration
    showAuthChoice();
    
    try {
        await initializeFirebase();
        console.log('Firebase initialized successfully - checking for existing session');
        
        // Firebase onAuthStateChanged will fire and handle session restoration automatically
        setTimeout(() => {
            // If no session restored after 2 seconds, show ready message
            if (!currentUser) {
                showMessage("Ragnarök is ready", "info");
            }
        }, 2000);
        
    } catch (error) {
        console.error('App initialization failed:', error);
        showMessage("Firebase initialization failed: " + error.message, "error");
    }
}

// Start initialization
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}

/* ========================= Auth buttons ========================= */
// Old auth functions removed - now using handleLogin and handleRegister with forms

async function loginWithGoogle() {
    try {
        if (!auth) {
            throw new Error("Firebase Auth не инициализирован");
        }

        showMessage("Signing in with Google...", "info");
        
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.addScope('email');
        provider.addScope('profile');
        
        const userCredential = await auth.signInWithPopup(provider);
        const user = userCredential.user;
        
        // Save user and token
        currentUser = user;
        authToken = await user.getIdToken();
        
        console.log('Google login successful:', user.email);
        
        // Mark user as logged in for session restoration
        localStorage.setItem('ragnarok_was_logged_in', 'true');
        
        // Register in backend (if new user)
        try {
            await apiCall("/auth/register", "POST", {
                email: user.email,
                display_name: user.displayName || user.email.split('@')[0],
                firebase_uid: user.uid
            });
        } catch (backendError) {
            console.warn('Backend registration failed (user may already exist):', backendError);
            // Don't stop process - user may already exist
        }
        
        await handleAuthSuccess(user);
        showMessage("Successfully signed in with Google!", "success");
        
    } catch (error) {
        console.error('Google login error:', error);
        let errorMessage = getHumanGoogleError(error);
        showMessage(`Google sign-in failed: ${errorMessage}`, "error");
    }
}

async function logout() {
    try {
        showMessage("Signing out...", "info");
        
        // Sign out from Firebase
        if (auth && currentUser) {
            await auth.signOut();
        }
        
        // Handle sign out (clears state and shows auth choice)
        handleAuthSignOut();
        showMessage("Signed out successfully", "success");
        
    } catch (error) {
        console.error('Logout error:', error);
        showMessage(`Sign out failed: ${error.message}`, "error");
        
        // Force logout even on error
        handleAuthSignOut();
    }
}

/* ========================= Prompts ========================= */
async function createPrompt() {
    const text = document.getElementById("prompt-text")?.value.trim();
    if (!text) return showMessage("Please enter prompt text", "error");

    try {
        await apiCall("/prompts", "POST", { prompt_text: text });
        showMessage("Prompt created successfully", "success");
        document.getElementById("prompt-text").value = "";
        await loadPrompts();
    } catch (e) {
        showMessage(`Failed to create prompt: ${e.message}`, "error");
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
                    <p>No prompts found</p>
                </div>
            `;
        }
    } catch (e) {
        console.error('Error loading prompts:', e);
        // Don't show error message for each load failure
    }
}

async function deletePrompt(id) {
    try {
        await apiCall(`/prompts/${id}`, "DELETE");
        showMessage("Prompt deleted", "success");
        await loadPrompts();
    } catch (e) {
        showMessage(`Error удаления: ${e.message}`, "error");
    }
}

/* ========================= Knowledge Bases ========================= */
async function createKnowledgeBase() {
    const name = document.getElementById("kb-name")?.value.trim();
    if (!name) return showMessage("Please enter knowledge base name", "error");

    try {
        await apiCall("/knowledge-bases", "POST", { name });
        showMessage("Knowledge base created", "success");
        document.getElementById("kb-name").value = "";
        await loadKnowledgeBases();
    } catch (e) {
        showMessage(`Error создания базы знаний: ${e.message}`, "error");
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
            select.innerHTML = '<option value="">Please select a knowledge base</option>';
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
        console.error('Error loading knowledge bases:', e);
    }
}

async function deleteKnowledgeBase(id) {
    try {
        await apiCall(`/knowledge-bases/${id}`, "DELETE");
        showMessage("Knowledge base deleted", "success");
        await loadKnowledgeBases();
    } catch (e) {
        showMessage(`Error удаления: ${e.message}`, "error");
    }
}

/* ========================= Resources ========================= */
async function createResource() {
    const kbId = document.getElementById("resource-kb")?.value;
    const type = document.getElementById("resource-type")?.value;
    const fileType = document.getElementById("file-type")?.value;

    if (!kbId) return showMessage("Please select a knowledge base", "error");
    if (!type) return showMessage("Please select resource type", "error");

    try {
        await apiCall("/resources", "POST", {
            knowledge_base_id: kbId,
            resource_type: type,
            file_type: fileType || null
        });
        showMessage("Resource created", "success");
        await loadResources();
    } catch (e) {
        showMessage(`Error создания ресурса: ${e.message}`, "error");
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
        console.error('Error loading resources:', e);
    }
}

async function deleteResource(id) {
    try {
        await apiCall(`/resources/${id}`, "DELETE");
        showMessage("Resource deleted", "success");
        await loadResources();
    } catch (e) {
        showMessage(`Error удаления: ${e.message}`, "error");
    }
}

/* ========================= Chatbots ========================= */
async function createChatbot() {
    const name = document.getElementById("chatbot-name")?.value.trim();
    const model = document.getElementById("chatbot-model")?.value;
    const temperature = parseFloat(document.getElementById("temperature")?.value || "0.7");
    const maxTokens = parseInt(document.getElementById("max-tokens")?.value || "1000");
    const systemPrompt = document.getElementById("system-prompt")?.value.trim();

    if (!name) return showMessage("Please enter chatbot name", "error");

    try {
        await apiCall("/chatbots", "POST", {
            name,
            model,
            temperature,
            max_tokens: maxTokens,
            system_prompt: systemPrompt
        });
        showMessage("Chatbot created", "success");
        document.getElementById("chatbot-name").value = "";
        document.getElementById("system-prompt").value = "";
        await loadChatbots();
    } catch (e) {
        showMessage(`Error создания чатбота: ${e.message}`, "error");
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
            select.innerHTML = '<option value="">Please select a chatbot</option>';
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
        console.error('Error loading chatbots:', e);
    }
}

async function deleteChatbot(id) {
    try {
        await apiCall(`/chatbots/${id}`, "DELETE");
        showMessage("Chatbot deleted", "success");
        await loadChatbots();
    } catch (e) {
        showMessage(`Error удаления: ${e.message}`, "error");
    }
}

/* ========================= Chat/Conversations ========================= */
async function newConversation() {
    const chatbotId = document.getElementById("chat-chatbot")?.value;
    if (!chatbotId) return showMessage("Please select a chatbot", "error");

    try {
        await apiCall("/conversations", "POST", { chatbot_id: chatbotId });
        showMessage("New conversation created", "success");
        await loadConversations();
    } catch (e) {
        showMessage(`Error создания беседы: ${e.message}`, "error");
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
        console.error('Error loading conversations:', e);
    }
}

async function deleteConversation(id) {
    try {
        await apiCall(`/conversations/${id}`, "DELETE");
        showMessage("Conversation deleted", "success");
        await loadConversations();
    } catch (e) {
        showMessage(`Error удаления: ${e.message}`, "error");
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
                    <p>No messages</p>
                </div>
            `;
        }

        // Save conversation ID for sending messages
        window.currentConversationId = conversationId;
        showMessage("Conversation loaded", "success");
    } catch (e) {
        showMessage(`Error загрузки сообщений: ${e.message}`, "error");
    }
}

async function sendMessage() {
    const content = document.getElementById("chat-input")?.value.trim();
    const conversationId = window.currentConversationId;

    if (!content) return showMessage("Please enter a message", "error");
    if (!conversationId) return showMessage("Please select a conversation", "error");

    try {
        await apiCall(`/conversations/${conversationId}/messages`, "POST", {
            role: "user",
            content
        });
        showMessage("Message sent", "success");
        document.getElementById("chat-input").value = "";
        await loadMessages(conversationId);
    } catch (e) {
        showMessage(`Error отправки: ${e.message}`, "error");
    }
}

/* ========================= Form Handlers ========================= */
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const loginBtn = document.getElementById("login-btn");
    const loginBtnText = document.getElementById("login-btn-text");
    const loginLoading = document.getElementById("login-loading");

    // Clear previous errors
    hideError('login-error');
    
    // Human-like validations with better error messages
    if (!email) {
        showError('login-error', "Please enter your email address");
        return;
    }
    
    if (!password) {
        showError('login-error', "Please enter your password");
        return;
    }
    
    if (!email.includes('@')) {
        showError('login-error', "That doesn't look like an email address");
        return;
    }
    
    if (email.endsWith('@') || email.startsWith('@')) {
        showError('login-error', "Please enter a complete email address");
        return;
    }

    // Show loading state
    loginBtn.disabled = true;
    loginBtnText.classList.add('hidden');
    loginLoading.classList.remove('hidden');

    try {
        if (!auth) {
            throw new Error("Firebase Auth is not initialized");
        }
        
        // Firebase authentication
        const userCredential = await auth.signInWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        // Save user and token
        currentUser = user;
        authToken = await user.getIdToken();
        
        console.log('Login successful:', user.email);
        
        // Mark user as logged in for session restoration
        localStorage.setItem('ragnarok_was_logged_in', 'true');
        
        await handleAuthSuccess(user);
        showMessage("Welcome back!", "success");
        
    } catch (error) {
        console.error('Login error:', error);
        let errorMessage = getHumanLoginError(error);
        showError('login-error', errorMessage);
        
    } finally {
        // Reset button state
        loginBtn.disabled = false;
        loginBtnText.classList.remove('hidden');
        loginLoading.classList.add('hidden');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById("register-email").value.trim();
    const password = document.getElementById("register-password").value;
    const confirmPassword = document.getElementById("register-password-confirm").value;
    const registerBtn = document.getElementById("register-btn");
    const registerBtnText = document.getElementById("register-btn-text");
    const registerLoading = document.getElementById("register-loading");

    // Clear previous errors
    hideError('register-error');
    
    // Human-like validations
    if (!email) {
        showError('register-error', "We need your email address to create an account");
        return;
    }
    
    if (!email.includes('@')) {
        showError('register-error', "That doesn't look like an email address");
        return;
    }
    
    if (email.endsWith('@gmail.com') && email.split('@')[0].length < 3) {
        showError('register-error', "Gmail addresses need at least 3 characters before @");
        return;
    }
    
    if (!password) {
        showError('register-error', "Please choose a password");
        return;
    }
    
    if (password.length < 6) {
        showError('register-error', "Password should be at least 6 characters long");
        return;
    }
    
    if (password === email || password === email.split('@')[0]) {
        showError('register-error', "Password can't be the same as your email");
        return;
    }
    
    if (password.toLowerCase() === 'password' || password === '123456') {
        showError('register-error', "Please choose a more secure password");
        return;
    }
    
    if (!confirmPassword) {
        showError('register-error', "Please confirm your password");
        return;
    }
    
    if (password !== confirmPassword) {
        showError('register-error', "Passwords don't match");
        return;
    }

    // Show loading state
    registerBtn.disabled = true;
    registerBtnText.classList.add('hidden');
    registerLoading.classList.remove('hidden');

    try {
        if (!auth) {
            throw new Error("Firebase Auth is not initialized");
        }
        
        // Firebase registration
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        const user = userCredential.user;
        
        // Update profile
        const displayName = email.split('@')[0];
        if (displayName) {
            await user.updateProfile({
                displayName: displayName
            });
        }

        // Save user and token
        currentUser = user;
        authToken = await user.getIdToken();
        
        console.log('Registration successful:', user.email);
        
        // Mark user as logged in for session restoration
        localStorage.setItem('ragnarok_was_logged_in', 'true');
        
        // Register in backend
        try {
            await apiCall("/auth/register", "POST", {
                email: email,
                display_name: displayName,
                firebase_uid: user.uid
            });
        } catch (backendError) {
            console.warn('Backend registration failed:', backendError);
        }

        await handleAuthSuccess(user);
        showMessage("Account created successfully! Welcome to Ragnarök!", "success");
        
    } catch (error) {
        console.error('Registration error:', error);
        let errorMessage = getHumanRegisterError(error);
        showError('register-error', errorMessage);
        
    } finally {
        // Reset button state
        registerBtn.disabled = false;
        registerBtnText.classList.remove('hidden');
        registerLoading.classList.add('hidden');
    }
}

/* ========================= Human Error Messages ========================= */
function getHumanLoginError(error) {
    switch(error.code) {
        case 'auth/user-not-found':
            return "We couldn't find an account with that email. Did you mean to sign up instead?";
        case 'auth/wrong-password':
            return "That password doesn't look right. Try again or reset your password.";
        case 'auth/invalid-email':
            return "That email address doesn't look valid. Please check and try again.";
        case 'auth/user-disabled':
            return "This account has been disabled. Please contact support for help.";
        case 'auth/too-many-requests':
            return "Too many failed login attempts. Please wait a few minutes and try again.";
        case 'auth/network-request-failed':
            return "Connection problem. Please check your internet and try again.";
        case 'auth/invalid-credential':
            return "The login information is incorrect. Please check your email and password.";
        default:
            return `Something went wrong: ${error.message}`;
    }
}

function getHumanRegisterError(error) {
    switch(error.code) {
        case 'auth/email-already-in-use':
            return "Looks like you already have an account with this email. Try signing in instead.";
        case 'auth/weak-password':
            return "Please choose a stronger password. Try adding numbers or special characters.";
        case 'auth/invalid-email':
            return "That email address doesn't look valid. Please double-check it.";
        case 'auth/operation-not-allowed':
            return "Account creation is currently disabled. Please contact support.";
        case 'auth/network-request-failed':
            return "Connection problem. Please check your internet and try again.";
        default:
            return `Something went wrong during registration: ${error.message}`;
    }
}

function getHumanGoogleError(error) {
    switch(error.code) {
        case 'auth/popup-closed-by-user':
            return 'Sign-in was cancelled. Please try again.';
        case 'auth/popup-blocked':
            return 'Pop-up blocked by browser. Please allow pop-ups and try again.';
        case 'auth/cancelled-popup-request':
            return 'Sign-in request was cancelled';
        case 'auth/account-exists-with-different-credential':
            return 'An account with this email already exists using a different sign-in method';
        case 'auth/network-request-failed':
            return 'Network error. Please check your internet connection.';
        default:
            return error.message;
    }
}

// Initialization log
console.log('Ragnarök UI loaded - Firebase Auth Only');
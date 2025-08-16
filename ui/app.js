// Firebase configuration - Replace with your actual config
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};

// Initialize Firebase only if not already initialized
let auth;
try {
    if (typeof firebase !== 'undefined') {
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        auth = firebase.auth();
    } else {
        console.warn('Firebase SDK not loaded. Authentication features will be disabled.');
        // Mock auth object for development
        auth = {
            onAuthStateChanged: (callback) => {
                // Simulate a logged in user for development
                setTimeout(() => {
                    callback({
                        email: 'demo@example.com',
                        getIdToken: () => Promise.resolve('demo-token')
                    });
                }, 1000);
            },
            createUserWithEmailAndPassword: () => Promise.reject(new Error('Firebase not available')),
            signInWithEmailAndPassword: () => Promise.reject(new Error('Firebase not available')),
            signOut: () => Promise.resolve()
        };
    }
} catch (error) {
    console.error('Error initializing Firebase:', error);
}

// API Gateway URL
const API_BASE_URL = window.location.hostname === 'localhost' ?
    'http://localhost:8000/api/v1' : '/api/v1';

let authToken = null;
let currentUser = null;

// Utility functions
function showMessage(message, type = 'success') {
    const messageDiv = document.getElementById('message-container') || createMessageContainer();
    messageDiv.innerHTML = `<div class="${type}-message">${message}</div>`;
    setTimeout(() => {
        messageDiv.innerHTML = '';
    }, 5000);
}

function createMessageContainer() {
    const container = document.createElement('div');
    container.id = 'message-container';
    container.style.position = 'fixed';
    container.style.top = '20px';
    container.style.right = '20px';
    container.style.zIndex = '1000';
    document.body.appendChild(container);
    return container;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

// Auth state observer
auth.onAuthStateChanged(async (user) => {
    if (user) {
        currentUser = user;
        try {
            authToken = await user.getIdToken();
            document.getElementById('auth-section').classList.add('hidden');
            document.getElementById('main-dashboard').classList.remove('hidden');
            document.getElementById('user-info').classList.remove('hidden');
            document.getElementById('user-email').textContent = user.email;

            // Load initial data
            await Promise.all([
                loadPrompts(),
                loadKnowledgeBases(),
                loadChatbots(),
                loadConversations()
            ]);
        } catch (error) {
            console.error('Error getting user token:', error);
            showMessage('Error getting authentication token', 'error');
        }
    } else {
        currentUser = null;
        authToken = null;
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('main-dashboard').classList.add('hidden');
        document.getElementById('user-info').classList.add('hidden');
    }
});

// Authentication functions
async function register() {
    const email = document.getElementById('auth-email').value.trim();
    const password = document.getElementById('auth-password').value;
    const displayName = document.getElementById('display-name').value.trim();

    if (!email || !password) {
        showMessage('Please fill in email and password', 'error');
        return;
    }

    if (!validateEmail(email)) {
        showMessage('Please enter a valid email address', 'error');
        return;
    }

    if (!validatePassword(password)) {
        showMessage('Password must be at least 6 characters long', 'error');
        return;
    }

    try {
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        if (displayName) {
            await userCredential.user.updateProfile({
                displayName: displayName
            });
        }

        // Register user in API Gateway
        const token = await userCredential.user.getIdToken();
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                email: email,
                password: password,
                display_name: displayName || ''
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Registration failed');
        }

        showMessage('Registration successful!');
        clearAuthForm();
    } catch (error) {
        showMessage('Registration failed: ' + error.message, 'error');
    }
}

async function login() {
    const email = document.getElementById('auth-email').value.trim();
    const password = document.getElementById('auth-password').value;

    if (!email || !password) {
        showMessage('Please fill in email and password', 'error');
        return;
    }

    if (!validateEmail(email)) {
        showMessage('Please enter a valid email address', 'error');
        return;
    }

    try {
        await auth.signInWithEmailAndPassword(email, password);
        showMessage('Login successful!');
        clearAuthForm();
    } catch (error) {
        showMessage('Login failed: ' + error.message, 'error');
    }
}

async function logout() {
    try {
        await auth.signOut();
        showMessage('Logged out successfully!');
    } catch (error) {
        showMessage('Logout failed: ' + error.message, 'error');
    }
}

function clearAuthForm() {
    document.getElementById('auth-email').value = '';
    document.getElementById('auth-password').value = '';
    document.getElementById('display-name').value = '';
}

// API helper function
async function apiCall(endpoint, method = 'GET', data = null) {
    if (!authToken) {
        throw new Error('Not authenticated');
    }

    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        }
    };

    if (data && method !== 'GET') {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch {
                errorData = { detail: errorText || 'Unknown error' };
            }
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            throw new Error('Unable to connect to server. Please check your connection.');
        }
        throw error;
    }
}

// Prompts functions
async function createPrompt() {
    const text = document.getElementById('prompt-text').value.trim();
    if (!text) {
        showMessage('Please enter prompt text', 'error');
        return;
    }

    try {
        await apiCall('/prompts', 'POST', { text: text });
        showMessage('Prompt created successfully!');
        document.getElementById('prompt-text').value = '';
        await loadPrompts();
    } catch (error) {
        showMessage('Failed to create prompt: ' + error.message, 'error');
    }
}

async function loadPrompts() {
    try {
        const result = await apiCall('/prompts');
        const list = document.getElementById('prompts-list');
        list.innerHTML = '';

        // Handle different possible response structures
        const prompts = result.prompts || result || [];

        if (Array.isArray(prompts) && prompts.length > 0) {
            prompts.forEach(prompt => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <h4>Prompt ${prompt.id || 'Unknown'}</h4>
                    <p><strong>Text:</strong> ${prompt.text || 'No text'}</p>
                    <p><strong>Created:</strong> ${prompt.created_at ? new Date(prompt.created_at).toLocaleDateString() : 'Unknown'}</p>
                `;
                list.appendChild(div);
            });
        } else {
            list.innerHTML = '<p>No prompts found. Create your first prompt!</p>';
        }
    } catch (error) {
        showMessage('Failed to load prompts: ' + error.message, 'error');
        document.getElementById('prompts-list').innerHTML = '<p>Error loading prompts</p>';
    }
}

// Knowledge Bases functions
async function createKnowledgeBase() {
    const name = document.getElementById('kb-name').value.trim();
    if (!name) {
        showMessage('Please enter knowledge base name', 'error');
        return;
    }

    try {
        await apiCall('/knowledge-bases', 'POST', { knowledge_base_name: name });
        showMessage('Knowledge base created successfully!');
        document.getElementById('kb-name').value = '';
        await loadKnowledgeBases();
    } catch (error) {
        showMessage('Failed to create knowledge base: ' + error.message, 'error');
    }
}

async function loadKnowledgeBases() {
    try {
        const result = await apiCall('/knowledge-bases');
        const list = document.getElementById('kb-list');
        const select = document.getElementById('resource-kb-select');

        list.innerHTML = '';
        select.innerHTML = '<option value="">Select Knowledge Base</option>';

        // Handle different possible response structures
        const knowledgeBases = result.knowledge_bases || result || [];

        if (Array.isArray(knowledgeBases) && knowledgeBases.length > 0) {
            knowledgeBases.forEach(kb => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <h4>${kb.name || kb.knowledge_base_name || 'Unnamed'}</h4>
                    <p><strong>ID:</strong> ${kb.id || 'Unknown'}</p>
                    <p><strong>Created:</strong> ${kb.created_at ? new Date(kb.created_at).toLocaleDateString() : 'Unknown'}</p>
                `;
                list.appendChild(div);

                const option = document.createElement('option');
                option.value = kb.id || '';
                option.textContent = kb.name || kb.knowledge_base_name || 'Unnamed';
                select.appendChild(option);
            });
        } else {
            list.innerHTML = '<p>No knowledge bases found. Create your first knowledge base!</p>';
        }
    } catch (error) {
        showMessage('Failed to load knowledge bases: ' + error.message, 'error');
        document.getElementById('kb-list').innerHTML = '<p>Error loading knowledge bases</p>';
    }
}

// Resources functions
async function createResource() {
    const knowledgeBaseId = document.getElementById('resource-kb-select').value;
    const resourceType = document.getElementById('resource-type').value;
    const fileType = document.getElementById('resource-file-type').value;

    if (!knowledgeBaseId) {
        showMessage('Please select a knowledge base', 'error');
        return;
    }

    try {
        const data = {
            knowledge_base_id: knowledgeBaseId,
            resource_type: resourceType
        };

        if (fileType) {
            data.file_type = fileType;
        }

        const result = await apiCall('/resources', 'POST', data);
        showMessage('Resource created successfully!');
        console.log('Resource creation result:', result);
    } catch (error) {
        showMessage('Failed to create resource: ' + error.message, 'error');
    }
}

// Chatbots functions
async function createChatbot() {
    const name = document.getElementById('chatbot-name').value.trim();
    const model = document.getElementById('chatbot-model').value;
    const temperature = parseFloat(document.getElementById('chatbot-temperature').value);
    const maxTokens = parseInt(document.getElementById('chatbot-max-tokens').value);
    const systemPrompt = document.getElementById('chatbot-system-prompt').value.trim();

    if (!name) {
        showMessage('Please enter chatbot name', 'error');
        return;
    }

    if (isNaN(temperature) || temperature < 0 || temperature > 2) {
        showMessage('Temperature must be between 0 and 2', 'error');
        return;
    }

    if (isNaN(maxTokens) || maxTokens < 1) {
        showMessage('Max tokens must be a positive number', 'error');
        return;
    }

    try {
        await apiCall('/chatbots', 'POST', {
            name: name,
            model: model,
            temperature: temperature,
            max_tokens: maxTokens,
            system_prompt: systemPrompt
        });
        showMessage('Chatbot created successfully!');
        clearChatbotForm();
        await loadChatbots();
    } catch (error) {
        showMessage('Failed to create chatbot: ' + error.message, 'error');
    }
}

function clearChatbotForm() {
    document.getElementById('chatbot-name').value = '';
    document.getElementById('chatbot-model').value = 'gpt-3.5-turbo';
    document.getElementById('chatbot-temperature').value = '0.7';
    document.getElementById('chatbot-max-tokens').value = '1000';
    document.getElementById('chatbot-system-prompt').value = '';
}

async function loadChatbots() {
    try {
        const result = await apiCall('/chatbots');
        const list = document.getElementById('chatbots-list');
        const select = document.getElementById('chatbot-select');

        list.innerHTML = '';
        select.innerHTML = '<option value="">Select a chatbot</option>';

        // Handle different possible response structures
        const chatbots = result.chatbots || result || [];

        if (Array.isArray(chatbots) && chatbots.length > 0) {
            chatbots.forEach(chatbot => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <h4>${chatbot.name || 'Unnamed'}</h4>
                    <p><strong>Model:</strong> ${chatbot.model || 'Unknown'}</p>
                    <p><strong>Temperature:</strong> ${chatbot.temperature || 'N/A'}</p>
                    <p><strong>Max Tokens:</strong> ${chatbot.max_tokens || 'N/A'}</p>
                    ${chatbot.system_prompt ? `<p><strong>System Prompt:</strong> ${chatbot.system_prompt}</p>` : ''}
                `;
                list.appendChild(div);

                const option = document.createElement('option');
                option.value = chatbot.id || '';
                option.textContent = chatbot.name || 'Unnamed';
                select.appendChild(option);
            });
        } else {
            list.innerHTML = '<p>No chatbots found. Create your first chatbot!</p>';
        }
    } catch (error) {
        showMessage('Failed to load chatbots: ' + error.message, 'error');
        document.getElementById('chatbots-list').innerHTML = '<p>Error loading chatbots</p>';
    }
}

// Chat functions
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    const chatbotId = document.getElementById('chatbot-select').value;

    if (!message) {
        showMessage('Please enter a message', 'error');
        return;
    }

    if (!chatbotId) {
        showMessage('Please select a chatbot', 'error');
        return;
    }

    const conversationId = document.getElementById('conversation-select').value;

    try {
        displayMessage(message, 'user');
        input.value = '';

        let result;
        const messageData = {
            message: message,
            chatbot_id: chatbotId
        };

        if (conversationId) {
            // Send message to existing conversation
            result = await apiCall(`/conversations/${conversationId}/messages`, 'POST', messageData);
        } else {
            // Create new conversation
            result = await apiCall('/conversations', 'POST', messageData);
            // Reload conversations to include the new one
            await loadConversations();
        }

        if (result && result.response) {
            displayMessage(result.response, 'ai');
        } else {
            displayMessage('No response received', 'ai');
        }

    } catch (error) {
        showMessage('Failed to send message: ' + error.message, 'error');
        displayMessage('Error: ' + error.message, 'ai');
    }
}

function displayMessage(message, type) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${type}-message`;
    div.textContent = message;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function loadConversations() {
    try {
        const result = await apiCall('/conversations');
        const select = document.getElementById('conversation-select');
        select.innerHTML = '<option value="">Create new conversation</option>';

        // Handle different possible response structures
        const conversations = result.conversations || result || [];

        if (Array.isArray(conversations) && conversations.length > 0) {
            conversations.forEach(conv => {
                const option = document.createElement('option');
                option.value = conv.id || '';
                const date = conv.created_at ? new Date(conv.created_at).toLocaleDateString() : 'Unknown date';
                option.textContent = `${(conv.id || 'Unknown').substring(0, 8)}... - ${date}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        showMessage('Failed to load conversations: ' + error.message, 'error');
    }
}

function handleMessageKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Load conversation messages when conversation is selected
document.addEventListener('DOMContentLoaded', function() {
    const conversationSelect = document.getElementById('conversation-select');
    if (conversationSelect) {
        conversationSelect.addEventListener('change', async function() {
            const conversationId = this.value;
            const chatContainer = document.getElementById('chat-messages');

            if (conversationId) {
                try {
                    // Clear current messages
                    chatContainer.innerHTML = '<p>Loading conversation...</p>';
                    // Note: You might want to add an endpoint to get conversation messages
                    // const result = await apiCall(`/conversations/${conversationId}/messages`);
                    // Display messages...
                    chatContainer.innerHTML = '<p>Conversation selected. Start chatting!</p>';
                } catch (error) {
                    showMessage('Failed to load conversation messages: ' + error.message, 'error');
                    chatContainer.innerHTML = '<p>Error loading conversation</p>';
                }
            } else {
                chatContainer.innerHTML = '';
            }
        });
    }
});

<old_str>// Firebase configuration
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "123456789",
    appId: "your-app-id"
};

// Initialize Firebase only if not already initialized
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}
const auth = firebase.auth();

// API Gateway URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

let authToken = null;
let currentUser = null;

// Auth state observer
auth.onAuthStateChanged((user) => {
    if (user) {
        currentUser = user;
        user.getIdToken().then((token) => {
            authToken = token;
            document.getElementById('auth-section').classList.add('hidden');
            document.getElementById('main-dashboard').classList.remove('hidden');
            document.getElementById('user-info').classList.remove('hidden');
            document.getElementById('user-email').textContent = user.email;
        });
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
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const displayName = document.getElementById('display-name').value;
    
    try {
        const userCredential = await auth.createUserWithEmailAndPassword(email, password);
        await userCredential.user.updateProfile({
            displayName: displayName
        });
        
        // Register user in API Gateway
        const token = await userCredential.user.getIdToken();
        await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                email: email,
                display_name: displayName
            })
        });
        
        alert('Registration successful!');
    } catch (error) {
        alert('Registration failed: ' + error.message);
    }
}

async function login() {
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    
    try {
        await auth.signInWithEmailAndPassword(email, password);
        alert('Login successful!');
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

async function logout() {
    try {
        await auth.signOut();
        alert('Logged out successfully!');
    } catch (error) {
        alert('Logout failed: ' + error.message);
    }
}

// API helper function
async function apiCall(endpoint, method = 'GET', data = null) {
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
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    return await response.json();
}

// Prompts functions
async function createPrompt() {
    const text = document.getElementById('prompt-text').value;
    if (!text) {
        alert('Please enter prompt text');
        return;
    }
    
    try {
        const result = await apiCall('/prompts', 'POST', { text: text });
        alert('Prompt created successfully!');
        document.getElementById('prompt-text').value = '';
        loadPrompts();
    } catch (error) {
        alert('Failed to create prompt: ' + error.message);
    }
}

async function loadPrompts() {
    try {
        const result = await apiCall('/prompts');
        const list = document.getElementById('prompts-list');
        list.innerHTML = '';
        
        result.prompts.forEach(prompt => {
            const div = document.createElement('div');
            div.className = 'list-item';
            div.innerHTML = `<strong>ID:</strong> ${prompt.id}<br><strong>Text:</strong> ${prompt.text}`;
            list.appendChild(div);
        });
    } catch (error) {
        alert('Failed to load prompts: ' + error.message);
    }
}

// Knowledge Bases functions
async function createKnowledgeBase() {
    const name = document.getElementById('kb-name').value;
    if (!name) {
        alert('Please enter knowledge base name');
        return;
    }
    
    try {
        const result = await apiCall('/knowledge-bases', 'POST', { knowledge_base_name: name });
        alert('Knowledge base created successfully!');
        document.getElementById('kb-name').value = '';
        loadKnowledgeBases();
    } catch (error) {
        alert('Failed to create knowledge base: ' + error.message);
    }
}

async function loadKnowledgeBases() {
    try {
        const result = await apiCall('/knowledge-bases');
        const list = document.getElementById('kb-list');
        list.innerHTML = '';
        
        result.knowledge_bases.forEach(kb => {
            const div = document.createElement('div');
            div.className = 'list-item';
            div.innerHTML = `<strong>ID:</strong> ${kb.id}<br><strong>Name:</strong> ${kb.name}`;
            list.appendChild(div);
        });
    } catch (error) {
        alert('Failed to load knowledge bases: ' + error.message);
    }
}

// Chatbots functions
async function createChatbot() {
    const name = document.getElementById('chatbot-name').value;
    const model = document.getElementById('chatbot-model').value;
    const temperature = parseFloat(document.getElementById('chatbot-temperature').value);
    const maxTokens = parseInt(document.getElementById('chatbot-max-tokens').value);
    const systemPrompt = document.getElementById('chatbot-system-prompt').value;
    
    if (!name) {
        alert('Please enter chatbot name');
        return;
    }
    
    try {
        const result = await apiCall('/chatbots', 'POST', {
            name: name,
            model: model,
            temperature: temperature,
            max_tokens: maxTokens,
            system_prompt: systemPrompt
        });
        alert('Chatbot created successfully!');
        clearChatbotForm();
        loadChatbots();
    } catch (error) {
        alert('Failed to create chatbot: ' + error.message);
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
        list.innerHTML = '';
        
        result.chatbots.forEach(chatbot => {
            const div = document.createElement('div');
            div.className = 'list-item';
            div.innerHTML = `<strong>Name:</strong> ${chatbot.name}<br><strong>Model:</strong> ${chatbot.model}<br><strong>Temperature:</strong> ${chatbot.temperature}`;
            list.appendChild(div);
        });
    } catch (error) {
        alert('Failed to load chatbots: ' + error.message);
    }
}

// Chat functions
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    const conversationId = document.getElementById('conversation-select').value;
    
    try {
        let result;
        if (conversationId) {
            // Send message to existing conversation
            result = await apiCall(`/conversations/${conversationId}/messages`, 'POST', {
                message: message
            });
        } else {
            // Create new conversation
            result = await apiCall('/conversations', 'POST', {
                message: message
            });
        }
        
        displayMessage(message, 'user');
        displayMessage(result.response, 'ai');
        input.value = '';
        
        if (!conversationId) {
            loadConversations();
        }
    } catch (error) {
        alert('Failed to send message: ' + error.message);
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
        
        result.conversations.forEach(conv => {
            const option = document.createElement('option');
            option.value = conv.id;
            option.textContent = `${conv.id} - ${new Date(conv.created_at).toLocaleDateString()}`;
            select.appendChild(option);
        });
    } catch (error) {
        alert('Failed to load conversations: ' + error.message);
    }
}

function handleMessageKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}</old_str>
<new_str>// Firebase configuration - Replace with your actual config
const firebaseConfig = {
    apiKey: "your-api-key-here",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "123456789",
    appId: "your-app-id-here"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// API Gateway URL
const API_BASE_URL = window.location.hostname === 'localhost' ? 
    'http://localhost:8000/api/v1' : '/api/v1';

let authToken = null;
let currentUser = null;

// Utility functions
function showMessage(message, type = 'success') {
    const messageDiv = document.getElementById('auth-message');
    messageDiv.innerHTML = `<div class="${type}-message">${message}</div>`;
    setTimeout(() => {
        messageDiv.innerHTML = '';
    }, 5000);
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
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const displayName = document.getElementById('display-name').value;
    
    if (!email || !password) {
        showMessage('Please fill in email and password', 'error');
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
        await fetch(`${API_BASE_URL}/auth/register`, {
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
        
        showMessage('Registration successful!');
        clearAuthForm();
    } catch (error) {
        showMessage('Registration failed: ' + error.message, 'error');
    }
}

async function login() {
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    
    if (!email || !password) {
        showMessage('Please fill in email and password', 'error');
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
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'API call failed');
    }
    
    return await response.json();
}

// Prompts functions
async function createPrompt() {
    const text = document.getElementById('prompt-text').value;
    if (!text.trim()) {
        showMessage('Please enter prompt text', 'error');
        return;
    }
    
    try {
        await apiCall('/prompts', 'POST', { text: text.trim() });
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
        
        if (result.prompts && result.prompts.length > 0) {
            result.prompts.forEach(prompt => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <h4>Prompt ${prompt.id}</h4>
                    <p><strong>Text:</strong> ${prompt.text}</p>
                    <p><strong>Created:</strong> ${new Date(prompt.created_at || Date.now()).toLocaleDateString()}</p>
                `;
                list.appendChild(div);
            });
        } else {
            list.innerHTML = '<p>No prompts found. Create your first prompt!</p>';
        }
    } catch (error) {
        showMessage('Failed to load prompts: ' + error.message, 'error');
    }
}

// Knowledge Bases functions
async function createKnowledgeBase() {
    const name = document.getElementById('kb-name').value;
    if (!name.trim()) {
        showMessage('Please enter knowledge base name', 'error');
        return;
    }
    
    try {
        await apiCall('/knowledge-bases', 'POST', { knowledge_base_name: name.trim() });
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
        
        if (result.knowledge_bases && result.knowledge_bases.length > 0) {
            result.knowledge_bases.forEach(kb => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <h4>${kb.name}</h4>
                    <p><strong>ID:</strong> ${kb.id}</p>
                    <p><strong>Created:</strong> ${new Date(kb.created_at || Date.now()).toLocaleDateString()}</p>
                `;
                list.appendChild(div);
                
                const option = document.createElement('option');
                option.value = kb.id;
                option.textContent = kb.name;
                select.appendChild(option);
            });
        } else {
            list.innerHTML = '<p>No knowledge bases found. Create your first knowledge base!</p>';
        }
    } catch (error) {
        showMessage('Failed to load knowledge bases: ' + error.message, 'error');
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
    const name = document.getElementById('chatbot-name').value;
    const model = document.getElementById('chatbot-model').value;
    const temperature = parseFloat(document.getElementById('chatbot-temperature').value);
    const maxTokens = parseInt(document.getElementById('chatbot-max-tokens').value);
    const systemPrompt = document.getElementById('chatbot-system-prompt').value;
    
    if (!name.trim()) {
        showMessage('Please enter chatbot name', 'error');
        return;
    }
    
    try {
        await apiCall('/chatbots', 'POST', {
            name: name.trim(),
            model: model,
            temperature: temperature,
            max_tokens: maxTokens,
            system_prompt: systemPrompt.trim()
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
        
        if (result.chatbots && result.chatbots.length > 0) {
            result.chatbots.forEach(chatbot => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <h4>${chatbot.name}</h4>
                    <p><strong>Model:</strong> ${chatbot.model}</p>
                    <p><strong>Temperature:</strong> ${chatbot.temperature}</p>
                    <p><strong>Max Tokens:</strong> ${chatbot.max_tokens}</p>
                    ${chatbot.system_prompt ? `<p><strong>System Prompt:</strong> ${chatbot.system_prompt}</p>` : ''}
                `;
                list.appendChild(div);
                
                const option = document.createElement('option');
                option.value = chatbot.id;
                option.textContent = chatbot.name;
                select.appendChild(option);
            });
        } else {
            list.innerHTML = '<p>No chatbots found. Create your first chatbot!</p>';
        }
    } catch (error) {
        showMessage('Failed to load chatbots: ' + error.message, 'error');
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
        if (conversationId) {
            // Send message to existing conversation
            result = await apiCall(`/conversations/${conversationId}/messages`, 'POST', {
                message: message,
                chatbot_id: chatbotId
            });
        } else {
            // Create new conversation
            result = await apiCall('/conversations', 'POST', {
                message: message,
                chatbot_id: chatbotId
            });
            // Reload conversations to include the new one
            await loadConversations();
        }
        
        if (result.response) {
            displayMessage(result.response, 'ai');
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
        
        if (result.conversations && result.conversations.length > 0) {
            result.conversations.forEach(conv => {
                const option = document.createElement('option');
                option.value = conv.id;
                option.textContent = `${conv.id.substring(0, 8)}... - ${new Date(conv.created_at || Date.now()).toLocaleDateString()}`;
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
document.getElementById('conversation-select').addEventListener('change', async function() {
    const conversationId = this.value;
    const chatContainer = document.getElementById('chat-messages');
    
    if (conversationId) {
        try {
            // Clear current messages
            chatContainer.innerHTML = '';
            // Note: You might want to add an endpoint to get conversation messages
            // const result = await apiCall(`/conversations/${conversationId}/messages`);
            // Display messages...
        } catch (error) {
            showMessage('Failed to load conversation messages: ' + error.message, 'error');
        }
    } else {
        chatContainer.innerHTML = '';
    }
});</new_str>

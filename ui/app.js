
const API_BASE_URL = 'http://localhost:8000/api/v1';
let currentUser = null;
let authToken = null;

// Auth state management
firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
        currentUser = user;
        authToken = await user.getIdToken();
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        document.getElementById('user-info').classList.remove('hidden');
        document.getElementById('user-email').textContent = user.email;
        await loadDashboard();
    } else {
        currentUser = null;
        authToken = null;
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('user-info').classList.add('hidden');
    }
});

// Auth functions
document.getElementById('signin-btn').addEventListener('click', async () => {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        await firebase.auth().signInWithEmailAndPassword(email, password);
    } catch (error) {
        showAuthError(error.message);
    }
});

document.getElementById('signup-btn').addEventListener('click', async () => {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const displayName = document.getElementById('displayName').value;
    
    try {
        const result = await firebase.auth().createUserWithEmailAndPassword(email, password);
        if (displayName) {
            await result.user.updateProfile({ displayName });
        }
        
        // Register user in backend
        await apiCall('POST', '/auth/register', {
            email,
            password,
            display_name: displayName
        });
    } catch (error) {
        showAuthError(error.message);
    }
});

document.getElementById('logout-btn').addEventListener('click', () => {
    firebase.auth().signOut();
});

// API helper
async function apiCall(method, endpoint, data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    return response.json();
}

// Tab management
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        showTab(tabName);
    });
});

function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Load content based on tab
    switch(tabName) {
        case 'knowledge-bases':
            loadKnowledgeBases();
            break;
        case 'chatbots':
            loadChatbots();
            break;
        case 'conversations':
            loadConversations();
            break;
        case 'prompts':
            loadPrompts();
            break;
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const [kbData, chatbotData, conversationData] = await Promise.all([
            apiCall('GET', '/knowledge-bases'),
            apiCall('GET', '/chatbots'),
            apiCall('GET', '/conversations')
        ]);
        
        document.getElementById('kb-count').textContent = kbData.knowledge_bases?.length || 0;
        document.getElementById('chatbot-count').textContent = chatbotData.chatbots?.length || 0;
        document.getElementById('conversation-count').textContent = conversationData.conversations?.length || 0;
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Knowledge Bases
async function loadKnowledgeBases() {
    try {
        const data = await apiCall('GET', '/knowledge-bases');
        const kbList = document.getElementById('kb-list');
        kbList.innerHTML = '';
        
        data.knowledge_bases?.forEach(kb => {
            const div = document.createElement('div');
            div.className = 'bg-gray-50 p-4 rounded border';
            div.innerHTML = `
                <h3 class="font-bold">${kb.name}</h3>
                <p class="text-gray-600">${kb.description || 'No description'}</p>
                <p class="text-sm text-gray-500">Created: ${new Date(kb.created_at).toLocaleDateString()}</p>
            `;
            kbList.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading knowledge bases:', error);
    }
}

// Chatbots
async function loadChatbots() {
    try {
        const data = await apiCall('GET', '/chatbots');
        const chatbotList = document.getElementById('chatbot-list');
        chatbotList.innerHTML = '';
        
        data.chatbots?.forEach(chatbot => {
            const div = document.createElement('div');
            div.className = 'bg-gray-50 p-4 rounded border';
            div.innerHTML = `
                <h3 class="font-bold">${chatbot.name}</h3>
                <p class="text-gray-600">Model: ${chatbot.model}</p>
                <p class="text-sm text-gray-500">Created: ${new Date(chatbot.created_at).toLocaleDateString()}</p>
            `;
            chatbotList.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading chatbots:', error);
    }
}

// Conversations
async function loadConversations() {
    try {
        const data = await apiCall('GET', '/conversations');
        const conversationList = document.getElementById('conversation-list');
        conversationList.innerHTML = '';
        
        data.conversations?.forEach(conversation => {
            const div = document.createElement('div');
            div.className = 'bg-gray-50 p-4 rounded border cursor-pointer hover:bg-gray-100';
            div.innerHTML = `
                <h3 class="font-bold">${conversation.title || 'Untitled Conversation'}</h3>
                <p class="text-sm text-gray-500">Created: ${new Date(conversation.created_at).toLocaleDateString()}</p>
            `;
            div.addEventListener('click', () => openConversation(conversation.id));
            conversationList.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

// Prompts
async function loadPrompts() {
    try {
        const data = await apiCall('GET', '/prompts');
        const promptList = document.getElementById('prompt-list');
        promptList.innerHTML = '';
        
        data.prompts?.forEach(prompt => {
            const div = document.createElement('div');
            div.className = 'bg-gray-50 p-4 rounded border';
            div.innerHTML = `
                <p class="text-gray-700">${prompt.text.substring(0, 100)}...</p>
                <p class="text-sm text-gray-500">Created: ${new Date(prompt.created_at).toLocaleDateString()}</p>
            `;
            promptList.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading prompts:', error);
    }
}

// Create buttons event listeners
document.getElementById('create-kb-btn').addEventListener('click', () => {
    showCreateKnowledgeBaseModal();
});

document.getElementById('create-chatbot-btn').addEventListener('click', () => {
    showCreateChatbotModal();
});

document.getElementById('new-conversation-btn').addEventListener('click', () => {
    createNewConversation();
});

document.getElementById('create-prompt-btn').addEventListener('click', () => {
    showCreatePromptModal();
});

// Modal functions
function showModal(content) {
    document.getElementById('modal-content').innerHTML = content;
    document.getElementById('modal-overlay').classList.remove('hidden');
}

function hideModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
}

function showCreateKnowledgeBaseModal() {
    showModal(`
        <h3 class="text-xl mb-4">Create Knowledge Base</h3>
        <div class="mb-4">
            <input type="text" id="kb-name" placeholder="Name" class="w-full p-2 border rounded">
        </div>
        <div class="mb-4">
            <textarea id="kb-description" placeholder="Description" class="w-full p-2 border rounded h-20"></textarea>
        </div>
        <div class="flex gap-2">
            <button onclick="createKnowledgeBase()" class="bg-blue-500 text-white px-4 py-2 rounded">Create</button>
            <button onclick="hideModal()" class="bg-gray-500 text-white px-4 py-2 rounded">Cancel</button>
        </div>
    `);
}

async function createKnowledgeBase() {
    const name = document.getElementById('kb-name').value;
    const description = document.getElementById('kb-description').value;
    
    try {
        await apiCall('POST', '/knowledge-bases', { name, description });
        hideModal();
        loadKnowledgeBases();
    } catch (error) {
        console.error('Error creating knowledge base:', error);
    }
}

function showAuthError(message) {
    const errorDiv = document.getElementById('auth-error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => errorDiv.classList.add('hidden'), 5000);
}

// Close modal on overlay click
document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) {
        hideModal();
    }
});

/* Ragnarök Firebase Configuration */

// ========================================
// Firebase Web App Configuration
// ========================================
// Project: newrole-rag (renamed to Ragnarök UI)
// Get these values from: https://console.firebase.google.com/project/newrole-rag
// Settings (⚙️) → Project Settings → Your apps → Web app

// Firebase Configuration - REAL DATA FROM FIREBASE CONSOLE
window.FIREBASE_CONFIG = {
    apiKey: "AIzaSyAPoAIWZ4dfWMXtFZ0Fj9AobIMsPJ3EjTc",
    authDomain: "newrole-rag.firebaseapp.com",
    projectId: "newrole-rag",
    storageBucket: "newrole-rag.firebasestorage.app",
    messagingSenderId: "714862252903",
    appId: "1:714862252903:web:ee61fc6f3e52e4710c55c2"
};

// API Configuration - Production Only
window.API_CONFIG = {
    GATEWAY_URL: "/api/v1",  // Through nginx proxy
    ENVIRONMENT: "production"
};

console.log('Ragnarök Firebase Config loaded for project:', window.FIREBASE_CONFIG.projectId);

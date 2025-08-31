// api.js - Frontend API Integration
class RecipeAPI {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
        this.token = this.getStoredToken();
    }

    // Token management
    getStoredToken() {
        return localStorage.getItem('recipe_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('recipe_token', token);
    }

    removeToken() {
        this.token = null;
        localStorage.removeItem('recipe_token');
    }

    // HTTP request helper
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add authorization header if token exists
        if (this.token) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Authentication
    async register(name, email, password) {
        const data = await this.request('/register', {
            method: 'POST',
            body: JSON.stringify({ name, email, password })
        });

        if (data.token) {
            this.setToken(data.token);
        }

        return data;
    }

    async login(email, password) {
        const data = await this.request('/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        if (data.token) {
            this.setToken(data.token);
        }

        return data;
    }

    logout() {
        this.removeToken();
    }

    // Recipe operations
    async searchRecipes(ingredients) {
        return await this.request('/recipes/search', {
            method: 'POST',
            body: JSON.stringify({ ingredients })
        });
    }

    // Ingredient operations
    async getIngredients() {
        return await this.request('/ingredients');
    }

    async addIngredient(ingredient) {
        return await this.request('/ingredients', {
            method: 'POST',
            body: JSON.stringify({ ingredient })
        });
    }

    async removeIngredient(ingredient) {
        return await this.request(`/ingredients/${encodeURIComponent(ingredient)}`, {
            method: 'DELETE'
        });
    }

    // Favorites operations
    async getFavorites() {
        return await this.request('/favorites');
    }

    async addFavorite(recipe) {
        return await this.request('/favorites', {
            method: 'POST',
            body: JSON.stringify({ recipe })
        });
    }

    // History operations
    async getHistory() {
        return await this.request('/history');
    }

    // Profile operations
    async getProfile() {
        return await this.request('/profile');
    }

    async getStats() {
        return await this.request('/stats');
    }

    // Health check
    async healthCheck() {
        return await this.request('/health');
    }
}

// Initialize API instance
const api = new RecipeAPI();

// Enhanced frontend functions with real API integration
async function handleLogin(event) {
    event.preventDefault();
    
    const email = event.target.querySelector('input[type="email"]').value;
    const password = event.target.querySelector('input[type="password"]').value;
    
    try {
        showLoading('Signing in...');
        const response = await api.login(email, password);
        
        hideLoading();
        showNotification('Login successful!', 'success');
        
        // Store user data
        currentUser = response.user;
        
        // Show dashboard
        showDashboard();
        
        // Load user data
        await loadUserData();
        
    } catch (error) {
        hideLoading();
        showNotification(error.message, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const form = event.target;
    const name = form.querySelector('input[placeholder="Full name"]').value;
    const email = form.querySelector('input[type="email"]').value;
    const password = form.querySelector('input[type="password"]').value;
    const confirmPassword = form.querySelectorAll('input[type="password"]')[1].value;
    
    if (password !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    try {
        showLoading('Creating account...');
        const response = await api.register(name, email, password);
        
        hideLoading();
        showNotification('Account created successfully!', 'success');
        
        // Store user data
        currentUser = response.user;
        
        // Show dashboard
        showDashboard();
        
        // Load user data
        await loadUserData();
        
    } catch (error) {
        hideLoading();
        showNotification(error.message, 'error');
    }
}

async function findRecipes() {
    const ingredientInput = document.getElementById('ingredientInput');
    const ingredients = ingredientInput.value.trim();
    
    if (!ingredients) {
        showNotification('Please enter some ingredients first!', 'warning');
        return;
    }
    
    try {
        showLoading('Finding delicious recipes...');
        const response = await api.searchRecipes(ingredients);
        
        hideLoading();
        displayRecipes(response.recipes);
        
        // Clear input
        ingredientInput.value = '';
        
        showNotification(`Found ${response.total} recipes!`, 'success');
        
    } catch (error) {
        hideLoading();
        showNotification(error.message, 'error');
    }
}

async function addIngredient() {
    const input = document.getElementById('newIngredient');
    const ingredient = input.value.trim();
    
    if (!ingredient) return;
    
    try {
        await api.addIngredient(ingredient);
        
        // Add to UI
        const ingredientsList = document.getElementById('ingredientsList');
        const ingredientTag = document.createElement('div');
        ingredientTag.className = 'ingredient-tag';
        ingredientTag.innerHTML = `
            ${ingredient}
            <button onclick="removeIngredientAPI('${ingredient}', this)">×</button>
        `;
        
        ingredientsList.appendChild(ingredientTag);
        input.value = '';
        
        showNotification('Ingredient added!', 'success');
        
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function removeIngredientAPI(ingredient, button) {
    try {
        await api.removeIngredient(ingredient);
        button.parentElement.remove();
        showNotification('Ingredient removed!', 'success');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function addToFavorites(recipe) {
    try {
        await api.addFavorite(recipe);
        showNotification('Added to favorites!', 'success');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function loadUserData() {
    try {
        // Load ingredients
        const ingredientsResponse = await api.getIngredients();
        displayUserIngredients(ingredientsResponse.ingredients);
        
        // Load favorites
        const favoritesResponse = await api.getFavorites();
        displayFavorites(favoritesResponse.favorites);
        
        // Load history
        const historyResponse = await api.getHistory();
        displayHistory(historyResponse.history);
        
        // Update user info in sidebar
        const profile = await api.getProfile();
        updateUserProfile(profile.user);
        
    } catch (error) {
        console.error('Failed to load user data:', error);
    }
}

// UI Helper Functions
function showLoading(message = 'Loading...') {
    // Create loading overlay if it doesn't exist
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <lord-icon
                    src="https://cdn.lordicon.com/xjovhxra.json"
                    trigger="loop"
                    colors="primary:#ff6b9d,secondary:#4ecdc4"
                    style="width:60px;height:60px">
                </lord-icon>
                <p id="loadingMessage">${message}</p>
            </div>
        `;
        document.body.appendChild(overlay);
    } else {
        document.getElementById('loadingMessage').textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    // Create notification if it doesn't exist
    let notification = document.getElementById('notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        notification.className = 'notification';
        document.body.appendChild(notification);
    }
    
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.display = 'block';
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

function displayRecipes(recipes) {
    const recipeGrid = document.getElementById('recipeGrid');
    
    if (!recipes || recipes.length === 0) {
        recipeGrid.innerHTML = `
            <div class="empty-state">
                <lord-icon
                    src="https://cdn.lordicon.com/gmzxduhd.json"
                    trigger="loop"
                    colors="primary:#ff6b9d,secondary:#4ecdc4"
                    style="width:80px;height:80px">
                </lord-icon>
                <p>No recipes found. Try different ingredients!</p>
            </div>
        `;
        return;
    }
    
    recipeGrid.innerHTML = recipes.map(recipe => `
        <div class="recipe-card" data-recipe='${JSON.stringify(recipe)}'>
            <div class="recipe-image"></div>
            <div class="recipe-content">
                <h4>${recipe.name}</h4>
                <p>${recipe.description}</p>
                <div class="recipe-meta">
                    <span class="cook-time">
                        <lord-icon
                            src="https://cdn.lordicon.com/abvsilkn.json"
                            trigger="hover"
                            colors="primary:#6c7293"
                            style="width:16px;height:16px">
                        </lord-icon>
                        ${recipe.cook_time}
                    </span>
                    <span class="difficulty ${recipe.difficulty.toLowerCase()}">${recipe.difficulty}</span>
                </div>
            </div>
            <button class="favorite-btn" onclick="handleFavoriteClick(this)">
                <lord-icon
                    src="https://cdn.lordicon.com/xyboiuok.json"
                    trigger="hover"
                    colors="primary:#ff6b9d"
                    style="width:20px;height:20px">
                </lord-icon>
            </button>
        </div>
    `).join('');
}

function displayUserIngredients(ingredients) {
    const ingredientsList = document.getElementById('ingredientsList');
    
    if (!ingredients || ingredients.length === 0) {
        ingredientsList.innerHTML = '<p class="empty-message">No ingredients added yet</p>';
        return;
    }
    
    ingredientsList.innerHTML = ingredients.map(ingredient => `
        <div class="ingredient-tag">
            ${ingredient}
            <button onclick="removeIngredientAPI('${ingredient}', this)">×</button>
        </div>
    `).join('');
}

function displayFavorites(favorites) {
    const favoritesContainer = document.querySelector('#favoritesSection .favorites-container');
    
    if (!favorites || favorites.length === 0) {
        favoritesContainer.innerHTML = `
            <h3>Your Favorite Recipes</h3>
            <div class="empty-state">
                <lord-icon
                    src="https://cdn.lordicon.com/xyboiuok.json"
                    trigger="loop"
                    delay="2000"
                    colors="primary:#ff6b9d,secondary:#4ecdc4"
                    style="width:80px;height:80px">
                </lord-icon>
                <p>No favorites yet. Start exploring recipes!</p>
            </div>
        `;
        return;
    }
    
    const favoritesHTML = `
        <h3>Your Favorite Recipes</h3>
        <div class="recipe-grid">
            ${favorites.map(recipe => `
                <div class="recipe-card">
                    <div class="recipe-image"></div>
                    <div class="recipe-content">
                        <h4>${recipe.name}</h4>
                        <p>${recipe.description}</p>
                        <div class="recipe-meta">
                            <span class="cook-time">
                                <lord-icon
                                    src="https://cdn.lordicon.com/abvsilkn.json"
                                    trigger="hover"
                                    colors="primary:#6c7293"
                                    style="width:16px;height:16px">
                                </lord-icon>
                                ${recipe.cook_time}
                            </span>
                            <span class="difficulty ${recipe.difficulty.toLowerCase()}">${recipe.difficulty}</span>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    favoritesContainer.innerHTML = favoritesHTML;
}

function displayHistory(history) {
    const historyList = document.querySelector('.history-list');
    
    if (!history || history.length === 0) {
        historyList.innerHTML = '<p class="empty-message">No search history yet</p>';
        return;
    }
    
    historyList.innerHTML = history.map(item => {
        const timeAgo = getTimeAgo(new Date(item.search_time));
        return `
            <div class="history-item">
                <div class="history-icon">
                    <lord-icon
                        src="https://cdn.lordicon.com/abvsilkn.json"
                        trigger="hover"
                        colors="primary:#ffffff"
                        style="width:24px;height:24px">
                    </lord-icon>
                </div>
                <div class="history-content">
                    <h4>Searched for: ${item.ingredients}</h4>
                    <p>Found ${item.recipes_found} recipes • ${timeAgo}</p>
                </div>
            </div>
        `;
    }).join('');
}

function updateUserProfile(user) {
    const userName = document.querySelector('.user-name');
    const userEmail = document.querySelector('.user-email');
    
    if (userName) userName.textContent = user.name;
    if (userEmail) userEmail.textContent = user.email;
}

async function handleFavoriteClick(button) {
    const recipeCard = button.closest('.recipe-card');
    const recipeData = JSON.parse(recipeCard.getAttribute('data-recipe'));
    
    try {
        await addToFavorites(recipeData);
        
        // Visual feedback
        button.style.background = 'rgba(255, 107, 157, 0.2)';
        button.querySelector('lord-icon').setAttribute('trigger', 'click');
        
    } catch (error) {
        console.error('Failed to add to favorites:', error);
    }
}

// Utility functions
function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
}

// Enhanced logout function
async function handleLogout() {
    try {
        api.logout();
        currentUser = null;
        
        // Clear all cached data
        clearUserData();
        
        showLogin();
        showNotification('Logged out successfully', 'success');
        
    } catch (error) {
        console.error('Logout error:', error);
        showNotification('Logout failed', 'error');
    }
}

function clearUserData() {
    // Clear ingredients list
    const ingredientsList = document.getElementById('ingredientsList');
    if (ingredientsList) {
        ingredientsList.innerHTML = '';
    }
    
    // Clear recipe grid
    const recipeGrid = document.getElementById('recipeGrid');
    if (recipeGrid) {
        recipeGrid.innerHTML = '';
    }
    
    // Reset forms
    document.querySelectorAll('form').forEach(form => form.reset());
}

// Check authentication on page load
window.addEventListener('DOMContentLoaded', async function() {
    const token = api.getStoredToken();
    
    if (token) {
        try {
            // Verify token is still valid
            await api.getProfile();
            
            // Token is valid, show dashboard
            showDashboard();
            await loadUserData();
            
        } catch (error) {
            // Token is invalid, remove it and show login
            api.removeToken();
            showLogin();
        }
    } else {
        showLogin();
    }
});

// Global error handler for unhandled API errors
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showNotification('Something went wrong. Please try again.', 'error');
});

// Add styles for loading and notifications
const additionalStyles = `
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }

    .loading-content {
        background: white;
        padding: 32px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
    }

    .loading-content p {
        margin-top: 16px;
        font-weight: 500;
        color: #333;
    }

    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 500;
        z-index: 10000;
        display: none;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease;
    }

    .notification.success {
        background: #10b981;
        color: white;
    }

    .notification.error {
        background: #ef4444;
        color: white;
    }

    .notification.warning {
        background: #f59e0b;
        color: white;
    }

    .notification.info {
        background: #3b82f6;
        color: white;
    }

    .empty-message {
        text-align: center;
        color: #6c7293;
        font-style: italic;
        padding: 20px;
    }

    .difficulty.easy {
        background: #dcfce7;
        color: #166534;
    }

    .difficulty.medium {
        background: #fef3c7;
        color: #92400e;
    }

    .difficulty.hard {
        background: #fee2e2;
        color: #991b1b;
    }

    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// Global variables
let currentUser = null;
// API基础URL
const API_BASE_URL = '/api/v1';


// 切换登录/注册标签
function switchTab(tab) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');

    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        loginTab.classList.remove('active');
        registerTab.classList.add('active');
    }

    // 清除消息
    showMessage('');
}


// 显示消息
function showMessage(message, type = 'error') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message message-${type}`;

    if (message) {
        messageDiv.style.display = 'block';

        // 3秒后自动隐藏成功消息
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 3000);
        }
    } else {
        messageDiv.style.display = 'none';
    }
}


// 保存Token
function saveToken(token) {
    localStorage.setItem('access_token', token);
}


// 获取Token
function getToken() {
    return localStorage.getItem('access_token');
}


// 清除Token
function clearToken() {
    localStorage.removeItem('access_token');
}


// API请求封装
async function apiRequest(url, options = {}) {
    const token = getToken();

    // 添加认证头
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers,
    });

    // 处理响应
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(error.detail || '请求失败');
    }

    return response.json();
}


// 登录
async function login(email, password) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });

        // 保存Token
        saveToken(data.access_token);

        showMessage('登录成功，正在跳转...', 'success');

        // 跳转到主页面
        setTimeout(() => {
            window.location.href = '/app';
        }, 1000);

    } catch (error) {
        showMessage(error.message, 'error');
    }
}


// 注册
async function register(email, password, nickname) {
    try {
        const data = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, nickname }),
        });

        showMessage('注册成功，正在跳转...', 'success');

        // 自动登录
        await login(email, password);

    } catch (error) {
        showMessage(error.message, 'error');
    }
}


// 检查是否已登录
async function checkAuth() {
    const token = getToken();

    if (!token) {
        return null;
    }

    try {
        const user = await apiRequest('/auth/me');
        return user;
    } catch (error) {
        // Token无效，清除并跳转到登录页
        clearToken();
        return null;
    }
}


// 登出
async function logout() {
    try {
        await apiRequest('/auth/logout', {
            method: 'POST',
        });
    } catch (error) {
        console.error('登出失败:', error);
    } finally {
        // 清除Token
        clearToken();

        // 跳转到登录页
        window.location.href = '/';
    }
}


// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否已登录
    checkAuth().then(user => {
        if (user && window.location.pathname !== '/app') {
            // 已登录，跳转到主页面
            window.location.href = '/app';
        }
    });

    // 登录表单提交
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        if (!email || !password) {
            showMessage('请填写完整的登录信息', 'error');
            return;
        }

        await login(email, password);
    });

    // 注册表单提交
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('register-email').value.trim();
        const nickname = document.getElementById('register-nickname').value.trim();
        const password = document.getElementById('register-password').value;
        const passwordConfirm = document.getElementById('register-password-confirm').value;

        if (!email || !password) {
            showMessage('请填写完整的注册信息', 'error');
            return;
        }

        if (password.length < 6) {
            showMessage('密码长度至少为6位', 'error');
            return;
        }

        if (password !== passwordConfirm) {
            showMessage('两次输入的密码不一致', 'error');
            return;
        }

        await register(email, password, nickname);
    });
});

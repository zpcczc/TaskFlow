// js/api.js
const API_BASE = 'http://localhost:8000/api/v1';

// 获取存储的 token
function getToken() {
    return localStorage.getItem('access_token');
}

// 保存 token
function setToken(token) {
    localStorage.setItem('access_token', token);
}

// 移除 token
function removeToken() {
    localStorage.removeItem('access_token');
}

// 通用 API 请求函数
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };
    const token = getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const config = {
        ...options,
        headers,
    };
    const response = await fetch(url, config);
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`请求失败: ${response.status} ${errorText}`);
    }
    if (response.status === 204) return null;
    return response.json();
}

export { apiRequest, getToken, setToken, removeToken };
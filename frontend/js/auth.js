// js/auth.js
import { apiRequest, setToken, removeToken, getToken } from './api.js';

// 登录
export async function login(email, password) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email: email, password })
        });
        setToken(data.access_token);
        return { success: true };
    } catch (err) {
        return { success: false, error: err.message };
    }
}

// 注册
export async function register(email, username, password) {
    try {
        await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, username, password })
        });
        // 注册后自动登录
        return await login(email, password);
    } catch (err) {
        return { success: false, error: err.message };
    }
}

// 登出
export function logout() {
    removeToken();
    window.location.href = '/login.html';
}

// 检查是否已登录，若未登录则跳转到登录页
export function requireAuth() {
    if (!getToken()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}
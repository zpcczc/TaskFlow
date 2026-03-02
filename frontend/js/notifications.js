// js/notifications.js
import { apiRequest } from './api.js';
import { requireAuth, logout } from './auth.js';

let offset = 0;
const limit = 20;
let hasMore = true;
let isLoading = false;

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;

    await loadUserInfo();
    await loadNotifications(true);

    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('load-more-btn').addEventListener('click', () => loadNotifications(false));
});

async function loadUserInfo() {
    try {
        const user = await apiRequest('/users/me');
        document.getElementById('user-name').textContent = user.username;
    } catch (err) {
        console.error('加载用户信息失败', err);
    }
}

async function loadNotifications(reset = false) {
    if (isLoading) return;
    if (reset) {
        offset = 0;
        hasMore = true;
    }
    if (!hasMore) return;

    isLoading = true;
    try {
        const notifs = await apiRequest(`/notifications?skip=${offset}&limit=${limit}`);
        if (reset) {
            document.getElementById('notification-list').innerHTML = '';
        }
        notifs.forEach(notif => appendNotification(notif));
        offset += notifs.length;
        if (notifs.length < limit) {
            hasMore = false;
            document.getElementById('load-more-btn').disabled = true;
        }
    } catch (err) {
        console.error('加载通知失败', err);
    } finally {
        isLoading = false;
    }
}

function appendNotification(notif) {
    const time = notif.created_at ? new Date(notif.created_at).toLocaleString() : '';
    const html = `
        <div class="notification-item" data-notif-id="${notif.id}">
            <span class="notification-message">${escapeHtml(notif.message)}</span>
            <span class="notification-time">${time}</span>
            <button class="delete-notif">删除</button>
        </div>
    `;
    document.getElementById('notification-list').insertAdjacentHTML('beforeend', html);
    // 绑定删除事件
    const item = document.querySelector(`.notification-item[data-notif-id="${notif.id}"]`);
    item.querySelector('.delete-notif').addEventListener('click', async () => {
        await deleteNotification(notif.id);
    });
}

async function deleteNotification(id) {
    try {
        await apiRequest(`/notifications/${id}`, { method: 'DELETE' });
        document.querySelector(`.notification-item[data-notif-id="${id}"]`).remove();
    } catch (err) {
        alert('删除通知失败: ' + err.message);
    }
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
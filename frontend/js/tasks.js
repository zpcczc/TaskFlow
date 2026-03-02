// tasks.js
import { apiRequest } from './api.js';
import { requireAuth } from './auth.js';

// 用户分页相关
let currentUserPage = 1;
const userPageSize = 5;
let currentPageUsers = [];

// WebSocket 相关
let ws = null;

// 页面加载初始化
document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;

    await loadUserInfo();
    await loadUserPage(currentUserPage);
    await loadTasks();
    await loadUnreadCount();
    connectWebSocket();

    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('create-task-btn').addEventListener('click', createTask);
    document.getElementById('prev-user-page').addEventListener('click', prevUserPage);
    document.getElementById('next-user-page').addEventListener('click', nextUserPage);
});

// 加载用户信息
async function loadUserInfo() {
    try {
        const user = await apiRequest('/users/me');
        document.getElementById('user-name').textContent = user.username;
    } catch (err) {
        console.error('加载用户信息失败', err);
    }
}

// 加载用户列表（分页）
async function loadUserPage(page) {
    const skip = (page - 1) * userPageSize;
    try {
        const users = await apiRequest(`/users/?skip=${skip}&limit=${userPageSize}`);
        currentPageUsers = users;
        document.getElementById('current-user-page').textContent = page;
        // 更新翻页按钮状态
        const prevBtn = document.getElementById('prev-user-page');
        const nextBtn = document.getElementById('next-user-page');
        prevBtn.disabled = page === 1;
        nextBtn.disabled = users.length < userPageSize;
    } catch (err) {
        console.error('加载用户列表失败', err);
        currentPageUsers = [];
    }
}

async function prevUserPage() {
    if (currentUserPage > 1) {
        currentUserPage--;
        await loadUserPage(currentUserPage);
        await loadTasks();
    }
}

async function nextUserPage() {
    currentUserPage++;
    await loadUserPage(currentUserPage);
    await loadTasks();
}

// 加载任务列表
async function loadTasks() {
    try {
        const tasks = await apiRequest('/tasks/');
        renderTasks(tasks);
    } catch (err) {
        console.error('加载任务失败', err);
    }
}

function renderTasks(tasks) {
    const container = document.getElementById('task-list');
    if (tasks.length === 0) {
        container.innerHTML = '<div class="loading">暂无任务，创建一个吧！</div>';
        return;
    }
    container.innerHTML = tasks.map(task => renderTaskCard(task)).join('');
    tasks.forEach(task => attachTaskEvents(task.id));
}

function renderTaskCard(task) {
    const priorityClass = `priority-${task.priority}`;
    const statusClass = `status-${task.status}`;
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleString() : '无截止日期';

    const userOptions = currentPageUsers.map(user =>
        `<option value="${user.id}">${escapeHtml(user.username)}</option>`
    ).join('');

    return `
        <div class="task-card" data-task-id="${task.id}">
            <div class="task-header">
                <span class="task-title">${escapeHtml(task.title)}</span>
                <span class="task-priority ${priorityClass}">${task.priority}</span>
            </div>
            <div class="task-meta">
                <span>创建者: ${task.creator?.username || task.creator_id}</span>
                <span>截止: ${dueDate}</span>
            </div>
            <div class="task-description">${escapeHtml(task.description || '')}</div>
            <div class="task-status ${statusClass}">${task.status}</div>
            <div class="assignees">
                执行者: 
                ${task.assignees && task.assignees.length ?
                    task.assignees.map(a => `<span class="assignee-tag">${escapeHtml(a.username)}</span>`).join('') :
                    '暂无'}
            </div>
            <div class="task-actions">
                <select class="status-select">
                    <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>待处理</option>
                    <option value="doing" ${task.status === 'doing' ? 'selected' : ''}>进行中</option>
                    <option value="done" ${task.status === 'done' ? 'selected' : ''}>已完成</option>
                </select>
                <button class="primary update-status">更新状态</button>
                <select class="assignee-select">
                    <option value="">选择执行者...</option>
                    ${userOptions}
                </select>
                <button class="primary add-assignee">添加执行者</button>
                <button class="danger remove-assignee">移除执行者</button>
                <button class="danger delete-task">删除</button>
            </div>
        </div>
    `;
}

function attachTaskEvents(taskId) {
    const card = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
    if (!card) return;

    const statusSelect = card.querySelector('.status-select');
    const updateBtn = card.querySelector('.update-status');
    const addBtn = card.querySelector('.add-assignee');
    const removeBtn = card.querySelector('.remove-assignee');
    const assigneeSelect = card.querySelector('.assignee-select');
    const deleteBtn = card.querySelector('.delete-task');

    updateBtn.addEventListener('click', async () => {
        const newStatus = statusSelect.value;
        await updateTask(taskId, { status: newStatus });
    });

    addBtn.addEventListener('click', async () => {
        const userId = assigneeSelect.value;
        if (!userId) return alert('请选择用户');
        await addAssignee(taskId, parseInt(userId));
    });

    removeBtn.addEventListener('click', async () => {
        const userId = assigneeSelect.value;
        if (!userId) return alert('请选择用户');
        await removeAssignee(taskId, parseInt(userId));
    });

    deleteBtn.addEventListener('click', async () => {
        if (!confirm('确定删除该任务吗？')) return;
        await deleteTask(taskId);
    });
}

async function createTask() {
    const title = document.getElementById('new-task-title').value;
    const description = document.getElementById('new-task-description').value;
    const priority = document.getElementById('new-task-priority').value;
    const dueDate = document.getElementById('new-task-due').value;
    if (!title) return alert('标题不能为空');
    try {
        await apiRequest('/tasks/', {
            method: 'POST',
            body: JSON.stringify({
                title,
                description,
                priority,
                due_date: dueDate ? new Date(dueDate).toISOString() : null
            })
        });
        await loadTasks();
    } catch (err) {
        alert('创建任务失败: ' + err.message);
    }
}

async function updateTask(taskId, updates) {
    try {
        await apiRequest(`/tasks/${taskId}`, {
            method: 'PATCH',
            body: JSON.stringify(updates)
        });
        await loadTasks();
    } catch (err) {
        alert('更新任务失败: ' + err.message);
    }
}

async function addAssignee(taskId, userId) {
    try {
        await apiRequest(`/tasks/${taskId}/assignees/${userId}`, {
            method: 'POST'
        });
        await loadTasks();
    } catch (err) {
        alert('添加执行者失败: ' + err.message);
    }
}

async function removeAssignee(taskId, userId) {
    try {
        await apiRequest(`/tasks/${taskId}/assignees/${userId}`, {
            method: 'DELETE'
        });
        await loadTasks();
    } catch (err) {
        alert('移除执行者失败: ' + err.message);
    }
}

async function deleteTask(taskId) {
    try {
        await apiRequest(`/tasks/${taskId}`, { method: 'DELETE' });
        await loadTasks();
    } catch (err) {
        alert('删除任务失败: ' + err.message);
    }
}

// ---------- 通知模块 ----------
async function loadUnreadCount() {
    try {
        const count = await apiRequest('/notifications/unread-count');
        document.getElementById('unread-count').textContent = count;
    } catch (err) {
        console.error('加载未读数失败', err);
    }
}

function connectWebSocket() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    const wsUrl = `ws://localhost:8000/ws/notifications?token=${encodeURIComponent(token)}`;
    ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            loadUnreadCount();
            alert(`🔔 新通知: ${data.message || '您有一条新通知'}`);
        } catch (e) {
            console.error('WebSocket 消息解析失败', e);
        }
    };
    ws.onclose = () => console.log('WebSocket 关闭');
    ws.onerror = (err) => console.error('WebSocket 错误', err);
}

// 退出登录
function logout() {
    if (ws) ws.close();
    localStorage.removeItem('access_token');
    window.location.href = '/login.html';
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
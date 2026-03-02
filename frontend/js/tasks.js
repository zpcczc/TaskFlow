// tasks.js
import { apiRequest } from './api.js';
import { requireAuth, logout } from './auth.js';

// 存储所有用户（用于下拉框）
let allUsers = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;

    await loadUserInfo();
    await loadAllUsers();   // 先加载用户列表
    await loadTasks();

    document.getElementById('logout-btn').addEventListener('click', logout);
    document.getElementById('create-task-btn').addEventListener('click', createTask);
});

async function loadUserInfo() {
    try {
        const user = await apiRequest('/users/me');
        document.getElementById('user-name').textContent = user.username;
    } catch (err) {
        console.error('加载用户信息失败', err);
    }
}

// 加载所有用户（调整 limit 以获取全部，例如 1000）
async function loadAllUsers() {
    try {
        // 可以根据需要调整 limit，如果用户很多可考虑分页加载，这里取 1000 足够大多数场景
        allUsers = await apiRequest('/users/?limit=1000');
    } catch (err) {
        console.error('加载用户列表失败', err);
        allUsers = [];
    }
}

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
        container.innerHTML = '<div class="loading">暂无任务</div>';
        return;
    }
    container.innerHTML = tasks.map(task => renderTaskCard(task)).join('');
    tasks.forEach(task => attachTaskEvents(task.id));
}

function renderTaskCard(task) {
    const priorityClass = `priority-${task.priority}`;
    const statusClass = `status-${task.status}`;
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleString() : '无截止日期';

    // 生成执行者选项下拉框
    const userOptions = allUsers.map(user =>
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
        // 重新加载任务列表
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
        // 局部更新（可选），这里简单重新加载全部
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

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
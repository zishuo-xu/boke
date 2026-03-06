// 当前选择的分组
let currentGroup = 'all';

// 用户的所有分组
let userGroups = [];


// 加载自选列表
async function loadWatchlist() {
    try {
        showLoading();

        // 加载分组
        await loadGroups();

        // 加载标的列表
        const groupId = currentGroup === 'all' || currentGroup === '0' ? null : currentGroup;
        const stocks = await watchlistAPI.getStocks(groupId);

        // 渲染标的列表
        renderStockList(stocks);

    } catch (error) {
        console.error('加载自选列表失败:', error);
        showMessage('加载自选列表失败', 'error');
    } finally {
        hideLoading();
    }
}


// 加载分组
async function loadGroups() {
    try {
        userGroups = await watchlistAPI.getGroups();

        // 渲染分组标签
        const groupList = document.getElementById('group-list');
        groupList.innerHTML = userGroups.map(group =>
            `<button class="group-tab" data-group="${group.id}" onclick="selectGroup(${group.id})">
                ${group.name} (${group.stock_count})
            </button>`
        ).join('');

        // 更新添加标的弹窗的分组选择
        const groupSelect = document.getElementById('stock-group-input');
        groupSelect.innerHTML = '<option value="">未分组</option>' +
            userGroups.map(group =>
                `<option value="${group.id}">${group.name}</option>`
            ).join('');

    } catch (error) {
        console.error('加载分组失败:', error);
    }
}


// 选择分组
async function selectGroup(groupId) {
    currentGroup = groupId;

    // 更新分组标签状态
    document.querySelectorAll('.group-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.group == groupId);
    });

    // 重新加载标的列表
    await loadWatchlist();
}


// 渲染标的列表
function renderStockList(stocks) {
    const tbody = document.getElementById('stock-list-body');
    const emptyState = document.getElementById('watchlist-empty');

    if (stocks.length === 0) {
        tbody.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';

    tbody.innerHTML = stocks.map(stock => `
        <tr>
            <td>${stock.code}</td>
            <td>${stock.name}</td>
            <td>${getStockTypeName(stock.type)}</td>
            <td>--</td>
            <td>--</td>
            <td>
                <button class="btn btn-sm" onclick="editStock(${stock.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteStock(${stock.id})">删除</button>
            </td>
        </tr>
    `).join('');
}


// 显示添加标的弹窗
function showAddStockModal() {
    // 清空表单
    document.getElementById('add-stock-form').reset();

    // 显示弹窗
    showModal('add-stock-modal');
}


// 添加标的
document.getElementById('add-stock-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {
        code: formData.get('code'),
        name: formData.get('name'),
        type: formData.get('type'),
        group_id: formData.get('group_id') ? parseInt(formData.get('group_id')) : null,
    };

    try {
        showLoading();

        await watchlistAPI.addStock(data);

        showMessage('添加成功');

        // 关闭弹窗
        closeModal('add-stock-modal');

        // 重新加载列表
        await loadWatchlist();

    } catch (error) {
        console.error('添加标的失败:', error);
        showMessage(error.message || '添加失败', 'error');
    } finally {
        hideLoading();
    }
});


// 编辑标的
function editStock(stockId) {
    // TODO: 实现编辑功能
    alert('编辑功能开发中');
}


// 删除标的
async function deleteStock(stockId) {
    if (!confirm('确定要删除这个标的吗？')) {
        return;
    }

    try {
        showLoading();

        await watchlistAPI.deleteStock(stockId);

        showMessage('删除成功');

        // 重新加载列表
        await loadWatchlist();

    } catch (error) {
        console.error('删除标的失败:', error);
        showMessage(error.message || '删除失败', 'error');
    } finally {
        hideLoading();
    }
}


// 创建分组（简单实现）
async function createGroup(name) {
    try {
        await watchlistAPI.createGroup({ name, sort_order: 0 });

        showMessage('分组创建成功');

        // 重新加载分组
        await loadGroups();

    } catch (error) {
        console.error('创建分组失败:', error);
        showMessage(error.message || '创建失败', 'error');
    }
}


// 删除分组
async function deleteGroup(groupId) {
    if (!confirm('确定要删除这个分组吗？该分组下的标的将移动到未分组。')) {
        return;
    }

    try {
        showLoading();

        await watchlistAPI.deleteGroup(groupId);

        showMessage('分组删除成功');

        // 如果当前选中的是被删除的分组，切换到全部
        if (currentGroup === groupId) {
            currentGroup = 'all';
        }

        // 重新加载
        await loadWatchlist();

    } catch (error) {
        console.error('删除分组失败:', error);
        showMessage(error.message || '删除失败', 'error');
    } finally {
        hideLoading();
    }
}

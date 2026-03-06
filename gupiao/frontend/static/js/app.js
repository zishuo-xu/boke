// 当前用户
let currentUser = null;

// 当前页面
let currentPage = 'watchlist';


// 搜索股票代码
async function searchStock() {
    const codeInput = document.getElementById('search-code-input');
    const code = codeInput.value.trim();

    if (!code) {
        showMessage('请输入股票代码', 'error');
        return;
    }

    showLoading();

    try {
        const data = await marketAPI.getStockByCode(code);
        displaySearchResult(data);
        showMessage('查询成功', 'success');
    } catch (error) {
        showMessage(error.message || '查询失败', 'error');
    } finally {
        hideLoading();
    }
}


// 处理搜索框回车
function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        searchStock();
    }
}


// 显示搜索结果
function displaySearchResult(data) {
    const modal = document.getElementById('search-result-modal');
    const content = document.getElementById('search-result-content');

    if (!data) {
        content.innerHTML = '<p>未找到该股票</p>';
        modal.style.display = 'flex';
        return;
    }

    const changeStyle = data.change_pct >= 0 ? 'up' : 'down';

    content.innerHTML = `
        <div class="stock-data-card">
            <div class="data-row">
                <div class="data-item">
                    <span class="data-label">股票代码</span>
                    <span class="data-value">${data.code}</span>
                </div>
                <div class="data-item">
                    <span class="data-label">股票名称</span>
                    <span class="data-value">${data.name}</span>
                </div>
            </div>
            <div class="data-row">
                <div class="data-item large">
                    <span class="data-label">现价</span>
                    <span class="data-value price">${formatNumber(data.price)}</span>
                </div>
                <div class="data-item large ${changeStyle(data.change_pct)}">
                    <span class="data-label">涨跌幅</span>
                    <span class="data-value change">${formatPercent(data.change_pct)}</span>
                </div>
            </div>
            <div class="data-row">
                <div class="data-item">
                    <span class="data-label">最高</span>
                    <span class="data-value">${formatNumber(data.high)}</span>
                </div>
                <div class="data-item">
                    <span class="data-label">最低</span>
                    <span class="data-value">${formatNumber(data.low)}</span>
                </div>
                <div class="data-item">
                    <span class="data-label">成交量</span>
                    <span class="data-value">${formatVolume(data.volume)}</span>
                </div>
            </div>
        </div>
    `;

    modal.style.display = 'flex';
}


// 格式化涨跌样式


// 初始化应用
document.addEventListener('DOMContentLoaded', async () => {
    // 检查认证
    try {
        currentUser = await authAPI.getCurrentUser();

        // 显示用户昵称
        document.getElementById('user-nickname').textContent =
            currentUser.nickname || currentUser.email;

    } catch (error) {
        // 未登录，跳转到登录页
        window.location.href = '/';
        return;
    }

    // 初始化页面导航
    initNavigation();

    // 加载初始页面
    await loadWatchlist();
});


// 初始化页面导航
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();

            const page = link.dataset.page;
            if (page === currentPage) {
                return;
            }

            // 更新导航状态
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // 切换页面
            await switchPage(page);
        });
    });
}


// 切换页面
async function switchPage(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');

    // 显示目标页面
    const pageElement = document.getElementById(`page-${page}`);
    if (pageElement) {
        pageElement.style.display = 'block';
    }

    currentPage = page;

    // 加载页面数据
    switch (page) {
        case 'watchlist':
            await loadWatchlist();
            break;
        case 'market':
            await loadMarket();
            break;
        case 'alerts':
            await loadAlerts();
            break;
    }
}


// 显示加载提示
function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}


// 隐藏加载提示
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}


// 显示消息
function showMessage(message, type = 'success') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message-toast message-toast-${type}`;
    messageDiv.style.display = 'block';

    // 3秒后自动隐藏
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 3000);
}


// 显示弹窗
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}


// 关闭弹窗
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}


// 点击弹窗外部关闭
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});


// 登出
async function logout() {
    if (!confirm('确定要退出登录吗？')) {
        return;
    }

    try {
        await authAPI.logout();
    } catch (error) {
        console.error('登出失败:', error);
    } finally {
        // 清除Token
        localStorage.removeItem('access_token');

        // 跳转到登录页
        window.location.href = '/';
    }
}


// 格式化数字
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) {
        return '--';
    }
    return num.toFixed(decimals);
}


// 格式化百分比
function formatPercent(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) {
        return '--%';
    }
    const sign = num >= 0 ? '+' : '';
    return `${sign}${num.toFixed(decimals)}%`;
}


// 格式化涨跌样式
function formatChangeStyle(num) {
    if (num === null || num === undefined || isNaN(num)) {
        return '';
    }
    return num >= 0 ? 'up' : 'down';
}


// 格式化成交量
function formatVolume(volume) {
    if (volume === null || volume === undefined || isNaN(volume)) {
        return '--';
    }

    if (volume >= 100000000) {
        return `${(volume / 100000000).toFixed(2)}亿`;
    } else if (volume >= 10000) {
        return `${(volume / 10000).toFixed(2)}万`;
    } else {
        return volume.toFixed(2);
    }
}


// 获取标的类型名称
function getStockTypeName(type) {
    return type === 'stock' ? '股票' : '基金';
}


// 获取预警类型名称
function getAlertTypeName(type) {
    return type === 'upper' ? '上限预警' : '下限预警';
}

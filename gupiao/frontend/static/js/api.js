// API基础URL
const API_BASE_URL = '/api/v1';


// 获取Token
function getToken() {
    return localStorage.getItem('access_token');
}


// API请求封装
async function apiRequest(url, options = {}) {
    const token = getToken();

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

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: '请求失败' }));
        throw new Error(error.detail || '请求失败');
    }

    return response.json();
}


// ========== 认证 API ==========

const authAPI = {
    // 用户登录
    login: (email, password) => {
        return apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    },

    // 用户注册
    register: (email, password, nickname) => {
        return apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, nickname }),
        });
    },

    // 获取当前用户
    getCurrentUser: () => {
        return apiRequest('/auth/me');
    },

    // 登出
    logout: () => {
        return apiRequest('/auth/logout', {
            method: 'POST',
        });
    },
};


// ========== 自选管理 API ==========

const watchlistAPI = {
    // 添加标的
    addStock: (data) => {
        return apiRequest('/watchlist', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // 获取自选列表
    getStocks: (groupId = null) => {
        const url = groupId !== null ? `/watchlist?group_id=${groupId}` : '/watchlist';
        return apiRequest(url);
    },

    // 获取单个标的
    getStock: (id) => {
        return apiRequest(`/watchlist/${id}`);
    },

    // 更新标的
    updateStock: (id, data) => {
        return apiRequest(`/watchlist/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // 删除标的
    deleteStock: (id) => {
        return apiRequest(`/watchlist/${id}`, {
            method: 'DELETE',
        });
    },

    // 搜索标的
    searchStocks: (keyword, type = null) => {
        return apiRequest('/watchlist/search', {
            method: 'POST',
            body: JSON.stringify({ keyword, type }),
        });
    },

    // 创建分组
    createGroup: (data) => {
        return apiRequest('/watchlist/groups', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // 获取分组列表
    getGroups: () => {
        return apiRequest('/watchlist/groups');
    },

    // 更新分组
    updateGroup: (id, data) => {
        return apiRequest(`/watchlist/groups/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // 删除分组
    deleteGroup: (id) => {
        return apiRequest(`/watchlist/groups/${id}`, {
            method: 'DELETE',
        });
    },
};


// ========== 市场数据 API ==========

const marketAPI = {
    // 根据代码获取股票实时数据（无需登录）
    getStockByCode: (code, force = false) => {
        return apiRequest(`/market/stock/code/${code}?force=${force}`);
    },

    // 获取股票实时数据
    getStockRealtime: (id, force = false) => {
        return apiRequest(`/market/stock/${id}?force=${force}`);
    },

    // 获取股票历史数据
    getStockHistory: (id, period = '30d', force = false) => {
        return apiRequest(`/market/stock/${id}/history?period=${period}&force=${force}`);
    },

    // 获取基金实时数据
    getFundRealtime: (id, force = false) => {
        return apiRequest(`/market/fund/${id}?force=${force}`);
    },

    // 获取基金历史数据
    getFundHistory: (id, period = '30d', force = false) => {
        return apiRequest(`/market/fund/${id}/history?period=${period}&force=${force}`);
    },

    // 批量获取股票数据
    getBatchStocks: (ids, force = false) => {
        return apiRequest('/market/batch', {
            method: 'POST',
            body: JSON.stringify({ stock_ids: ids, force }),
        });
    },

    // 刷新所有数据
    refreshAll: () => {
        return apiRequest('/market/refresh', {
            method: 'POST',
        });
    },
};


// ========== 预警 API ==========

const alertAPI = {
    // 创建预警
    createAlert: (data) => {
        return apiRequest('/alerts', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // 获取预警列表
    getAlerts: () => {
        return apiRequest('/alerts');
    },

    // 更新预警
    updateAlert: (id, data) => {
        return apiRequest(`/alerts/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // 删除预警
    deleteAlert: (id) => {
        return apiRequest(`/alerts/${id}`, {
            method: 'DELETE',
        });
    },

    // 获取通知
    getNotifications: () => {
        return apiRequest('/alerts/notifications');
    },

    // 标记通知已读
    markNotificationRead: (id) => {
        return apiRequest(`/alerts/notifications/${id}/read`, {
            method: 'PUT',
        });
    },
};

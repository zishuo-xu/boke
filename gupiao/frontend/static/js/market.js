// 当前选择的标的
let currentStock = null;

// 当前时间周期
let currentPeriod = '30d';

// 图表实例
let stockChart = null;


// 加载数据监控页面
async function loadMarket() {
    try {
        showLoading();

        // 加载用户自选列表作为选择项
        await loadStockSelect();

    } catch (error) {
        console.error('加载数据监控页面失败:', error);
        showMessage('加载数据监控页面失败', 'error');
    } finally {
        hideLoading();
    }
}


// 加载标的选择列表
async function loadStockSelect() {
    try {
        const stocks = await watchlistAPI.getStocks();

        const select = document.getElementById('market-stock-select');
        select.innerHTML = '<option value="">请选择标的</option>' +
            stocks.map(stock =>
                `<option value="${stock.id}" data-code="${stock.code}" data-type="${stock.type}">
                    ${stock.code} - ${stock.name}
                </option>`
            ).join('');

    } catch (error) {
        console.error('加载标的选择失败:', error);
    }
}


// 选择标的
async function selectStock() {
    const select = document.getElementById('market-stock-select');
    const stockId = parseInt(select.value);

    if (!stockId) {
        // 清空数据展示
        document.getElementById('stock-data-card').style.display = 'none';
        document.getElementById('chart-container').style.display = 'none';
        currentStock = null;
        return;
    }

    const selectedOption = select.options[select.selectedIndex];

    currentStock = {
        id: stockId,
        code: selectedOption.dataset.code,
        type: selectedOption.dataset.type,
    };

    try {
        showLoading();

        // 显示数据卡片
        document.getElementById('stock-data-card').style.display = 'block';

        // 加载实时数据
        await loadStockRealtimeData();

        // 显示图表容器
        document.getElementById('chart-container').style.display = 'block';

        // 加载历史数据并绘制图表
        await loadStockHistoryData();

    } catch (error) {
        console.error('加载标的数据失败:', error);
        showMessage('加载标的数据失败', 'error');
    } finally {
        hideLoading();
    }
}


// 加载实时数据
async function loadStockRealtimeData() {
    if (!currentStock) {
        return;
    }

    try {
        let data;
        if (currentStock.type === 'stock') {
            data = await marketAPI.getStockRealtime(currentStock.id);
        } else {
            data = await marketAPI.getFundRealtime(currentStock.id);
        }

        // 更新数据卡片
        document.getElementById('stock-code').textContent = data.code;
        document.getElementById('stock-name').textContent = data.name;

        const priceElement = document.getElementById('stock-price');
        const changeElement = document.getElementById('stock-change');

        if (currentStock.type === 'stock') {
            priceElement.textContent = formatNumber(data.price, 2);
            changeElement.textContent = formatPercent(data.change_pct);
        } else {
            priceElement.textContent = formatNumber(data.nav, 4);
            changeElement.textContent = formatPercent(data.change_pct);
        }

        // 更新涨跌样式
        const changeStyle = formatChangeStyle(data.change_pct);
        priceElement.className = `data-value price ${changeStyle}`;
        changeElement.className = `data-value change ${changeStyle}`;

        // 更新其他数据
        if (currentStock.type === 'stock') {
            document.getElementById('stock-high').textContent = formatNumber(data.high);
            document.getElementById('stock-low').textContent = formatNumber(data.low);
            document.getElementById('stock-volume').textContent = formatVolume(data.volume);
        }

    } catch (error) {
        console.error('加载实时数据失败:', error);
    }
}


// 加载历史数据
async function loadStockHistoryData() {
    if (!currentStock) {
        return;
    }

    try {
        let data;
        if (currentStock.type === 'stock') {
            data = await marketAPI.getStockHistory(currentStock.id, currentPeriod);
        } else {
            data = await marketAPI.getFundHistory(currentStock.id, currentPeriod);
        }

        // 绘制图表
        drawChart(data);

    } catch (error) {
        console.error('加载历史数据失败:', error);
    }
}


// 切换时间周期
async function changePeriod(period) {
    currentPeriod = period;

    // 更新按钮状态
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent === period.replace('d', '天').replace('y', '年')) {
            btn.classList.add('active');
        }
    });

    // 重新加载历史数据
    if (currentStock) {
        await loadStockHistoryData();
    }
}


// 刷新数据
async function refreshMarketData() {
    try {
        showLoading();

        // 刷新所有数据
        await marketAPI.refreshAll();

        showMessage('数据刷新成功');

        // 如果有选中的标的，重新加载
        if (currentStock) {
            await loadStockRealtimeData();
            await loadStockHistoryData();
        }

    } catch (error) {
        console.error('刷新数据失败:', error);
        showMessage('刷新数据失败', 'error');
    } finally {
        hideLoading();
    }
}


// 绘制图表
function drawChart(historyData) {
    const dates = historyData.map(item => item.date);
    const values = historyData.map(item => currentStock.type === 'stock' ? item.close : item.nav);

    // 初始化图表
    if (!stockChart) {
        const chartContainer = document.getElementById('stock-chart');
        stockChart = echarts.init(chartContainer);
    }

    const option = {
        title: {
            text: `${currentStock.code} - 历史走势`,
            left: 'center',
        },
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                const date = params[0].name;
                const value = params[0].value;
                return `${date}<br/>${currentStock.type === 'stock' ? '收盘价' : '净值'}: ${formatNumber(value)}`;
            },
        },
        legend: {
            bottom: 0,
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates,
        },
        yAxis: {
            type: 'value',
            scale: true,
        },
        series: [
            {
                name: currentStock.type === 'stock' ? '收盘价' : '净值',
                type: 'line',
                data: values,
                smooth: true,
                sampling: 'average',
                large: true,
                itemStyle: {
                    color: '#2563eb',
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(37, 99, 235, 0.3)' },
                        { offset: 1, color: 'rgba(37, 99, 235, 0.05)' },
                    ]),
                },
            },
        ],
        dataZoom: [
            {
                type: 'inside',
                start: 0,
                end: 100,
            },
            {
                start: 0,
                end: 100,
            },
        ],
    };

    stockChart.setOption(option);

    // 响应式
    window.addEventListener('resize', () => {
        stockChart.resize();
    });
}

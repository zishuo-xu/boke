/**
 * ECharts 图表工具类
 */

class StockChart {
    /**
     * 股票走势图
     */
    static drawTrendChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`容器 ${containerId} 不存在`);
            return null;
        }

        const chart = echarts.init(container);

        const defaultOption = {
            title: {
                text: options.title || '历史走势',
                left: 'center',
            },
            tooltip: {
                trigger: 'axis',
                formatter: function (params) {
                    return params[0].name + '<br/>' +
                        params.map(param => `${param.seriesName}: ${param.value}`).join('<br/>');
                },
            },
            legend: {
                bottom: 0,
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: data.dates || [],
            },
            yAxis: {
                type: 'value',
                scale: true,
            },
            series: [{
                name: options.seriesName || '价格',
                type: 'line',
                data: data.values || [],
                smooth: true,
                sampling: 'average',
                large: true,
                itemStyle: {
                    color: options.color || '#2563eb',
                },
                areaStyle: options.showArea !== false ? {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: options.areaColorStart || 'rgba(37, 99, 235, 0.3)' },
                        { offset: 1, color: options.areaColorEnd || 'rgba(37, 99, 235, 0.05)' },
                    ]),
                } : undefined,
            }],
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

        chart.setOption({ ...defaultOption, ...options });

        return chart;
    }

    /**
     * 组合对比图
     */
    static drawComparisonChart(containerId, data, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`容器 ${containerId} 不存在`);
            return null;
        }

        const chart = echarts.init(container);

        const dates = data[0]?.dates || [];

        const series = data.map((item, index) => ({
            name: item.name,
            type: 'line',
            data: item.values,
            smooth: true,
            sampling: 'average',
            large: true,
        }));

        const option = {
            title: {
                text: options.title || '组合走势对比',
                left: 'center',
            },
            tooltip: {
                trigger: 'axis',
            },
            legend: {
                bottom: 0,
                data: data.map(item => item.name),
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
            series: series,
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

        chart.setOption({ ...option, ...options });

        return chart;
    }

    /**
     * 销毁图表
     */
    static dispose(chart) {
        if (chart) {
            chart.dispose();
        }
    }

    /**
     * 调整图表大小
     */
    static resize(chart) {
        if (chart) {
            chart.resize();
        }
    }
}


// 导出工具类
window.StockChart = StockChart;

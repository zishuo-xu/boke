import akshare as ak
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取工具（封装AKShare）"""

    @staticmethod
    def get_stock_realtime_data(code: str) -> Optional[Dict]:
        """
        获取股票实时数据

        Args:
            code: 股票代码

        Returns:
            股票数据字典，失败返回None
        """
        try:
            # 获取A股实时行情
            df = ak.stock_zh_a_spot_em()

            # 查找指定股票
            stock_data = df[df['代码'] == code]

            if stock_data.empty:
                logger.warning(f"股票{code}未找到")
                return None

            stock = stock_data.iloc[0]

            return {
                'code': stock['代码'],
                'name': stock['名称'],
                'price': float(stock['最新价']) if stock['最新价'] else 0.0,
                'change': float(stock['涨跌额']) if stock['涨跌额'] else 0.0,
                'change_pct': float(stock['涨跌幅']) if stock['涨跌幅'] else 0.0,
                'volume': float(stock['成交量']) if stock['成交量'] else 0.0,
                'turnover_rate': float(stock['换手率']) if stock['换手率'] else 0.0,
                'open': float(stock['今开']) if stock['今开'] else 0.0,
                'close': float(stock['昨收']) if stock['昨收'] else 0.0,
                'high': float(stock['最高']) if stock['最高'] else 0.0,
                'low': float(stock['最低']) if stock['最低'] else 0.0,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"获取股票{code}数据失败: {e}")
            return None

    @staticmethod
    def get_stock_history_data(code: str, period: str = "30d") -> list:
        """
        获取股票历史数据

        Args:
            code: 股票代码
            period: 时间周期（7d/30d/90d/1y）

        Returns:
            历史数据列表
        """
        try:
            # 计算日期范围
            end_date = datetime.now()

            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

            # 获取历史数据
            df = ak.stock_zh_a_daily(
                symbol=code,
                adjust="qfq",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d")
            )

            if df.empty:
                logger.warning(f"股票{code}历史数据为空")
                return []

            # 转换为列表格式
            history_data = []
            for idx, row in df.iterrows():
                history_data.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row['open']) if row['open'] else 0.0,
                    "high": float(row['high']) if row['high'] else 0.0,
                    "low": float(row['low']) if row['low'] else 0.0,
                    "close": float(row['close']) if row['close'] else 0.0,
                    "volume": float(row['volume']) if row['volume'] else 0.0,
                    "change_pct": 0.0  # 计算涨跌幅
                })

            # 计算涨跌幅
            for i in range(1, len(history_data)):
                prev_close = history_data[i - 1]['close']
                curr_close = history_data[i]['close']
                if prev_close > 0:
                    history_data[i]['change_pct'] = ((curr_close - prev_close) / prev_close) * 100

            return history_data

        except Exception as e:
            logger.error(f"获取股票{code}历史数据失败: {e}")
            return []

    @staticmethod
    def get_fund_realtime_data(code: str) -> Optional[Dict]:
        """
        获取基金实时数据

        Args:
            code: 基金代码

        Returns:
            基金数据字典，失败返回None
        """
        try:
            # 获取ETF实时行情
            df = ak.fund_etf_spot_em()

            # 查找指定基金
            fund_data = df[df['代码'] == code]

            if fund_data.empty:
                logger.warning(f"基金{code}未找到")
                return None

            fund = fund_data.iloc[0]

            return {
                'code': fund['代码'],
                'name': fund['名称'],
                'nav': float(fund['最新净值']) if fund['最新净值'] else 0.0,
                'acc_nav': float(fund['累计净值']) if fund['累计净值'] else 0.0,
                'change_pct': float(fund['涨跌幅']) if fund['涨跌幅'] else 0.0,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"获取基金{code}数据失败: {e}")
            return None

    @staticmethod
    def get_fund_history_data(code: str, period: str = "30d") -> list:
        """
        获取基金历史数据

        Args:
            code: 基金代码
            period: 时间周期（7d/30d/90d/1y）

        Returns:
            历史数据列表
        """
        try:
            # 计算日期范围
            end_date = datetime.now()

            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "90d":
                start_date = end_date - timedelta(days=90)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)

            # 获取历史数据
            df = ak.fund_etf_hist_em(
                symbol=code,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d")
            )

            if df.empty:
                logger.warning(f"基金{code}历史数据为空")
                return []

            # 转换为列表格式
            history_data = []
            for idx, row in df.iterrows():
                history_data.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "nav": float(row['净值']) if row['净值'] else 0.0,
                    "acc_nav": float(row['累计净值']) if row['累计净值'] else 0.0,
                    "change_pct": 0.0
                })

            # 计算涨跌幅
            for i in range(1, len(history_data)):
                prev_nav = history_data[i - 1]['nav']
                curr_nav = history_data[i]['nav']
                if prev_nav > 0:
                    history_data[i]['change_pct'] = ((curr_nav - prev_nav) / prev_nav) * 100

            return history_data

        except Exception as e:
            logger.error(f"获取基金{code}历史数据失败: {e}")
            return []

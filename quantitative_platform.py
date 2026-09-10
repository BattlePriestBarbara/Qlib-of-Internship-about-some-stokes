import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class QuantitativeAnalyzer:
    """专业量化分析引擎"""
    
    def __init__(self, stock_codes):
        """
        初始化
        stock_codes: 字典 {股票名称: 股票代码}
        """
        self.stock_codes = stock_codes
        self.stock_data = {}
        
    def fetch_realtime_data(self, code, start_date="20200101"):
        """获取实时历史数据（使用 AkShare）"""
        try:
            print(f"  📡 正在获取 {code} 数据...")
            # 获取日频数据
            df = ak.stock_zh_a_hist(
                symbol=code, 
                period="daily", 
                start_date=start_date,
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                print(f"  ⚠️ 未获取到 {code} 的数据")
                return None
                
            # 标准化列名
            df.columns = ['日期', '开盘价', '收盘价', '最高价', '最低价', '成交量', '成交额', 
                         '振幅', '涨跌幅', '涨跌额', '换手率']
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            
            print(f"  ✅ 获取成功：{len(df)} 条记录，最新价：{df['收盘价'].iloc[-1]:.2f}")
            return df
            
        except Exception as e:
            print(f"  ❌ 获取失败：{e}")
            return None
    
    def calculate_indicators(self, df):
        """计算技术指标"""
        if df is None or len(df) < 60:
            return None
            
        # 移动平均线
        df['MA5'] = df['收盘价'].rolling(5).mean()
        df['MA10'] = df['收盘价'].rolling(10).mean()
        df['MA20'] = df['收盘价'].rolling(20).mean()
        df['MA60'] = df['收盘价'].rolling(60).mean()
        
        # MACD
        exp1 = df['收盘价'].ewm(span=12, adjust=False).mean()
        exp2 = df['收盘价'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']
        
        # RSI (14日)
        delta = df['收盘价'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['BB_middle'] = df['收盘价'].rolling(20).mean()
        std = df['收盘价'].rolling(20).std()
        df['BB_upper'] = df['BB_middle'] + (std * 2)
        df['BB_lower'] = df['BB_middle'] - (std * 2)
        
        # 波动率 (年化)
        df['Daily_Return'] = df['收盘价'].pct_change()
        df['Volatility_20'] = df['Daily_Return'].rolling(20).std() * np.sqrt(252) * 100
        
        # 最大回撤 (滚动计算)
        df['Cummax'] = df['收盘价'].cummax()
        df['Drawdown'] = (df['收盘价'] - df['Cummax']) / df['Cummax'] * 100
        
        return df
    
    def generate_signals(self, df):
        """生成买卖信号"""
        signals = []
        
        # 获取最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 信号1: 均线交叉
        if latest['MA5'] > latest['MA20'] and prev['MA5'] <= prev['MA20']:
            signals.append("🟢 金叉信号 (MA5上穿MA20)")
        elif latest['MA5'] < latest['MA20'] and prev['MA5'] >= prev['MA20']:
            signals.append("🔴 死叉信号 (MA5下穿MA20)")
            
        # 信号2: MACD
        if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
            signals.append("🟢 MACD金叉")
        elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
            signals.append("🔴 MACD死叉")
            
        # 信号3: RSI
        if latest['RSI'] < 30:
            signals.append("🟢 RSI超卖 (<30)")
        elif latest['RSI'] > 70:
            signals.append("🔴 RSI超买 (>70)")
            
        # 信号4: 布林带
        if latest['收盘价'] < latest['BB_lower']:
            signals.append("🟢 跌破布林带下轨")
        elif latest['收盘价'] > latest['BB_upper']:
            signals.append("🔴 突破布林带上轨")
            
        # 趋势判断
        if latest['MA5'] > latest['MA10'] > latest['MA20']:
            trend = "📈 强势上涨"
        elif latest['MA5'] < latest['MA10'] < latest['MA20']:
            trend = "📉 强势下跌"
        else:
            trend = "📊 震荡整理"
            
        return signals, trend
    
    def calculate_metrics(self, df):
        """计算量化指标"""
        if df is None or len(df) < 252:
            return None
            
        latest_close = df['收盘价'].iloc[-1]
        
        # 收益率
        total_return = (df['收盘价'].iloc[-1] / df['收盘价'].iloc[0] - 1) * 100
        
        # 年化收益率
        years = len(df) / 252
        annual_return = ((1 + total_return/100) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # 波动率
        volatility = df['Daily_Return'].std() * np.sqrt(252) * 100
        
        # 夏普比率 (假设无风险利率3%)
        risk_free = 3.0
        sharpe = (annual_return - risk_free) / volatility if volatility > 0 else 0
        
        # 最大回撤
        max_drawdown = df['Drawdown'].min()
        
        # 胜率 (上涨天数比例)
        win_rate = (df['Daily_Return'] > 0).sum() / len(df) * 100
        
        return {
            "最新价": round(latest_close, 2),
            "累计收益(%)": round(total_return, 2),
            "年化收益(%)": round(annual_return, 2),
            "波动率(%)": round(volatility, 2),
            "夏普比率": round(sharpe, 3),
            "最大回撤(%)": round(max_drawdown, 2),
            "胜率(%)": round(win_rate, 2)
        }
    
    def plot_analysis(self, df, stock_name, code):
        """绘制专业图表"""
        if df is None:
            return
            
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        fig.suptitle(f'{stock_name} ({code}) 量化分析报告', fontsize=16, fontweight='bold')
        
        # 子图1: K线 + 均线 + 布林带
        ax1 = axes[0]
        ax1.plot(df.index, df['收盘价'], label='收盘价', linewidth=1.5, alpha=0.7)
        ax1.plot(df.index, df['MA5'], label='MA5', linewidth=1)
        ax1.plot(df.index, df['MA20'], label='MA20', linewidth=1)
        ax1.fill_between(df.index, df['BB_lower'], df['BB_upper'], alpha=0.1, label='布林带')
        ax1.set_ylabel('价格 (元)')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('价格趋势与技术指标')
        
        # 子图2: MACD
        ax2 = axes[1]
        ax2.plot(df.index, df['MACD'], label='MACD', linewidth=1.5)
        ax2.plot(df.index, df['Signal'], label='Signal', linewidth=1.5)
        ax2.bar(df.index, df['Histogram'], color='gray', alpha=0.3, label='Histogram')
        ax2.axhline(y=0, color='black', linewidth=0.5)
        ax2.set_ylabel('MACD')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # 子图3: RSI
        ax3 = axes[2]
        ax3.plot(df.index, df['RSI'], label='RSI', linewidth=1.5)
        ax3.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='超买线(70)')
        ax3.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='超卖线(30)')
        ax3.fill_between(df.index, 30, 70, alpha=0.1)
        ax3.set_ylabel('RSI')
        ax3.set_ylim(0, 100)
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        
        # 子图4: 回撤
        ax4 = axes[3]
        ax4.fill_between(df.index, 0, df['Drawdown'], alpha=0.5, color='red')
        ax4.set_ylabel('回撤 (%)')
        ax4.set_title('历史最大回撤')
        ax4.grid(True, alpha=0.3)
        
        # 格式化x轴日期
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            
        plt.tight_layout()
        
        # 保存图片
        save_path = f"D:/my_qlib_project/{stock_name}_{code}.png"
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  📊 图表已保存: {save_path}")
        plt.close()
    
    def analyze_all(self):
        """分析所有股票"""
        print("=" * 80)
        print("🎯 专业量化投资分析平台 v1.0")
        print("=" * 80)
        
        all_results = []
        
        for name, code in self.stock_codes.items():
            print(f"\n{'='*80}")
            print(f"📈 分析: {name} ({code})")
            print(f"{'='*80}")
            
            # 1. 获取数据
            df = self.fetch_realtime_data(code)
            if df is None:
                continue
                
            # 2. 计算指标
            df = self.calculate_indicators(df)
            if df is None:
                print("  ⚠️ 数据量不足，跳过")
                continue
                
            # 3. 生成信号
            signals, trend = self.generate_signals(df)
            
            # 4. 计算指标
            metrics = self.calculate_metrics(df)
            
            # 5. 打印结果
            print(f"\n📊 最新数据 (截至 {df.index[-1].strftime('%Y-%m-%d')}):")
            print(f"  最新价: ¥{metrics['最新价']}")
            print(f"  累计收益: {metrics['累计收益(%)']}%")
            print(f"  年化收益: {metrics['年化收益(%)']}%")
            print(f"  夏普比率: {metrics['夏普比率']}")
            print(f"  最大回撤: {metrics['最大回撤(%)']}%")
            print(f"  波动率: {metrics['波动率(%)']}%")
            print(f"  胜率: {metrics['胜率(%)']}%")
            
            print(f"\n📈 趋势判断: {trend}")
            
            print(f"\n🎯 交易信号:")
            if signals:
                for sig in signals:
                    print(f"  {sig}")
            else:
                print("  ⚪ 无明显信号")
                
            # 6. 绘图
            self.plot_analysis(df, name, code)
            
            # 7. 保存结果
            result = {
                "股票名称": name,
                "股票代码": code,
                **metrics,
                "趋势": trend,
                "信号数量": len(signals)
            }
            all_results.append(result)
            
        # 汇总报告
        if all_results:
            results_df = pd.DataFrame(all_results)
            results_df = results_df.sort_values("夏普比率", ascending=False)
            
            print(f"\n{'='*80}")
            print("🏆 综合排名 (按夏普比率)")
            print(f"{'='*80}")
            print(results_df.to_string(index=False))
            
            # 保存CSV
            csv_path = "D:/my_qlib_project/quantitative_analysis.csv"
            results_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\n✅ 完整报告已保存: {csv_path}")
            
            # 投资建议
            print(f"\n{'='*80}")
            print("💡 量化投资建议")
            print(f"{'='*80}")
            best = results_df.iloc[0]
            print(f"⭐ 最优标的: {best['股票名称']} (夏普比率: {best['夏普比率']})")
            print(f"⚠️  风险提示: 最大回撤最深的股票: {results_df.loc[results_df['最大回撤(%)'].idxmin(), '股票名称']}")
            print(f"\n📌 免责声明: 本分析仅供参考，不构成投资建议。投资有风险，决策需谨慎。")
            
        return all_results

# ============ 主程序 ============
if __name__ == "__main__":
    # 定义股票池
    stock_pool = {
        "万华化学": "600309",
        "隆基绿能": "601012",
        "华勤技术": "603296",
        "洛阳钼业": "603993",
        "建投能源": "000600",
        "紫光股份": "000938"
    }
    
    # 创建分析器并运行
    analyzer = QuantitativeAnalyzer(stock_pool)
    analyzer.analyze_all()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 尝试导入 AkShare
try:
    import akshare as ak
    HAS_AK = True
except ImportError:
    HAS_AK = False

# 导入 Qlib (本地数据保底)
import qlib
from qlib.config import REG_CN
from qlib.data import D

# 初始化 Qlib
qlib.init(provider_uri=r"D:\qlib_data\cn_data", region=REG_CN)

def get_stock_data(code, name):
    """获取数据：优先联网，失败则用本地 Qlib"""
    print(f"\n--- 正在处理: {name} ({code}) ---")
    
    # 1. 尝试 AkShare (实时数据)
    if HAS_AK:
        try:
            print("  [1/2] 尝试联网获取最新数据...")
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20190101", end_date="20260613", adjust="qfq")
            if not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                df.set_index('日期', inplace=True)
                df.rename(columns={'收盘': 'close', '开盘': 'open', '最高': 'high', '最低': 'low', '成交量': 'volume'}, inplace=True)
                print(f"  ✅ 联网成功！获取到 {len(df)} 条数据 (最新: {df.index[-1].date()})")
                return df
        except Exception as e:
            print(f"  ⚠️ 联网失败: {str(e)[:50]}...")

    # 2. 回退到 Qlib (本地数据)
    print("  [2/2] 切换到本地 Qlib 数据...")
    try:
        qlib_code = f"SH{code}" if code.startswith('6') else f"SZ{code}"
        df = D.features([qlib_code], ["$close", "$open", "$high", "$low", "$volume"], 
                        start_time="2019-01-01", end_time="2021-12-31")
        
        if not df.empty:
            df = df.droplevel(0) 
            df.index.name = '日期'
            # 🔑 关键修复：将 Qlib 的列名 ($close) 统一改为标准列名 (close)
            df.rename(columns={'$close': 'close', '$open': 'open', '$high': 'high', '$low': 'low', '$volume': 'volume'}, inplace=True)
            print(f"  ✅ 本地数据加载成功！获取到 {len(df)} 条数据 (截止: {df.index[-1].date()})")
            return df
    except Exception as e:
        print(f"   本地数据也失败: {e}")
        
    return None

def calculate_indicators(df):
    """计算技术指标"""
    df['MA5'] = df['close'].rolling(5).mean()
    df['MA20'] = df['close'].rolling(20).mean()
    df['MA60'] = df['close'].rolling(60).mean()
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 布林带
    df['BB_mid'] = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    df['BB_up'] = df['BB_mid'] + 2*std
    df['BB_low'] = df['BB_mid'] - 2*std
    
    # 最大回撤
    df['Cummax'] = df['close'].cummax()
    df['Drawdown'] = (df['close'] - df['Cummax']) / df['Cummax'] * 100
    
    return df

def plot_stock(df, name, code):
    """画图"""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f'{name} ({code}) 趋势分析', fontsize=16)
    
    # 上图：价格 + 均线 + 布林带
    ax1.plot(df.index, df['close'], label='Close Price', color='blue', alpha=0.6)
    ax1.plot(df.index, df['MA5'], label='MA5', color='orange')
    ax1.plot(df.index, df['MA20'], label='MA20', color='red')
    ax1.fill_between(df.index, df['BB_low'], df['BB_up'], color='gray', alpha=0.2, label='Bollinger Bands')
    ax1.set_ylabel('Price')
    ax1.legend(loc='upper left')
    ax1.grid(True)
    
    # 中图：MACD
    ax2.plot(df.index, df['MACD'], label='MACD', color='blue')
    ax2.plot(df.index, df['Signal'], label='Signal', color='red')
    ax2.bar(df.index, df['MACD'] - df['Signal'], color='gray', alpha=0.5)
    ax2.set_ylabel('MACD')
    ax2.legend(loc='upper left')
    ax2.grid(True)
    
    # 下图：最大回撤
    ax3.fill_between(df.index, 0, df['Drawdown'], color='red', alpha=0.5)
    ax3.set_ylabel('Drawdown (%)')
    ax3.set_xlabel('Date')
    ax3.grid(True)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    save_path = f"D:/my_qlib_project/{name}_{code}.png"
    plt.savefig(save_path)
    print(f"   图表已保存: {save_path}")
    plt.close()

def main():
    print("="*60)
    print("🚀 混合模式量化分析平台 (联网 + 本地保底)")
    print("="*60)
    
    stocks = {
        "万华化学": "600309",
        "隆基绿能": "601012",
        "洛阳钼业": "603993",
        "紫光股份": "000938",
        "建投能源": "000600"
    }
    
    results = []
    
    for name, code in stocks.items():
        df = get_stock_data(code, name)
        if df is None:
            continue
            
        df = calculate_indicators(df)
        
        latest_price = df['close'].iloc[-1]
        start_price = df['close'].iloc[0]
        total_return = (latest_price / start_price - 1) * 100
        max_drawdown = df['Drawdown'].min()
        
        print(f"  📈 最新价: {latest_price:.2f} | 区间收益: {total_return:.2f}% | 最大回撤: {max_drawdown:.2f}%")
        
        plot_stock(df, name, code)
        
        results.append({
            "股票": name,
            "代码": code,
            "最新价": latest_price,
            "区间收益(%)": round(total_return, 2),
            "最大回撤(%)": round(max_drawdown, 2)
        })
        
    if results:
        res_df = pd.DataFrame(results)
        res_df.to_csv("D:/my_qlib_project/hybrid_result.csv", index=False, encoding='utf-8-sig')
        print("\n" + "="*60)
        print("🏆 分析汇总:")
        print(res_df.to_string(index=False))
        print(f"\n✅ 结果已保存至 hybrid_result.csv")

if __name__ == "__main__":
    main()
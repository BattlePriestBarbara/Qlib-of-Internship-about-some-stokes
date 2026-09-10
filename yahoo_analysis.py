import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def get_yahoo_data(code, name):
    """使用 Yahoo Finance 获取数据（海外可访问）"""
    print(f"\n--- 正在处理: {name} ({code}) ---")
    
    try:
        # Yahoo Finance 格式：600309.SS (上海) 或 000938.SZ (深圳)
        if code.startswith('6'):
            yahoo_code = f"{code}.SS"
        else:
            yahoo_code = f"{code}.SZ"
        
        print(f"  📡 从 Yahoo Finance 获取 {yahoo_code}...")
        stock = yf.Ticker(yahoo_code)
        df = stock.history(start="2019-01-01", end=datetime.now().strftime("%Y-%m-%d"))
        
        if df.empty:
            print(f"  ⚠️ 未获取到数据")
            return None
            
        # 标准化列名
        df = df.rename(columns={
            'Close': 'close',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Volume': 'volume'
        })
        
        print(f"  ✅ 获取成功！{len(df)} 条数据 (最新: {df.index[-1].date()})")
        return df
        
    except Exception as e:
        print(f"  ❌ 获取失败: {str(e)[:100]}")
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
    fig.suptitle(f'{name} ({code}) - 最新趋势分析', fontsize=16)
    
    # 价格 + 均线
    ax1.plot(df.index, df['close'], label='收盘价', color='blue', linewidth=2)
    ax1.plot(df.index, df['MA5'], label='MA5', color='orange')
    ax1.plot(df.index, df['MA20'], label='MA20', color='red')
    ax1.fill_between(df.index, df['BB_low'], df['BB_up'], color='gray', alpha=0.2, label='布林带')
    ax1.set_ylabel('价格 (元)')
    ax1.legend(loc='upper left')
    ax1.grid(True)
    
    # MACD
    ax2.plot(df.index, df['MACD'], label='MACD', color='blue')
    ax2.plot(df.index, df['Signal'], label='Signal', color='red')
    ax2.bar(df.index, df['MACD'] - df['Signal'], color='gray', alpha=0.5)
    ax2.set_ylabel('MACD')
    ax2.legend(loc='upper left')
    ax2.grid(True)
    
    # 回撤
    ax3.fill_between(df.index, 0, df['Drawdown'], color='red', alpha=0.5)
    ax3.set_ylabel('回撤 (%)')
    ax3.set_xlabel('日期')
    ax3.grid(True)
    
    plt.tight_layout()
    save_path = f"D:/my_qlib_project/{name}_{code}_latest.png"
    plt.savefig(save_path, dpi=150)
    print(f"  📊 图表已保存: {save_path}")
    plt.close()

def main():
    print("="*60)
    print("🚀 Yahoo Finance 量化分析平台 (英国可用)")
    print("="*60)
    
    stocks = {
        "万华化学": "600309",
        "隆基绿能": "601012",
        "华勤技术": "603296",
        "洛阳钼业": "603993",
        "紫光股份": "000938",
        "建投能源": "000600"
    }
    
    results = []
    
    for name, code in stocks.items():
        df = get_yahoo_data(code, name)
        if df is None:
            continue
            
        df = calculate_indicators(df)
        
        latest_price = df['close'].iloc[-1]
        start_price = df['close'].iloc[0]
        total_return = (latest_price / start_price - 1) * 100
        max_drawdown = df['Drawdown'].min()
        
        # 趋势判断
        latest = df.iloc[-1]
        if latest['MA5'] > latest['MA20'] > latest['MA60']:
            trend = "📈 强势上涨"
        elif latest['MA5'] < latest['MA20'] < latest['MA60']:
            trend = "📉 强势下跌"
        else:
            trend = "📊 震荡整理"
        
        print(f"  📈 最新价: ¥{latest_price:.2f} | 总收益: {total_return:.2f}% | 最大回撤: {max_drawdown:.2f}%")
        print(f"  🎯 趋势: {trend}")
        
        plot_stock(df, name, code)
        
        results.append({
            "股票": name,
            "代码": code,
            "最新价": round(latest_price, 2),
            "总收益(%)": round(total_return, 2),
            "最大回撤(%)": round(max_drawdown, 2),
            "趋势": trend
        })
        
    if results:
        res_df = pd.DataFrame(results)
        res_df = res_df.sort_values("总收益(%)", ascending=False)
        
        print("\n" + "="*60)
        print("🏆 最新分析汇总 (按收益排名):")
        print("="*60)
        print(res_df.to_string(index=False))
        
        res_df.to_csv("D:/my_qlib_project/latest_analysis.csv", index=False, encoding='utf-8-sig')
        print(f"\n✅ 结果已保存至 latest_analysis.csv")
        
        # 投资建议
        print("\n" + "="*60)
        print("💡 量化投资建议")
        print("="*60)
        best = res_df.iloc[0]
        print(f"⭐ 表现最佳: {best['股票']} (总收益: {best['总收益(%)']}%)")
        print(f"⚠️  风险最大: {res_df.loc[res_df['最大回撤(%)'].idxmin(), '股票']} (最大回撤: {res_df['最大回撤(%)'].min():.2f}%)")
        print(f"\n📌 免责声明: 本分析仅供参考，不构成投资建议。")

if __name__ == "__main__":
    main()
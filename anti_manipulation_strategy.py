import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 第一部分：数据获取
# ============================================================
def fetch_data(stock_dict, start_date="2020-01-01"):
    """获取股票数据"""
    print("="*70)
    print("📡 第一阶段：获取股票数据")
    print("="*70)
    
    all_data = {}
    for name, code in stock_dict.items():
        yahoo_code = f"{code}.SS" if code.startswith('6') else f"{code}.SZ"
        print(f"  获取 {name} ({yahoo_code})...")
        try:
            df = yf.Ticker(yahoo_code).history(start=start_date)
            if not df.empty:
                df = df.rename(columns={
                    'Close': 'close', 'Open': 'open', 
                    'High': 'high', 'Low': 'low', 'Volume': 'volume'
                })
                all_data[name] = df
                print(f"    ✅ 成功：{len(df)} 条数据")
            else:
                print(f"    ❌ 无数据")
        except Exception as e:
            print(f"    ❌ 失败：{e}")
    return all_data

# ============================================================
# 第二部分：计算"反操纵"因子
# ============================================================
def calculate_manipulation_factors(df):
    """计算6个庄家操纵特征因子"""
    df = df.copy()
    
    # 基础收益率
    df['return'] = df['close'].pct_change()
    
    # 因子1：异常成交量 (ABV) - 当日成交量 / 20日均量
    df['ABV'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # 因子2：价格冲击 (IMPACT) - Kyle's Lambda 简化版
    # 单位成交量引起的价格变化，越大说明越容易被操纵
    df['IMPACT'] = df['return'].abs() / (df['volume'] / 1e6 + 1)
    
    # 因子3：振幅因子 (AMPL) - 日内波动幅度
    df['AMPL'] = (df['high'] - df['low']) / df['close']
    
    # 因子4：短期反转 (REV5) - 过去5日累计收益
    df['REV5'] = df['close'].pct_change(5)
    
    # 因子5：波动率 (VOL20) - 20日收益率标准差
    df['VOL20'] = df['return'].rolling(20).std() * np.sqrt(252)
    
    # 因子6：量价背离 (DIVER) - 价格创新高但成交量萎缩
    price_high = df['close'].rolling(20).max()
    vol_ma = df['volume'].rolling(20).mean()
    df['DIVER'] = (df['close'] / price_high) / (df['volume'] / vol_ma + 1)
    
    # 综合操纵指数 (Manipulation Index) - 加权平均
    # 标准化每个因子（Z-score）
    factors = ['ABV', 'IMPACT', 'AMPL', 'VOL20']
    for f in factors:
        df[f'{f}_z'] = (df[f] - df[f].rolling(60).mean()) / (df[f].rolling(60).std() + 1e-8)
    
    # 操纵指数：越高说明越可能有庄家操纵
    df['MANIP_INDEX'] = (
        df['ABV_z'] * 0.3 +      # 异常成交量权重30%
        df['IMPACT_z'] * 0.25 +  # 价格冲击权重25%
        df['AMPL_z'] * 0.25 +    # 振幅权重25%
        df['VOL20_z'] * 0.2      # 波动率权重20%
    )
    
    return df

# ============================================================
# 第三部分：策略构建
# ============================================================
def build_strategy(all_data):
    """基于操纵指数构建投资组合"""
    print("\n" + "="*70)
    print("🧠 第二阶段：计算操纵因子与策略信号")
    print("="*70)
    
    results = []
    
    for name, df in all_data.items():
        df = calculate_manipulation_factors(df)
        
        # 取最新数据
        latest = df.iloc[-1]
        
        # 策略逻辑：
        # - 操纵指数高 + 短期反转正 = 可能是洗盘结束，买入信号
        # - 操纵指数高 + 量价背离 = 可能是出货，卖出信号
        # - 操纵指数低 = 市场自然波动，按趋势操作
        
        manip_score = latest['MANIP_INDEX']
        rev5 = latest['REV5']
        diver = latest['DIVER']
        
        # 综合打分
        if manip_score > 1.5 and rev5 > 0:
            signal = "🟢 洗盘结束 - 买入"
            score = 80
        elif manip_score > 1.5 and diver < 0.9:
            signal = "🔴 疑似出货 - 卖出"
            score = 20
        elif manip_score < 0:
            signal = "⚪ 自然波动 - 持有"
            score = 50
        else:
            signal = "🟡 观望"
            score = 50
        
        print(f"\n{name}:")
        print(f"  操纵指数: {manip_score:.3f} (越高越可能被操纵)")
        print(f"  短期反转: {rev5*100:.2f}%")
        print(f"  量价背离: {diver:.3f}")
        print(f"  👉 信号: {signal}")
        
        results.append({
            '股票': name,
            '最新价': round(latest['close'], 2),
            '操纵指数': round(manip_score, 3),
            '短期反转(%)': round(rev5*100, 2),
            '量价背离': round(diver, 3),
            '波动率(%)': round(latest['VOL20']*100, 2),
            '信号': signal,
            '综合评分': score
        })
    
    return pd.DataFrame(results).sort_values('综合评分', ascending=False)

# ============================================================
# 第四部分：历史回测
# ============================================================
def backtest_strategy(all_data):
    """简单回测：做多低操纵+正反转的股票"""
    print("\n" + "="*70)
    print("📊 第三阶段：历史回测")
    print("="*70)
    
    # 合并所有股票数据
    panel = pd.DataFrame()
    for name, df in all_data.items():
        df = calculate_manipulation_factors(df)
        df['股票'] = name
        panel = pd.concat([panel, df])
    
    # 每月调仓一次
    panel['month'] = panel.index.to_period('M')
    
    # 策略：每月选择操纵指数最低 + 短期反转最高的股票
    monthly_returns = []
    
    for month, group in panel.groupby('month'):
        # 取每月最后一天的数据
        last_day = group.groupby('股票').tail(1)
        
        if len(last_day) < 2:
            continue
        
        # 打分：操纵指数低（好）+ 反转高（好）
        last_day['score'] = -last_day['MANIP_INDEX'] * 0.5 + last_day['REV5'] * 10
        last_day = last_day.dropna(subset=['score'])
        
        if len(last_day) == 0:
            continue
        
        # 选前2名做多
        top = last_day.nlargest(min(2, len(last_day)), 'score')
        
        # 下个月收益
        next_month_data = panel[panel['month'] == month + 1]
        if len(next_month_data) > 0:
            ret = next_month_data.groupby('股票')['return'].sum().mean()
            monthly_returns.append({'月份': str(month), '策略收益': ret})
    
    if monthly_returns:
        backtest_df = pd.DataFrame(monthly_returns)
        cum_ret = (1 + backtest_df['策略收益']).cumprod()
        
        print(f"  回测月份数: {len(backtest_df)}")
        print(f"  累计收益: {(cum_ret.iloc[-1] - 1) * 100:.2f}%")
        print(f"  年化收益: {((cum_ret.iloc[-1]) ** (12/len(backtest_df)) - 1) * 100:.2f}%")
        print(f"  最大回撤: {((cum_ret / cum_ret.cummax()) - 1).min() * 100:.2f}%")
        
        return backtest_df, cum_ret
    return None, None

# ============================================================
# 第五部分：可视化
# ============================================================
def plot_results(result_df, cum_ret=None):
    """绘制分析结果"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('反操纵量化策略分析报告', fontsize=16, fontweight='bold')
    
    # 图1：操纵指数排名
    ax1 = axes[0, 0]
    colors = ['red' if x > 1 else 'orange' if x > 0 else 'green' for x in result_df['操纵指数']]
    ax1.barh(result_df['股票'], result_df['操纵指数'], color=colors)
    ax1.axvline(x=1, color='red', linestyle='--', label='操纵警戒线')
    ax1.set_xlabel('操纵指数 (越高越可能被操纵)')
    ax1.set_title('各股票操纵指数')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 图2：综合评分
    ax2 = axes[0, 1]
    colors2 = ['green' if x >= 70 else 'orange' if x >= 50 else 'red' for x in result_df['综合评分']]
    ax2.barh(result_df['股票'], result_df['综合评分'], color=colors2)
    ax2.set_xlabel('综合评分')
    ax2.set_title('投资建议评分')
    ax2.grid(True, alpha=0.3)
    
    # 图3：波动率 vs 操纵指数
    ax3 = axes[1, 0]
    ax3.scatter(result_df['操纵指数'], result_df['波动率(%)'], s=100)
    for _, row in result_df.iterrows():
        ax3.annotate(row['股票'], (row['操纵指数'], row['波动率(%)']))
    ax3.set_xlabel('操纵指数')
    ax3.set_ylabel('年化波动率 (%)')
    ax3.set_title('风险-操纵关系图')
    ax3.grid(True, alpha=0.3)
    
    # 图4：回测累计收益
    ax4 = axes[1, 1]
    if cum_ret is not None:
        ax4.plot(cum_ret.values, linewidth=2, color='blue')
        ax4.fill_between(range(len(cum_ret)), 1, cum_ret.values, alpha=0.3)
        ax4.set_xlabel('月份')
        ax4.set_ylabel('累计净值')
        ax4.set_title('策略历史回测')
        ax4.axhline(y=1, color='gray', linestyle='--')
        ax4.grid(True, alpha=0.3)
    else:
        ax4.text(0.5, 0.5, '数据不足，无法回测', ha='center', va='center', fontsize=14)
        ax4.set_title('策略历史回测')
    
    plt.tight_layout()
    save_path = "D:/my_qlib_project/anti_manipulation_report.png"
    plt.savefig(save_path, dpi=150)
    print(f"\n📊 分析报告已保存: {save_path}")
    plt.close()

# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 反操纵量化策略 v1.0")
    print("基于市场微观结构理论（Kyle 1985, Amihud 2002）")
    print("="*70)
    
    # 股票池（你母亲的持仓）
    stocks = {
        "万华化学": "600309",
        "隆基绿能": "601012",
        "华勤技术": "603296",
        "洛阳钼业": "603993",
        "紫光股份": "000938",
        "建投能源": "000600"
    }
    
    # 1. 获取数据
    all_data = fetch_data(stocks)
    
    if not all_data:
        print("❌ 未获取到任何数据")
    else:
        # 2. 构建策略
        result_df = build_strategy(all_data)
        
        print("\n" + "="*70)
        print("🏆 最终投资建议（按评分排序）")
        print("="*70)
        print(result_df.to_string(index=False))
        
        # 3. 回测
        backtest_df, cum_ret = backtest_strategy(all_data)
        
        # 4. 可视化
        plot_results(result_df, cum_ret)
        
        # 5. 保存结果
        csv_path = "D:/my_qlib_project/anti_manipulation_result.csv"
        result_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 结果已保存: {csv_path}")
        
        # 6. 老师的总结
        print("\n" + "="*70)
        print("🎓 老师的量化洞察")
        print("="*70)
        high_manip = result_df[result_df['操纵指数'] > 1]
        if len(high_manip) > 0:
            print(f"⚠️ 高度疑似被操纵的股票:")
            for _, row in high_manip.iterrows():
                print(f"   - {row['股票']} (操纵指数: {row['操纵指数']})")
        
        low_manip = result_df[result_df['操纵指数'] < 0]
        if len(low_manip) > 0:
            print(f"\n✅ 市场自然波动的股票（更适合量化分析）:")
            for _, row in low_manip.iterrows():
                print(f"   - {row['股票']} (操纵指数: {row['操纵指数']})")
        
        print("\n📌 免责声明：本策略基于统计模型，不构成投资建议。")
        print("   庄家操纵识别是学术界未完全解决的难题，本策略仅供参考。")
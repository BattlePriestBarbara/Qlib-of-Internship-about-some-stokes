import os
import sys
import numpy as np
import pandas as pd

# 1. 环境配置（解决之前的路径和编码问题）
os.environ['TEMP'] = r'D:\temp'
os.environ['TMP'] = r'D:\temp'
os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
os.environ['QLIB_NUM_PROCESS'] = '1'

import qlib
from qlib.config import REG_CN
from qlib.data import D

def calculate_metrics(close_prices):
    """计算单只股票的核心量化指标"""
    if len(close_prices) < 20:
        return None
    
    # 基础统计
    latest_price = close_prices.iloc[-1]
    total_return = (close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100
    
    # 年化收益率 (假设一年252个交易日)
    trading_days = len(close_prices)
    annual_return = ((1 + total_return/100) ** (252 / trading_days) - 1) * 100
    
    # 年化波动率 (日收益率的标准差 * sqrt(252))
    daily_returns = close_prices.pct_change().dropna()
    annual_volatility = daily_returns.std() * np.sqrt(252) * 100
    
    # 最大回撤 (Max Drawdown)
    cummax = close_prices.cummax()
    drawdown = (close_prices - cummax) / cummax
    max_drawdown = drawdown.min() * 100
    
    # 夏普比率 (假设无风险利率为 3%)
    risk_free_rate = 3.0
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
    
    # 趋势预测 (基于双均线系统 MA5 和 MA20)
    ma5 = close_prices.rolling(window=5).mean().iloc[-1]
    ma20 = close_prices.rolling(window=20).mean().iloc[-1]
    recent_5d_return = (close_prices.iloc[-1] / close_prices.iloc[-5] - 1) * 100 if len(close_prices) >= 5 else 0
    
    if ma5 > ma20 and recent_5d_return > 0:
        trend = "📈 多头趋势 (看多)"
    elif ma5 < ma20 and recent_5d_return < 0:
        trend = "📉 空头趋势 (看空)"
    else:
        trend = "📊 震荡整理 (观望)"
        
    return {
        "最新价": round(latest_price, 2),
        "累计收益(%)": round(total_return, 2),
        "年化收益(%)": round(annual_return, 2),
        "年化波动率(%)": round(annual_volatility, 2),
        "最大回撤(%)": round(max_drawdown, 2),
        "夏普比率": round(sharpe_ratio, 3),
        "趋势预测": trend
    }

if __name__ == '__main__':
    print("=" * 70)
    print("🎯 母亲持仓股票量化分析与预测系统")
    print("=" * 70)
    
    # 初始化 Qlib
    print("\n🔧 初始化 Qlib 引擎...")
    qlib.init(provider_uri=r"D:\qlib_data\cn_data", region=REG_CN)
    print("✅ 引擎就绪！")
    
    # 定义股票池 (中文名称 -> Qlib 标准代码)
    # 注意：华勤技术(603296)是2023年上市，Qlib默认数据可能不包含，脚本会自动处理
    stock_pool = {
        "万华化学": "SH600309",
        "隆基绿能": "SH601012",
        "华勤技术": "SH603296", 
        "洛阳钼业": "SH603993",
        "建投能源": "SZ000600",
        "紫光股份": "SZ000938"
    }
    
    instruments = list(stock_pool.values())
    
    # 获取历史数据 (Qlib自带数据通常到2020/2021年左右)
    print("\n📈 正在获取历史行情数据...")
    fields = ["$close", "$open", "$high", "$low", "$volume"]
    df = D.features(
        instruments, 
        fields, 
        start_time="2018-01-01", 
        end_time="2025-12-31" # 设置到未来，Qlib会自动截取到数据最新日期
    )
    
    results = []
    
    print("\n" + "=" * 70)
    print("📊 逐只股票深度分析")
    print("=" * 70)
    
    for name, code in stock_pool.items():
        print(f"\n▶ 正在分析: {name} ({code})")
        
        # 提取单只股票的数据
        if code in df.index.get_level_values('instrument'):
            stock_data = df.loc[code].copy()
            close_prices = stock_data['$close'].dropna()
            
            if len(close_prices) > 20:
                metrics = calculate_metrics(close_prices)
                if metrics:
                    metrics["股票名称"] = name
                    metrics["股票代码"] = code
                    results.append(metrics)
                    
                    # 打印单只股票结果
                    print(f"  最新价: ¥{metrics['最新价']}")
                    print(f"  累计收益: {metrics['累计收益(%)']}% | 年化收益: {metrics['年化收益(%)']}%")
                    print(f"  波动率: {metrics['年化波动率(%)']}% | 最大回撤: {metrics['最大回撤(%)']}%")
                    print(f"  夏普比率: {metrics['夏普比率']}")
                    print(f"  👉 趋势预测: {metrics['趋势预测']}")
                else:
                    print(f"  ⚠️ 数据量不足，无法计算指标。")
            else:
                print(f"  ⚠️ 数据缺失或上市时间太短（如华勤技术），跳过分析。")
        else:
            print(f"  ❌ 数据库中未找到该股票数据。")

    # 汇总并保存结果
    if results:
        results_df = pd.DataFrame(results)
        # 调整列顺序
        cols = ["股票名称", "股票代码", "最新价", "累计收益(%)", "年化收益(%)", "年化波动率(%)", "最大回撤(%)", "夏普比率", "趋势预测"]
        results_df = results_df[cols]
        
        # 按夏普比率降序排列（性价比最高的排在前面）
        results_df = results_df.sort_values(by="夏普比率", ascending=False)
        
        print("\n" + "=" * 70)
        print("🏆 综合评估排名 (按夏普比率排序，越高代表性价比越好)")
        print("=" * 70)
        print(results_df.to_string(index=False))
        
        # 保存到 CSV
        save_path = r"D:\my_qlib_project\mom_stocks_analysis.csv"
        results_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"\n✅ 分析报告已保存至: {save_path}")
        
        # 给出学术性建议
        print("\n" + "=" * 70)
        print("🎓 老师的量化建议")
        print("=" * 70)
        best_stock = results_df.iloc[0]
        worst_dd_stock = results_df.loc[results_df['最大回撤(%)'].idxmin()] # 注意：回撤是负数，idxmin是绝对值最大的
        
        print(f"1. 风险调整后收益最佳: {best_stock['股票名称']} (夏普比率: {best_stock['夏普比率']})")
        print(f"2. 历史最大回撤最深: {worst_dd_stock['股票名称']} (最大回撤: {worst_dd_stock['最大回撤(%)']}%)，需注意仓位控制。")
        print(f"3. 免责声明：以上预测基于历史数据统计与简单均线模型，不构成直接投资建议。股市有风险，投资需谨慎。")
    else:
        print("\n❌ 没有获取到有效数据，请检查股票代码或数据源。")
        
    print("\n" + "=" * 70)
    print("✨ 分析完成！")
    print("=" * 70)
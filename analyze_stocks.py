import os
os.environ['TEMP'] = r'D:\temp'
os.environ['TMP'] = r'D:\temp'
os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
os.environ['QLIB_NUM_PROCESS'] = '1'

import qlib
from qlib.config import REG_CN
from qlib.data import D
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH
import pandas as pd

if __name__ == '__main__':
    print("=" * 70)
    print("🎯 A股量化分析系统")
    print("=" * 70)
    
    # 初始化
    print("\n🔧 初始化 Qlib...")
    qlib.init(provider_uri=r"D:\qlib_data\cn_data", region=REG_CN)
    print("✅ 初始化完成！")
    
    # 选择热门股票
    stocks = [
        "SH600000",  # 浦发银行
        "SH600036",  # 招商银行
        "SH600519",  # 贵州茅台
        "SZ000001",  # 平安银行
        "SZ000858",  # 五粮液
        "SH601318",  # 中国平安
        "SZ300750",  # 宁德时代
        "SH600276",  # 恒瑞医药
    ]
    
    print("\n" + "=" * 70)
    print("📊 分析股票池:")
    print("=" * 70)
    for stock in stocks:
        print(f"  - {stock}")
    
    # 获取历史数据
    print("\n📈 获取历史数据...")
    df = D.features(
        stocks,
        ["$close", "$open", "$high", "$low", "$volume", "$change"],
        start_time="2019-01-01",
        end_time="2020-12-31"
    )
    
    print(f"✅ 获取到 {len(df)} 条记录")
    
    # 分析每只股票
    print("\n" + "=" * 70)
    print("📊 股票分析结果")
    print("=" * 70)
    
    results = []
    for stock in stocks:
        stock_data = df.loc[stock] if stock in df.index.get_level_values('instrument') else None
        
        if stock_data is not None and len(stock_data) > 0:
            close_prices = stock_data['$close']
            
            # 计算指标
            latest_price = close_prices.iloc[-1]
            avg_price = close_prices.mean()
            max_price = close_prices.max()
            min_price = close_prices.min()
            volatility = close_prices.std()
            
            # 计算收益率
            if len(close_prices) > 1:
                total_return = (close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100
            else:
                total_return = 0
            
            results.append({
                '股票代码': stock,
                '最新价': round(latest_price, 2),
                '平均价': round(avg_price, 2),
                '最高价': round(max_price, 2),
                '最低价': round(min_price, 2),
                '波动率': round(volatility, 2),
                '累计收益(%)': round(total_return, 2)
            })
            
            print(f"\n{stock}:")
            print(f"  最新价格: ¥{latest_price:.2f}")
            print(f"  平均价格: ¥{avg_price:.2f}")
            print(f"  价格区间: ¥{min_price:.2f} - ¥{max_price:.2f}")
            print(f"  波动率: {volatility:.2f}")
            print(f"  累计收益: {total_return:.2f}%")
    
    # 创建DataFrame并排序
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('累计收益(%)', ascending=False)
    
    print("\n" + "=" * 70)
    print("🏆 收益排名")
    print("=" * 70)
    print(results_df.to_string(index=False))
    
    # 保存结果
    results_df.to_csv("D:/my_qlib_project/stock_analysis.csv", index=False, encoding='utf-8-sig')
    print(f"\n✅ 分析结果已保存到: D:/my_qlib_project/stock_analysis.csv")
    
    # 推荐股票
    print("\n" + "=" * 70)
    print("💡 推荐股票（基于历史收益）")
    print("=" * 70)
    top_stocks = results_df.head(3)
    for idx, row in top_stocks.iterrows():
        print(f"  {idx+1}. {row['股票代码']} - 累计收益: {row['累计收益(%)']:.2f}% - 最新价: ¥{row['最新价']:.2f}")
    
    print("\n" + "=" * 70)
    print("✨ 分析完成！")
    print("=" * 70)
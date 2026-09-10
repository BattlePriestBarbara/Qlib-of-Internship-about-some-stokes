import os
import sys

# 关键设置
os.environ['TEMP'] = r'D:\temp'
os.environ['TMP'] = r'D:\temp'
os.environ['TMPDIR'] = r'D:\temp'
os.environ['QLIB_NUM_PROCESS'] = '1'
os.environ['PYTHONUTF8'] = '1'

import qlib
from qlib.config import REG_CN
from qlib.data import D
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH
import pandas as pd

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 初始化 Qlib...")
    print("=" * 60)
    qlib.init(
        provider_uri=r"D:\qlib_data\cn_data",
        region=REG_CN,
    )
    print("✅ Qlib 初始化成功！")
    
    print("\n" + "=" * 60)
    print("📊 准备数据集...")
    print("=" * 60)
    
    # 准备数据集
    dataset = DatasetH(
        handler=Alpha158(
            instruments=D.instruments(market='csi300'),
            start_time="2018-01-01",
            end_time="2020-06-01",
            fit_start_time="2018-01-01",
            fit_end_time="2019-12-31",
        ),
        segments={
            "train": ("2018-01-01", "2019-12-31"),
            "valid": ("2020-01-01", "2020-03-31"),
            "test": ("2020-04-01", "2020-06-01"),
        },
    )
    print("✅ 数据集准备完成！")
    
    print("\n" + "=" * 60)
    print("🚀 训练 LightGBM 模型...")
    print("=" * 60)
    
    # 创建并训练模型
    model = LGBModel(
        loss="mse",
        learning_rate=0.05,
        max_depth=5,
        num_leaves=64,
        n_estimators=100,
    )
    
    print("训练中，请稍候...")
    model.fit(dataset)
    print("✅ 模型训练完成！")
    
    print("\n" + "=" * 60)
    print("📊 生成预测...")
    print("=" * 60)
    
    # 在测试集上预测
    pred = model.predict(dataset, segment="test")
    
    print(f"\n预测结果形状: {pred.shape}")
    print("\n前20条预测结果:")
    print(pred.head(20))
    
    # 统计分析
    print("\n" + "=" * 60)
    print("📈 预测结果统计:")
    print("=" * 60)
    print(f"平均值: {pred.mean().iloc[0]:.6f}")
    print(f"标准差: {pred.std().iloc[0]:.6f}")
    print(f"最大值: {pred.max().iloc[0]:.6f}")
    print(f"最小值: {pred.min().iloc[0]:.6f}")
    
    # 保存预测结果
    pred.to_csv("D:/my_qlib_project/predictions.csv")
    print("\n✅ 预测结果已保存到: D:/my_qlib_project/predictions.csv")
    
    print("\n" + "=" * 60)
    print("🎉 预测完成！")
    print("=" * 60)
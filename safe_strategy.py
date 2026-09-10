import os
import sys

# 必须在导入 qlib 之前设置
os.environ['QLIB_NUM_PROCESS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['PYTHONUTF8'] = '1'

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

print("Starting in single-process mode...")

import qlib
from qlib.config import REG_CN
from qlib.data import D
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

print("=" * 60)
print("🔧 初始化 Qlib...")
qlib.init(
    provider_uri=r"D:\qlib_data\cn_data",
    region=REG_CN,
)

print("\n📊 准备数据集（简化版）...")
# 使用更小的数据集
dataset = DatasetH(
    handler=Alpha158(
        instruments=D.instruments(market='csi300'),
        start_time="2019-01-01",
        end_time="2020-06-01",
        fit_start_time="2019-01-01",
        fit_end_time="2019-12-31",
    ),
    segments={
        "train": ("2019-01-01", "2019-12-31"),
        "valid": ("2020-01-01", "2020-03-31"),
        "test": ("2020-04-01", "2020-06-01"),
    },
)

print("\n🚀 训练模型...")
model = LGBModel(
    loss="mse",
    learning_rate=0.05,
    max_depth=3,  # 减小深度
    num_leaves=32,
    n_estimators=50,  # 减少树的数量
)

model.fit(dataset)
print("✅ 训练完成！")

print("\n📊 生成预测...")
pred = model.predict(dataset, segment="test")
print(f"预测形状: {pred.shape}")
print(pred.head())

print("\n🎉 完成！")
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

print("\n📊 准备数据集...")
dataset = DatasetH(
    handler=Alpha158(
        instruments=D.instruments(market='csi300'),
        start_time="2018-01-01",
        end_time="2020-08-01",
        fit_start_time="2018-01-01",
        fit_end_time="2019-12-31",
    ),
    segments={
        "train": ("2018-01-01", "2019-12-31"),
        "valid": ("2020-01-01", "2020-03-31"),
        "test": ("2020-04-01", "2020-08-01"),
    },
)

print("\n🚀 训练 LightGBM 模型...")
model = LGBModel(
    loss="mse",
    learning_rate=0.05,
    max_depth=5,
    num_leaves=64,
)

model.fit(dataset)
print("✅ 训练完成！")

print("\n📊 生成预测...")
pred = model.predict(dataset, segment="test")
print(f"预测形状: {pred.shape}")
print(pred.head())

print("\n🎉 策略运行成功！")
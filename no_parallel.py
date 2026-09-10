import os
import sys

# 所有可能的环境变量设置
os.environ['QLIB_NUM_PROCESS'] = '1'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

print("Testing basic Qlib functionality...")

import qlib
from qlib.config import REG_CN
from qlib.data import D

# 初始化
qlib.init(
    provider_uri=r"D:\qlib_data\cn_data",
    region=REG_CN,
)

print("✅ Qlib initialized")

# 只测试基础功能
print("\nTest 1: Get instruments")
instruments = D.instruments(market='csi300')
inst_list = list(instruments)
print(f"Got {len(inst_list)} stocks")
print(f"First 5: {inst_list[:5]}")

print("\nTest 2: Get price data")
df = D.features(
    inst_list[:3],
    ["$close", "$open", "$high", "$low", "$volume"],
    start_time="2020-01-01",
    end_time="2020-01-31"
)

print(f"✅ Success! Shape: {df.shape}")
print(df.head(10))
print("\n🎉 All tests passed!")
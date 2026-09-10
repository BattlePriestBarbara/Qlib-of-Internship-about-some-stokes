import qlib
from qlib.config import REG_CN

# 使用 D 盘路径
qlib.init(
    provider_uri=r"D:\qlib_data\cn_data",
    region=REG_CN,
)

print("✅ Qlib 初始化成功！")
print(f"数据路径: D:\\qlib_data\\cn_data")

from qlib.data import D
df = D.features(["SH600000"], ["$close"], start_time="20200101", end_time="20200110")
print(f"✅ 数据获取成功：{len(df)} 条记录")
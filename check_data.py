import os
import sys

# 关键：设置临时文件夹到纯英文路径
os.environ['TEMP'] = r'D:\temp'
os.environ['TMP'] = r'D:\temp'
os.environ['TMPDIR'] = r'D:\temp'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'



import qlib
from qlib.config import REG_CN
from qlib.data import D

if __name__ == '__main__':
    qlib.init(
        provider_uri=r"D:\qlib_data\cn_data",
        region=REG_CN,
    )

    stocks = ["SH600000", "SH600036", "SZ000001"]

    print("Checking data for specific stocks...")
    df = D.features(
        stocks,
        ["$close"],
        start_time="2018-01-01",
        end_time="2020-12-31"
    )

    print(f"Total records: {len(df)}")
    if len(df) > 0:
        print(df.head(10))
    else:
        print("No data found!")
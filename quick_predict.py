import os
os.environ['TEMP'] = r'D:\temp'
os.environ['TMP'] = r'D:\temp'
os.environ['QLIB_NUM_PROCESS'] = '1'

import qlib
from qlib.config import REG_CN
from qlib.data import D
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.data.handler import Alpha158
from qlib.data.dataset import DatasetH

if __name__ == '__main__':
    print("Initializing...")
    qlib.init(provider_uri=r"D:\qlib_data\cn_data", region=REG_CN)
    
    print("Preparing dataset...")
    dataset = DatasetH(
        handler=Alpha158(
            instruments=D.instruments(market='csi300'),
            start_time="2019-01-01",
            end_time="2020-03-01",
            fit_start_time="2019-01-01",
            fit_end_time="2019-12-31",
        ),
        segments={
            "train": ("2019-01-01", "2019-12-31"),
            "valid": ("2020-01-01", "2020-02-01"),
            "test": ("2020-02-01", "2020-03-01"),
        },
    )
    
    print("Training model...")
    model = LGBModel(loss="mse", learning_rate=0.05, max_depth=3, num_leaves=32)
    model.fit(dataset)
    
    print("Predicting...")
    pred = model.predict(dataset, segment="test")
    print(f"\n✅ Success! Shape: {pred.shape}")
    print(pred.head(10))
    
    # 保存结果
    pred.to_csv("D:/my_qlib_project/predictions.csv")
    print("\n✅ Saved to predictions.csv")
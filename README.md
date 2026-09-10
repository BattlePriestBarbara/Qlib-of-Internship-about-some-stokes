# Qlib 金融量化分析项目文档

> 基于 Microsoft Qlib 的 A 股量化投资实习项目
> 覆盖「数据准备 → 因子构建 → 模型训练 → 策略回测 → 可视化 → PDF 报告」的完整量化研究流程

---

## 一、项目背景与目标

本项目是围绕 **Microsoft Qlib** 开源量化投资平台搭建的一套 A 股量化研究工具集，主要用于金融量化实习中的实际研究工作。项目以本地 Qlib 数据库（`D:\qlib_data\cn_data`）为核心数据源，同时兼容 AkShare、Yahoo Finance 等联网数据源作为补充/兜底。

项目围绕一组真实持仓股票（被注释为「母亲的持仓」）展开，主要股票池如下：

| 股票名称 | 代码 | Qlib 代码 | Yahoo 代码 |
| --- | --- | --- | --- |
| 万华化学 | 600309 | SH600309 | 600309.SS |
| 隆基绿能 | 601012 | SH601012 | 601012.SS |
| 华勤技术 | 603296 | SH603296 | 603296.SS |
| 洛阳钼业 | 603993 | SH603993 | 603993.SS |
| 紫光股份 | 000938 | SZ000938 | 000938.SZ |
| 建投能源 | 000600 | SZ000600 | 000600.SZ |

项目要达成的目标：

1. **打通数据链路**：验证 Qlib 本地数据可用性，解决中文路径/编码/多进程等工程问题。
2. **构建因子模型**：基于 Alpha158 因子库以及自定义「反操纵」六因子模型进行特征工程。
3. **训练预测模型**：使用 LightGBM 对股票收益进行建模与预测。
4. **风险评估**：计算年化收益、波动率、夏普比率、最大回撤等核心风险指标。
5. **策略回测与信号生成**：产出买入/卖出/持有信号并做简易历史回测。
6. **自动出具报告**：将分析结果可视化为 PNG 图表，并生成中文 PDF 研究报告。

---

## 二、运行环境与依赖

### 2.1 基础环境

| 项目 | 说明 |
| --- | --- |
| 操作系统 | Windows（路径含中文，脚本中通过 `TEMP` 重定向与 UTF-8 编码规避） |
| Python | Anaconda 环境（`D:\Anaconda3`） |
| 数据目录 | `D:\qlib_data\cn_data`（Qlib 二进制数据） |
| 临时目录 | `D:\temp`（脚本中强制设置，避免中文用户名路径导致的问题） |

### 2.2 核心依赖及实测版本

| 包 | 版本 | 用途 |
| --- | --- | --- |
| qlib | 0.9.7 | 量化数据/因子/模型框架 |
| pandas | 2.2.2 | 数据处理 |
| numpy | 1.26.4 | 数值计算 |
| matplotlib | 3.8.4 | 可视化 |
| lightgbm | 4.6.0 | GBDT 预测模型 |
| scikit-learn | 1.5.1 | 机器学习工具 |
| torch | 2.8.0 | 深度学习依赖（Qlib 后端） |
| mlflow | 3.2.0 | 实验追踪（`mlruns/`） |
| yfinance | 0.2.66 | Yahoo Finance 数据源 |
| akshare | 未安装（脚本自动降级） | A 股实时数据源 |
| reportlab | 未安装 | PDF 报告生成 |

> ⚠️ **注意**：当前环境中 `akshare` 与 `reportlab` 未安装。
> - `hybrid_analysis.py` 已内置 `try/except ImportError`，无 AkShare 时自动回退本地 Qlib 数据。
> - `generate_pdf_report.py` / `generate_anti_manipulation_report.py` 依赖 `reportlab`，如需重新生成 PDF 请先 `pip install reportlab akshare`。

### 2.3 安装依赖

```bash
pip install pyqlib lightgbm yfinance reportlab akshare
```

---

## 三、目录结构

```
d:\my_qlib_project\
│
├── 【数据准备与模型训练】
│   ├── test_qlib.py                    # Qlib 初始化连通性测试
│   ├── check_data.py                   # 指定股票数据可用性检查
│   ├── no_parallel.py                  # 单进程模式基础功能测试
│   ├── safe_strategy.py                # 单进程安全版 LightGBM 策略
│   ├── full_strategy.py                # 完整版 LightGBM 预测流程
│   ├── quick_predict.py                # 快速训练+预测脚本
│   └── train_and_predict.py            # Alpha158 + LightGBM 训练预测
│
├── 【个股量化分析】
│   ├── analyze_stocks.py               # 8 只热门股票收益分析
│   ├── mom_stocks_analysis.py          # 持仓股票多指标分析（夏普/回撤）
│   ├── quantitative_platform.py        # AkShare 专业量化分析平台
│   ├── hybrid_analysis.py              # 混合数据源(联网+本地)分析
│   └── yahoo_analysis.py               # Yahoo Finance 数据源分析
│
├── 【反操纵策略】
│   ├── anti_manipulation_strategy.py   # 六因子反操纵策略 + 回测
│   └── generate_anti_manipulation_report.py  # 反操纵中文 PDF 报告
│
├── 【报告生成】
│   └── generate_pdf_report.py          # 资产分析预测中文 PDF 报告
│
├── 【配置】
│   └── .vscode\settings.json           # VS Code conda 环境配置
│
├── 【结果输出】
│   ├── stock_analysis.csv              # 热门股票分析结果
│   ├── mom_stocks_analysis.csv         # 持仓股票多指标结果
│   ├── hybrid_result.csv               # 混合数据源分析结果
│   ├── latest_analysis.csv             # 最新行情趋势分析结果
│   ├── anti_manipulation_result.csv    # 反操纵策略信号结果
│   ├── anti_manipulation_report.png    # 反操纵策略汇总图
│   ├── 紫光股份_000938_latest.png       # 个股最新趋势图
│   ├── _bar_comparison.png             # 收益对比柱状图
│   ├── _factor_radar.png               # 因子雷达图
│   ├── _manip_scatter.png              # 操纵指数散点图
│   ├── _radar_chart.png                # 综合指标雷达图
│   ├── _score_heatmap.png              # 评分热力图
│   ├── _score_stacked.png              # 操纵指数与评分图
│   ├── 反操纵量化分析报告.pdf            # 反操纵策略 PDF 报告
│   └── 量化资产分析与预测报告.pdf          # 资产分析 PDF 报告
│
├── 【中间产物】
│   ├── .1.png\                         # 全部个股趋势图归档
│   │   ├── 万华化学_600309.png / _latest.png
│   │   ├── 隆基绿能_601012.png / _latest.png
│   │   ├── 华勤技术_603296_latest.png
│   │   ├── 洛阳钼业_603993.png / _latest.png
│   │   ├── 建投能源_000600.png / _latest.png
│   │   └── 紫光股份_000938.png
│   └── mlruns\                         # MLflow 实验追踪目录（当前为空）
│
└── README.md                           # 本文档
```

---

## 四、脚本模块详解

### 4.1 数据准备与模型训练模块

#### `test_qlib.py`
最小化连通性验证脚本。初始化 Qlib（`provider_uri=D:\qlib_data\cn_data`, `region=REG_CN`），读取 `SH600000` 在 `20200101~20200110` 的收盘价，用于确认「Qlib 能否正常初始化并取到数据」。

#### `check_data.py`
数据核查脚本。在导入 Qlib **之前**把 `TEMP/TMP/TMPDIR` 重定向到 `D:\temp` 并设置 `PYTHONUTF8=1`，随后批量检查 `SH600000 / SH600036 / SZ000001` 三只股票 `2018-2020` 的收盘价数据量，打印前 10 行。这是解决「中文用户名导致临时文件路径异常」问题的关键模板。

#### `no_parallel.py`
单进程模式基础功能测试。通过设置 `QLIB_NUM_PROCESS=1`、`MKL_NUM_THREADS=1`、`OMP_NUM_THREADS=1` 等环境变量，把 Qlib 限制为单进程运行（规避 Windows 下多进程/多线程崩溃），并测试：
- `D.instruments(market='csi300')` 获取 CSI300 成分股；
- `D.features(...)` 读取前 3 只股票的 OHLCV 数据。

#### `safe_strategy.py`
「安全版」完整策略。在单进程环境下，用较小的数据集（`2019-01-01 ~ 2020-06-01`）训练一个轻量 LightGBM（`max_depth=3`, `num_leaves=32`, `n_estimators=50`），用于在资源受限时也能跑通全流程。

#### `full_strategy.py`
完整版训练流程：`Alpha158` 因子 + `LGBModel`，训练集 `2018-2019`，验证集 `2020Q1`，测试集 `2020Q2~Q3`，输出预测结果形状与前几行。

#### `quick_predict.py`
快速预测脚本，使用更短的时间窗口（`2019-01-01 ~ 2020-03-01`）训练 `LGBModel(learning_rate=0.05, max_depth=3, num_leaves=32)`，并将预测结果保存为 `predictions.csv`。

#### `train_and_predict.py`
主力训练脚本。使用 `Alpha158` 因子集 + `LGBModel(learning_rate=0.05, max_depth=5, num_leaves=64, n_estimators=100)`：
- 训练集：`2018-01-01 ~ 2019-12-31`
- 验证集：`2020-01-01 ~ 2020-03-31`
- 测试集：`2020-04-01 ~ 2020-06-01`

输出预测结果的**均值、标准差、最大值、最小值**统计，并保存到 `predictions.csv`。


---

### 4.2 个股量化分析模块

#### `analyze_stocks.py`
对 8 只热门股票（浦发银行、招商银行、贵州茅台、平安银行、五粮液、中国平安、宁德时代、恒瑞医药）做基础统计：最新价、平均价、最高/最低价、波动率、累计收益率，按累计收益排序，结果保存到 `stock_analysis.csv`，并输出 Top3 推荐。

#### `mom_stocks_analysis.py` ★
针对「持仓股票池」的核心分析脚本，使用 Qlib 本地数据（`2018-01-01 ~ 2025-12-31`，Qlib 自动截断至最新可用日期），为每只股票计算：

| 指标 | 计算方法 |
| --- | --- |
| 累计收益 | `(P_t / P_0 - 1) × 100%` |
| 年化收益 | `((1 + 累计收益) ^ (252/交易日数) - 1) × 100%` |
| 年化波动率 | `日收益率标准差 × √252 × 100%` |
| 最大回撤 | `min((P_t - cummax(P)) / cummax(P)) × 100%` |
| 夏普比率 | `(年化收益 - 3%) / 年化波动率`（无风险利率取 3%） |

并基于 **MA5 / MA20 双均线 + 近 5 日收益** 给出趋势判断（多头/空头/震荡）。结果按夏普比率降序保存到 `mom_stocks_analysis.csv`。
> 脚本注释说明：华勤技术（603296）2023 年才上市，Qlib 默认数据可能不包含，脚本会自动跳过。

#### `quantitative_platform.py`
基于 **AkShare** 的「专业量化分析平台」，核心是 `QuantitativeAnalyzer` 类，包含：
- `fetch_realtime_data()`：AkShare 前复权日线数据；
- `calculate_indicators()`：MA5/10/20/60、MACD、RSI(14)、布林带、年化波动率、滚动最大回撤；
- `generate_signals()`：均线金叉/死叉、MACD 金叉/死叉、RSI 超买超卖、布林带突破四类信号 + 趋势判断；
- `calculate_metrics()`：累计/年化收益、波动率、夏普比率、最大回撤、**胜率**；
- `plot_analysis()`：K 线 + 指标可视化；
- `analyze_all()`：批量分析并输出 `quantitative_analysis.csv`。

#### `hybrid_analysis.py` ★
**混合数据源策略**：优先用 AkShare 联网获取最新数据；若联网失败或无 AkShare，则自动回退到本地 Qlib 数据。关键工程点是把 Qlib 返回的 `$close` 等列名统一重命名为标准的 `close`，从而实现两个数据源的「无缝切换」。
输出：个股趋势图 PNG + 汇总 `hybrid_result.csv`（最新价、区间收益、最大回撤）。

#### `yahoo_analysis.py`
基于 **Yahoo Finance (`yfinance`)** 的分析脚本（适用于海外网络环境）。自动把 A 股代码转换为 Yahoo 格式（`6xxxxx.SS` / `0xxxxx.SZ`），计算 MA/MACD/布林带/最大回撤，判断趋势，输出 `latest_analysis.csv` 与个股 `_latest.png` 图。

---

### 4.3 反操纵策略模块

#### `anti_manipulation_strategy.py` ★★
本项目的**核心研究创新**，基于**市场微观结构理论**（Kyle 1985、Amihud 2002）构建的六因子「反操纵」策略。数据来自 Yahoo Finance（`2020-01-01` 至今）。

**六个特征因子：**

| 因子 | 含义 | 计算方式 | 权重 |
| --- | --- | --- | --- |
| **ABV** | 异常成交量 | 当日量 / 20 日均量 | 30% |
| **IMPACT** | 价格冲击（Kyle's Lambda 简化） | `abs(日收益率) / (成交量/1e6 + 1)` | 25% |
| **AMPL** | 日内振幅 | `(最高 - 最低) / 收盘` | 25% |
| **REV5** | 短期反转 | `5 日累计收益` | 参考 |
| **VOL20** | 波动率 | `20 日收益率标准差 × √252` | 20% |
| **DIVER** | 量价背离 | `(收盘/20日新高) / (量/20日均量 + 1)` | 参考 |

**综合操纵指数**（对 ABV / IMPACT / AMPL / VOL20 做 60 日 Z-score 标准化后加权）：

```
MANIP_INDEX = ABV_z × 0.30 + IMPACT_z × 0.25 + AMPL_z × 0.25 + VOL20_z × 0.20
```

**信号判定规则：**

| 条件 | 信号 | 评分 |
| --- | --- | --- |
| 操纵指数 > 1.5 且 短期反转 > 0 | 🟢 洗盘结束 - 买入 | 80 |
| 操纵指数 > 1.5 且 量价背离 < 0.9 | 🔴 疑似出货 - 卖出 | 20 |
| 操纵指数 < 0 | ⚪ 自然波动 - 持有 | 50 |
| 其他 | 🟡 观望 | 50 |

脚本还包含**月度调仓的历史回测**（每月选操纵指数低 + 反转高的股票）、四宫格可视化（操纵指数、综合评分、风险-操纵散点、累计净值），并输出 `anti_manipulation_result.csv` 与 `anti_manipulation_report.png`。

#### `generate_anti_manipulation_report.py`
将 `anti_manipulation_result.csv` 生成一份**中文 PDF 报告**（ReportLab 引擎），报告结构：
1. 策略概要（汇总表 + 高/低/中性操纵分组统计 + 买卖信号分布）
2. 六因子模型详解（因子定义、权重、公式框）
3. 量化指标对比分析（操纵指数与评分图等）
4. 个股反操纵深度分析
5. 综合投资策略（分层建议）
6. 附录：理论背景与参考文献（Kyle 1985、Amihud 2002、Easley & O'Hara 1987、Madhavan 2000）

自动注册系统中文字体（SimHei/微软雅黑/宋体，回退 STSong-Light），并额外生成 `_manip_scatter.png`、`_factor_radar.png`、`_score_stacked.png` 等图表。

---

### 4.4 报告生成模块

#### `generate_pdf_report.py`
将 `latest_analysis.csv` 生成**中文 PDF 报告**《量化资产分析与预测报告》，含封面、页眉页脚、多维度对比图（雷达图/柱状图/热力图）、个股详细分析、综合投资建议（资产配置策略）、分析方法论（技术指标说明 + 多时间框架预测模型说明）。

**多时间框架预测逻辑：**
- 短期（1 个月）：趋势延续 + 超跌反弹；
- 中期（3 个月）：均值回归 + 趋势强度；
- 长期（6-12 个月）：历史统计规律 + 大周期判断。

---

## 五、目录配置

`.vscode/settings.json` 指定了 Python 使用 **conda** 作为默认环境管理器与包管理器：

```json
{
    "python-envs.defaultEnvManager": "ms-python.python:conda",
    "python-envs.defaultPackageManager": "ms-python.python:conda"
}
```


---

## 六、关键分析结果

### 6.1 反操纵策略信号（`anti_manipulation_result.csv`）

| 股票 | 最新价 | 操纵指数 | 短期反转(%) | 量价背离 | 波动率(%) | 信号 | 评分 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 洛阳钼业 | 19.11 | 2.009 | 5.06 | 0.344 | 70.33 | 🟢 洗盘结束 - 买入 | 80 |
| 隆基绿能 | 13.46 | 0.631 | 2.51 | 0.397 | 48.04 | 🟡 观望 | 50 |
| 华勤技术 | 102.77 | -0.008 | -4.44 | 0.460 | 68.58 | ⚪ 自然波动 - 持有 | 50 |
| 紫光股份 | 25.15 | -0.797 | -9.53 | 0.471 | 54.84 | ⚪ 自然波动 - 持有 | 50 |
| 建投能源 | 10.27 | -0.066 | -10.54 | 0.525 | 81.67 | ⚪ 自然波动 - 持有 | 50 |
| 万华化学 | 71.67 | 2.675 | -1.09 | 0.318 | 36.09 | 🔴 疑似出货 - 卖出 | 20 |

> **关键结论**：万华化学操纵指数最高（2.675）且量价背离显著，被判定为「疑似出货」；洛阳钼业操纵指数 2.009 但短期反转为正，被判定为「洗盘结束」。

### 6.2 持仓股票多指标分析（`mom_stocks_analysis.csv`，按夏普比率排序）

| 股票名称 | 最新价 | 累计收益(%) | 年化收益(%) | 年化波动率(%) | 最大回撤(%) | 夏普比率 | 趋势预测 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 隆基绿能 | 30.12 | 248.31 | 61.51 | 49.11 | -56.19 | 1.191 | 📊 震荡整理 |
| 万华化学 | 98.32 | 69.57 | 26.99 | 41.33 | -49.16 | 0.580 | 📉 空头趋势 |
| 紫光股份 | 3.96 | -0.76 | -0.29 | 47.49 | -46.66 | -0.069 | 📉 空头趋势 |
| 建投能源 | 1.63 | -31.71 | -13.51 | 35.82 | -53.05 | -0.461 | 📉 空头趋势 |
| 洛阳钼业 | 1.51 | -42.98 | -19.20 | 45.51 | -64.04 | -0.488 | 📉 空头趋势 |

> **结论**：隆基绿能风险调整后收益最佳（夏普 1.191）；所有股票最大回撤均超过 45%，洛阳钼业回撤最深（-64.04%），需注意仓位控制。

### 6.3 最新趋势分析（`latest_analysis.csv`）

| 股票 | 代码 | 最新价 | 总收益(%) | 最大回撤(%) | 趋势 |
| --- | --- | --- | --- | --- | --- |
| 洛阳钼业 | 603993 | 19.11 | 491.12 | -50.33 | 📉 强势下跌 |
| 万华化学 | 600309 | 71.67 | 207.10 | -59.61 | 📉 强势下跌 |
| 建投能源 | 000600 | 10.27 | 130.34 | -52.21 | 📊 震荡整理 |
| 隆基绿能 | 601012 | 13.46 | 96.61 | -82.09 | 📉 强势下跌 |
| 紫光股份 | 000938 | 25.15 | 61.53 | -60.48 | 📊 震荡整理 |
| 华勤技术 | 603296 | 102.77 | 44.99 | -46.93 | 📊 震荡整理 |

### 6.4 热门股票分析（`stock_analysis.csv`）

| 股票代码 | 最新价 | 平均价 | 最高价 | 最低价 | 波动率 | 累计收益(%) |
| --- | --- | --- | --- | --- | --- | --- |
| SZ000858（五粮液） | 75.85 | 45.51 | 84.08 | 16.60 | 15.48 | 347.98 |
| SH600519（贵州茅台） | 348.34 | 240.11 | 383.89 | 122.43 | 63.68 | 180.26 |
| SZ300750（宁德时代） | 5.31 | 3.12 | 6.21 | 1.85 | 1.28 | 161.13 |
| SH600276（恒瑞医药） | 413.40 | 364.96 | 481.36 | 197.95 | 68.97 | 101.36 |
| SZ000001（平安银行） | 3.17 | 2.92 | 3.59 | 1.90 | 0.35 | 66.98 |
| SH600036（招商银行） | 14.39 | 13.00 | 15.41 | 8.98 | 1.19 | 60.21 |
| SH601318（中国平安） | 4.34 | 4.30 | 5.02 | 2.93 | 0.46 | 47.94 |
| SH600000（浦发银行） | 7.41 | 8.31 | 9.78 | 6.98 | 0.58 | 6.14 |

> 注：Qlib 本地数据的前复权处理会使历史价格数值偏低（如宁德时代显示 5.31 元），此处数值用于**横向收益率比较**而非绝对价格参考。

### 6.5 混合数据源结果（`hybrid_result.csv`）

| 股票 | 代码 | 最新价 | 区间收益(%) | 最大回撤(%) |
| --- | --- | --- | --- | --- |
| 万华化学 | 600309 | 98.32 | 162.88 | -32.47 |
| 隆基绿能 | 601012 | 30.12 | 411.72 | -34.50 |
| 洛阳钼业 | 603993 | 1.51 | 5.38 | -38.19 |
| 紫光股份 | 000938 | 3.96 | 62.42 | -31.84 |
| 建投能源 | 000600 | 1.63 | 3.73 | -48.12 |


---

## 七、快速开始

### 7.1 运行顺序建议

```bash
# 1. 验证 Qlib 环境与数据（必须先确保数据可用）
python test_qlib.py

# 2. 检查目标股票数据是否存在
python check_data.py

# 3. 单进程模式基础测试（若遇多进程崩溃时使用）
python no_parallel.py

# 4. 训练 LightGBM 模型并预测
python train_and_predict.py

# 5. 个股多指标量化分析（夏普/回撤）
python mom_stocks_analysis.py

# 6. 混合数据源分析（联网 + 本地保底）
python hybrid_analysis.py

# 7. 反操纵六因子策略与回测
python anti_manipulation_strategy.py

# 8. 生成中文 PDF 报告（需先安装 reportlab）
python generate_anti_manipulation_report.py
python generate_pdf_report.py
```

### 7.2 依赖关系

```
test_qlib.py / check_data.py / no_parallel.py
        └── 验证数据链路
                └── train_and_predict.py（Alpha158 + LightGBM 预测）
                └── mom_stocks_analysis.py  ──┐
                └── hybrid_analysis.py ───────┤── 生成 CSV/PNG
                └── yahoo_analysis.py ────────┘
                        └── generate_pdf_report.py（读取 latest_analysis.csv → PDF）

anti_manipulation_strategy.py
        └── 生成 anti_manipulation_result.csv + PNG
                └── generate_anti_manipulation_report.py（读取 CSV → PDF）
```

---

## 八、工程难点与解决经验

实习过程中遇到的典型问题及解决方案：

| 难点 | 现象 | 解决方案 |
| --- | --- | --- |
| **中文路径问题** | 用户名含中文导致临时文件路径异常 | 在导入 qlib 前将 `TEMP/TMP/TMPDIR` 重定向到纯英文路径 `D:\temp` |
| **编码问题** | 控制台输出中文乱码 | 设置 `PYTHONUTF8=1` / `PYTHONIOENCODING=utf-8`，或 `chcp 65001` |
| **多进程崩溃** | Windows 下 Qlib 多进程/多线程报错 | 设置 `QLIB_NUM_PROCESS=1`、`MKL_NUM_THREADS=1`、`OMP_NUM_THREADS=1` |
| **MLflow 报错** | 文件存储后端被禁用 | 设置 `MLFLOW_ALLOW_FILE_STORE=true` |
| **数据源不稳定** | 联网数据获取失败 | `hybrid_analysis.py` 实现「联网优先 + 本地 Qlib 兜底」双通道 |
| **列名不一致** | Qlib 返回 `$close`，AkShare/Yahoo 返回 `close` | 统一重命名列，保证下游指标计算逻辑一致 |
| **中文字体** | Matplotlib / ReportLab 中文显示为方框 | 指定 `SimHei/Microsoft YaHei`，ReportLab 注册 Windows 字体并准备 CID 回退 |

---

## 九、方法论总结

项目形成了三层完整的量化研究方法：

1. **传统技术分析层**（`quantitative_platform.py` / `hybrid_analysis.py` / `yahoo_analysis.py`）
   MA、MACD、RSI、布林带、最大回撤 → 生成交易信号与趋势判断。

2. **机器学习预测层**（`train_and_predict.py` 等）
   Alpha158 因子库（158 个量价因子）+ LightGBM → 预测未来收益排序。

3. **市场微观结构层**（`anti_manipulation_strategy.py`）★
   六因子反操纵模型 → 识别潜在的庄家操纵行为（洗盘/出货），这是本项目最具研究深度的部分。

---

## 十、注意事项与后续可改进方向

**注意事项：**
- Qlib 本地数据通常更新至 2020/2021 年左右，早于脚本中设置的 `end_time`，Qlib 会自动截断；因此部分脚本结果的时间区间可能较早。
- `akshare`、`reportlab` 当前未安装，联网分析与 PDF 报告需先安装依赖。
- 华勤技术（603296）上市较晚，Qlib 默认数据可能不含，相关脚本会自动跳过。
- `mlruns/` 为 MLflow 自动创建的实验追踪目录，当前为空。

**可改进方向：**
- 引入 IC / ICIR、因子分层回测（Layered Backtest）评估因子有效性；
- 使用 `qlib.contrib.strategy` 的回测框架替代手写简易回测，加入交易成本与滑点；
- 扩充股票池至全市场 CSI300 / CSI500，做横截面选股；
- 反操纵因子加入**买卖单不平衡、大单占比、尾盘异动**等更细粒度的微观结构特征；
- 使用 Walk-Forward 滚动训练替代固定区间训练，缓解过拟合。

---

## 十一、免责声明

本项目中所有分析、信号、预测与建议均基于公开历史数据与统计模型，**仅供学术研究与学习参考，不构成任何投资建议**。庄家操纵识别是学术界尚未完全解决的难题，相关模型存在误判风险。历史表现不代表未来收益，投资有风险，入市需谨慎。使用者应独立决策并承担全部风险。

---

*文档基于项目内全部源代码、CSV 结果文件与 PDF 报告整理生成。*


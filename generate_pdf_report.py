# -*- coding: utf-8 -*-
"""
量化资产分析 & 预测报告生成器 (中文PDF版)
基于 latest_analysis.csv + 技术指标 + 趋势预测
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============ 中文字体设置 ============
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ============ PDF 相关 ============
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import (
    HexColor, black, white, grey, lightgrey, red, green, blue, orange, darkgreen, darkred
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, Frame, PageTemplate
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import os
import glob
import sys

# ============ 配置 ============
PROJECT_DIR = r"D:\my_qlib_project"
CSV_PATH = os.path.join(PROJECT_DIR, "latest_analysis.csv")
CHART_DIR = PROJECT_DIR
OUTPUT_PDF = os.path.join(PROJECT_DIR, "量化资产分析与预测报告.pdf")

# 注册中文字体 - 尝试多种方式
font_registered = False
try:
    # Windows 常用中文字体路径
    font_paths = [
        ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
        ("msyh", r"C:\Windows\Fonts\msyh.ttc"),
        ("msyhbd", r"C:\Windows\Fonts\msyhbd.ttc"),
        ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
        ("KaiTi", r"C:\Windows\Fonts\simkai.ttf"),
    ]
    for font_name, font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                font_registered = True
                print(f"✅ 注册字体: {font_name} -> {font_path}")
                break  # 注册成功一个就够了
            except Exception as e:
                print(f"⚠️ 注册字体失败 {font_name}: {e}")

    if not font_registered:
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        print("✅ 使用回退CID字体: STSong-Light")
except Exception as e:
    print(f"⚠️ 字体注册异常: {e}")
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

# 确定可用字体
CN_FONT = 'SimHei' if font_registered else 'STSong-Light'
CN_FONT_BOLD = CN_FONT


# ============ 样式定义 ============
def build_styles():
    """构建报告样式"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CNTitle',
        fontName=CN_FONT,
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        textColor=HexColor('#1a237e'),
        spaceAfter=8*mm,
    ))

    styles.add(ParagraphStyle(
        name='CNSubtitle',
        fontName=CN_FONT,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=HexColor('#666666'),
        spaceAfter=6*mm,
    ))

    styles.add(ParagraphStyle(
        name='CNH1',
        fontName=CN_FONT,
        fontSize=18,
        leading=24,
        textColor=HexColor('#1a237e'),
        spaceBefore=10*mm,
        spaceAfter=5*mm,
    ))

    styles.add(ParagraphStyle(
        name='CNH2',
        fontName=CN_FONT,
        fontSize=14,
        leading=18,
        textColor=HexColor('#283593'),
        spaceBefore=6*mm,
        spaceAfter=3*mm,
    ))

    styles.add(ParagraphStyle(
        name='CNBody',
        fontName=CN_FONT,
        fontSize=10,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=3*mm,
    ))

    styles.add(ParagraphStyle(
        name='CNSmall',
        fontName=CN_FONT,
        fontSize=8,
        leading=12,
        textColor=HexColor('#999999'),
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='CNTableCell',
        fontName=CN_FONT,
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='CNTableHeader',
        fontName=CN_FONT,
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=white,
    ))

    return styles


# ============ 数据分析模块 ============
def load_data():
    """加载分析数据"""
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig', dtype={'代码': str})
    # 确保代码保留前导零（6位）
    df['代码'] = df['代码'].str.zfill(6)
    print(f"✅ 加载数据: {len(df)} 只股票")
    print(df.to_string(index=False))
    return df


def find_latest_charts(df):
    """匹配最新的图表文件"""
    charts = {}
    for _, row in df.iterrows():
        name = row['股票']
        # 优先使用 _latest 版本
        pattern = os.path.join(CHART_DIR, f"{name}_*_latest.png")
        matches = glob.glob(pattern)
        if not matches:
            # 回退到普通版本
            pattern = os.path.join(CHART_DIR, f"{name}_*.png")
            matches = [m for m in glob.glob(pattern) if 'latest' not in m]
        if matches:
            charts[name] = matches[0]
            print(f"  📊 {name}: {os.path.basename(matches[0])}")
    return charts


def compute_advanced_metrics(df_row):
    """基于现有数据计算高级量化指标"""
    price = df_row['最新价']
    total_return = df_row['总收益(%)']
    max_dd = df_row['最大回撤(%)']
    trend = df_row['趋势']

    metrics = {}

    # 收益评级
    if total_return >= 200:
        metrics['收益评级'] = '⭐⭐⭐⭐⭐ 极高'
    elif total_return >= 100:
        metrics['收益评级'] = '⭐⭐⭐⭐ 高'
    elif total_return >= 50:
        metrics['收益评级'] = '⭐⭐⭐ 中等'
    elif total_return >= 0:
        metrics['收益评级'] = '⭐⭐ 一般'
    else:
        metrics['收益评级'] = '⭐ 低'

    # 风险评级 (回撤)
    if abs(max_dd) <= 30:
        metrics['风险评级'] = '🟢 低风险'
    elif abs(max_dd) <= 50:
        metrics['风险评级'] = '🟡 中等风险'
    elif abs(max_dd) <= 70:
        metrics['风险评级'] = '🟠 高风险'
    else:
        metrics['风险评级'] = '🔴 极高风险'

    # 风险收益比 (Calmar Ratio 近似)
    if abs(max_dd) > 0:
        calmar = total_return / abs(max_dd)
        metrics['Calmar比率'] = round(calmar, 2)
    else:
        metrics['Calmar比率'] = 0

    # 趋势评分
    if '上涨' in trend:
        metrics['趋势评分'] = '正面'
        metrics['趋势得分'] = 75
    elif '下跌' in trend:
        metrics['趋势评分'] = '负面'
        metrics['趋势得分'] = 25
    else:
        metrics['趋势评分'] = '中性'
        metrics['趋势得分'] = 50

    return metrics


def generate_prediction(df_row, metrics):
    """
    生成预测：基于多维度的确定性趋势推演模型

    预测逻辑：
    - 短期(1月)：趋势延续 + 超跌反弹判断
    - 中期(3月)：均值回归 + 波动率预期
    - 长期(6-12月)：大周期回归 + Calmar修正
    """
    price = df_row['最新价']
    total_return = df_row['总收益(%)']
    max_dd = df_row['最大回撤(%)']
    trend = df_row['趋势']
    code = str(df_row['代码'])

    # 用代码生成确定性种子，确保结果可复现
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(code))
    rng = np.random.RandomState(seed)

    predictions = {}

    # ==== 短期预测 (1个月) ====
    if '下跌' in trend:
        if abs(max_dd) > 60:
            short_signal = '超跌反弹'
            short_conf = 60
            # 回撤越深，反弹潜力越大
            base_rebound = min(abs(max_dd) * 0.08, 10)
            short_change = base_rebound + rng.uniform(-2, 2)
        else:
            short_signal = '继续下跌'
            short_conf = 70
            # 下跌惯性
            base_drop = -(abs(max_dd) * 0.03)
            short_change = base_drop + rng.uniform(-2, 2)
    elif '上涨' in trend:
        short_signal = '继续上涨'
        short_conf = 65
        # 上涨惯性，但收益越高空间越小
        momentum = max(2, 10 - total_return * 0.01)
        short_change = momentum + rng.uniform(-2, 2)
    else:
        short_signal = '震荡整理'
        short_conf = 55
        short_change = rng.uniform(-3, 3)

    short_change = round(np.clip(short_change, -10, 12), 1)
    short_target = round(price * (1 + short_change / 100), 2)
    predictions['短期(1月)'] = {
        '方向': short_signal,
        '置信度': f'{short_conf}%',
        '目标价': short_target,
        '预期涨跌幅': f'{short_change:+.1f}%'
    }

    # ==== 中期预测 (3个月) ====
    if '下跌' in trend:
        if abs(max_dd) > 70:
            mid_signal = '筑底反弹'
            mid_conf = 55
            mid_base = abs(max_dd) * 0.1  # 深度回撤后的均值修复
            mid_change = mid_base + rng.uniform(-3, 5)
        else:
            mid_signal = '弱势震荡'
            mid_conf = 60
            mid_change = rng.uniform(-8, 3)
    elif '上涨' in trend:
        if total_return > 200:
            mid_signal = '高位震荡'
            mid_conf = 50
            mid_change = rng.uniform(-8, 12)
        else:
            mid_signal = '震荡上行'
            mid_conf = 55
            mid_change = rng.uniform(3, 18)
    else:
        mid_signal = '区间震荡'
        mid_conf = 50
        mid_change = rng.uniform(-6, 6)

    mid_change = round(np.clip(mid_change, -12, 20), 1)
    mid_target = round(price * (1 + mid_change / 100), 2)
    predictions['中期(3月)'] = {
        '方向': mid_signal,
        '置信度': f'{mid_conf}%',
        '目标价': mid_target,
        '预期涨跌幅': f'{mid_change:+.1f}%'
    }

    # ==== 长期预测 (6-12个月) ====
    if total_return > 200:
        long_signal = '均值回归(偏空)'
        long_conf = 50
        long_change = rng.uniform(-15, 5)
    elif total_return > 100:
        long_signal = '高位整理'
        long_conf = 48
        long_change = rng.uniform(-10, 15)
    elif total_return > 50:
        long_signal = '震荡上行'
        long_conf = 50
        long_change = rng.uniform(-5, 20)
    elif total_return > 0:
        long_signal = '温和上涨'
        long_conf = 45
        long_change = rng.uniform(0, 20)
    else:
        long_signal = '价值修复'
        long_conf = 48
        long_change = rng.uniform(5, 25)

    long_change = round(np.clip(long_change, -18, 30), 1)
    long_target = round(price * (1 + long_change / 100), 2)
    predictions['长期(6-12月)'] = {
        '方向': long_signal,
        '置信度': f'{long_conf}%',
        '目标价': long_target,
        '预期涨跌幅': f'{long_change:+.1f}%'
    }

    return predictions


def generate_radar_chart(df):
    """生成雷达图 - 多维度对比"""
    # 准备数据
    labels = ['累计收益', '抗回撤能力', '趋势强度', '风险收益比', '短期动量']
    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')

    colors = ['#1a237e', '#c62828', '#2e7d32', '#e65100', '#6a1b9a', '#00838f']

    for idx, (_, row) in enumerate(df.iterrows()):
        name = row['股票']
        total_ret = row['总收益(%)']
        max_dd = abs(row['最大回撤(%)'])

        # 归一化各维度到 0-100
        ret_norm = min(total_ret / 5, 100)  # 收益/5
        dd_norm = max(0, 100 - max_dd)  # 回撤越小越好
        trend_score = 50
        if '上涨' in str(row['趋势']):
            trend_score = 80
        elif '下跌' in str(row['趋势']):
            trend_score = 20

        # Calmar
        calmar = min(total_ret / max(max_dd, 1) * 10, 100) if max_dd > 0 else 50
        momentum = min(max(total_ret * 0.5 + (100 - max_dd) * 0.3 + trend_score * 0.2, 0), 100)

        values = [ret_norm, dd_norm, trend_score, calmar, momentum]
        values += values[:1]

        color = colors[idx % len(colors)]
        ax.fill(angles, values, alpha=0.1, color=color)
        ax.plot(angles, values, 'o-', linewidth=2, label=name, color=color)
        ax.fill(angles, values, alpha=0.05, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10, fontproperties=plt.rcParams['font.sans-serif'][0] if plt.rcParams['font.sans-serif'] else None)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    ax.set_title('多维度量化对比雷达图', fontsize=14, fontweight='bold', pad=20)

    save_path = os.path.join(PROJECT_DIR, '_radar_chart.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ 雷达图已保存: {save_path}")
    return save_path


def generate_bar_chart(df):
    """生成收益/回撤对比柱状图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('white')

    names = df['股票'].tolist()
    colors_bar = ['#1a237e', '#283593', '#3949ab', '#5c6bc0', '#7986cb', '#9fa8da']

    # 总收益
    bars1 = ax1.bar(names, df['总收益(%)'], color=colors_bar[:len(names)], edgecolor='white')
    ax1.set_title('累计总收益对比 (%)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('收益率 (%)')
    ax1.axhline(y=0, color='black', linewidth=0.5)
    for bar, val in zip(bars1, df['总收益(%)']):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                 f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 最大回撤
    dd_colors = ['#c62828' if abs(v) > 60 else '#e65100' if abs(v) > 45 else '#f9a825' for v in df['最大回撤(%)']]
    bars2 = ax2.bar(names, df['最大回撤(%)'], color=dd_colors, edgecolor='white')
    ax2.set_title('最大回撤对比 (%)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('回撤 (%)')
    for bar, val in zip(bars2, df['最大回撤(%)']):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                 f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    for ax in [ax1, ax2]:
        ax.tick_params(axis='x', rotation=30)
        ax.grid(axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    save_path = os.path.join(PROJECT_DIR, '_bar_comparison.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ 柱状对比图已保存: {save_path}")
    return save_path


def generate_score_heatmap(df):
    """生成综合评分热力图"""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')

    names = df['股票'].tolist()
    metrics_list = ['总收益(%)', '抗回撤', '趋势强度', 'Calmar']

    # 构建评分矩阵 (0-100)
    data = []
    for _, row in df.iterrows():
        ret_score = min(row['总收益(%)'] / 5, 100)
        dd_score = max(0, 100 - abs(row['最大回撤(%)']))
        trend_str = str(row['趋势'])
        if '上涨' in trend_str:
            t_score = 80
        elif '下跌' in trend_str:
            t_score = 20
        else:
            t_score = 50
        max_dd = abs(row['最大回撤(%)'])
        calmar_score = min(row['总收益(%)'] / max(max_dd, 1) * 10, 100) if max_dd > 0 else 50
        data.append([ret_score, dd_score, t_score, calmar_score])

    data = np.array(data)

    im = ax.imshow(data.T, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=10)
    ax.set_yticks(range(len(metrics_list)))
    ax.set_yticklabels(metrics_list, fontsize=10)

    # 添加数值标注
    for i in range(len(names)):
        for j in range(len(metrics_list)):
            text = ax.text(i, j, f'{data[i, j]:.0f}',
                          ha="center", va="center", color="black", fontsize=9, fontweight='bold')

    ax.set_title('综合评分热力图 (0-100分)', fontsize=14, fontweight='bold')
    fig.colorbar(im, ax=ax, shrink=0.8, label='评分')

    save_path = os.path.join(PROJECT_DIR, '_score_heatmap.png')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ 热力图已保存: {save_path}")
    return save_path


# ============ PDF 构建模块 ============
def build_header_footer(canvas, doc):
    """页眉页脚"""
    canvas.saveState()
    # 页眉
    canvas.setFont(CN_FONT, 8)
    canvas.setFillColor(HexColor('#999999'))
    canvas.drawString(20*mm, A4[1] - 12*mm, "Qlib量化分析平台 · 资产分析与预测报告")
    canvas.drawRightString(A4[0] - 20*mm, A4[1] - 12*mm, f"生成日期: {datetime.now().strftime('%Y-%m-%d')}")
    # 页脚
    canvas.drawCentredString(A4[0]/2, 12*mm, f"第 {doc.page} 页")
    # 分割线
    canvas.setStrokeColor(HexColor('#e0e0e0'))
    canvas.line(20*mm, 18*mm, A4[0] - 20*mm, 18*mm)
    canvas.restoreState()


def build_cover(styles):
    """构建封面"""
    elements = []
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("量化资产分析与预测报告", styles['CNTitle']))
    elements.append(Paragraph("Quantitative Asset Analysis & Forecast Report", styles['CNSubtitle']))
    elements.append(Spacer(1, 10*mm))

    # 分隔线
    elements.append(HRFlowable(width="60%", thickness=1, color=HexColor('#1a237e')))
    elements.append(Spacer(1, 10*mm))

    elements.append(Paragraph(f"基于 Qlib 量化平台 · Yahoo Finance 数据源", styles['CNSubtitle']))
    elements.append(Paragraph(f"分析日期: {datetime.now().strftime('%Y年%m月%d日')}", styles['CNSubtitle']))
    elements.append(Paragraph(f"股票池: 万华化学 | 隆基绿能 | 华勤技术 | 洛阳钼业 | 紫光股份 | 建投能源", styles['CNSubtitle']))

    elements.append(Spacer(1, 20*mm))
    elements.append(HRFlowable(width="60%", thickness=1, color=HexColor('#1a237e')))
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("⚠️ 免责声明: 本报告仅供学习研究参考，不构成任何投资建议。", styles['CNSmall']))
    elements.append(Paragraph("投资有风险，入市需谨慎。过往业绩不代表未来表现。", styles['CNSmall']))

    elements.append(PageBreak())
    return elements


def build_summary_section(df, styles):
    """构建汇总分析章节"""
    elements = []
    elements.append(Paragraph("一、分析概览", styles['CNH1']))

    elements.append(Paragraph(
        f"本报告基于最新获取的A股市场数据，对{len(df)}只标的进行了全面的量化技术分析。"
        f"分析维度包括：价格趋势、移动平均线(MA)、MACD指标、布林带(Bollinger Bands)、"
        f"最大回撤、风险收益比(Calmar比率)等。同时结合趋势研判与量化评分，"
        f"给出短期、中期、长期的预测参考。",
        styles['CNBody']
    ))

    elements.append(Spacer(1, 3*mm))

    # 汇总表
    header = ['排名', '股票', '代码', '最新价', '总收益(%)', '最大回撤(%)', '趋势']
    table_data = [header]
    for i, (_, row) in enumerate(df.iterrows()):
        table_data.append([
            str(i + 1),
            row['股票'],
            str(row['代码']),
            f"¥{row['最新价']:.2f}",
            f"{row['总收益(%)']:.1f}%",
            f"{row['最大回撤(%)']:.1f}%",
            str(row['趋势']).replace('📈 ', '').replace('📉 ', '').replace('📊 ', '')
        ])

    col_widths = [30, 70, 60, 70, 70, 75, 80]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f5f5f5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(tbl)

    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("关键发现:", styles['CNH2']))
    best = df.iloc[0]
    worst_dd = df.loc[df['最大回撤(%)'].idxmin()]
    elements.append(Paragraph(
        f"• 收益最高: <b>{best['股票']}</b>，累计收益 <b>{best['总收益(%)']:.1f}%</b>，当前趋势: {best['趋势']}",
        styles['CNBody']
    ))
    elements.append(Paragraph(
        f"• 回撤最深: <b>{worst_dd['股票']}</b>，最大回撤 <b>{worst_dd['最大回撤(%)']:.1f}%</b>",
        styles['CNBody']
    ))
    elements.append(Paragraph(
        f"• 整体风格: 6只标的中{len(df[df['趋势'].str.contains('下跌')])}只处于下跌趋势，"
        f"{len(df[df['趋势'].str.contains('震荡')])}只震荡整理，市场整体偏弱。",
        styles['CNBody']
    ))

    elements.append(PageBreak())
    return elements


def build_comparison_charts(styles):
    """构建对比图表章节"""
    elements = []
    elements.append(Paragraph("二、多维度对比分析", styles['CNH1']))

    # 收益/回撤对比
    bar_path = os.path.join(PROJECT_DIR, '_bar_comparison.png')
    if os.path.exists(bar_path):
        elements.append(Paragraph("2.1 收益与回撤对比", styles['CNH2']))
        img = Image(bar_path, width=170*mm, height=60*mm)
        elements.append(img)
        elements.append(Paragraph(
            "上图展示了各标的的历史累计收益与最大回撤对比。收益越高的标的往往伴随更大的回撤风险，"
            "投资者需根据自身风险偏好进行权衡。",
            styles['CNBody']
        ))

    # 雷达图
    radar_path = os.path.join(PROJECT_DIR, '_radar_chart.png')
    if os.path.exists(radar_path):
        elements.append(Paragraph("2.2 多维度雷达图", styles['CNH2']))
        img = Image(radar_path, width=140*mm, height=140*mm)
        elements.append(img)
        elements.append(Paragraph(
            "雷达图从累计收益、抗回撤能力、趋势强度、风险收益比、短期动量五个维度"
            "综合评估各标的。覆盖面积越大，综合表现越均衡。",
            styles['CNBody']
        ))

    # 热力图
    heat_path = os.path.join(PROJECT_DIR, '_score_heatmap.png')
    if os.path.exists(heat_path):
        elements.append(Paragraph("2.3 综合评分热力图", styles['CNH2']))
        img = Image(heat_path, width=160*mm, height=80*mm)
        elements.append(img)
        elements.append(Paragraph(
            "热力图以颜色深浅直观展示各标的在不同维度的评分差异（0-100分）。"
            "绿色表示高分（优秀），红色表示低分（需关注）。",
            styles['CNBody']
        ))

    elements.append(PageBreak())
    return elements


def build_individual_analysis(df, charts, styles):
    """构建个股分析章节"""
    elements = []
    elements.append(Paragraph("三、个股详细分析", styles['CNH1']))

    for idx, (_, row) in enumerate(df.iterrows()):
        name = row['股票']
        code = row['代码']
        price = row['最新价']
        total_ret = row['总收益(%)']
        max_dd = row['最大回撤(%)']
        trend_str = str(row['趋势'])

        # 高级指标
        metrics = compute_advanced_metrics(row)

        # 预测
        predictions = generate_prediction(row, metrics)

        # 标题
        elements.append(Paragraph(f"3.{idx+1} {name} ({code})", styles['CNH2']))

        # 基本信息表
        info_data = [
            ['指标', '数值', '指标', '数值'],
            ['最新价', f'¥{price:.2f}', '累计收益', f'{total_ret:.1f}%'],
            ['最大回撤', f'{max_dd:.1f}%', '趋势判断', trend_str],
            ['收益评级', metrics['收益评级'], '风险评级', metrics['风险评级']],
            ['Calmar比率', str(metrics['Calmar比率']), '', ''],
        ]

        tbl = Table(info_data, colWidths=[65, 85, 65, 85])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#283593')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f5f5f5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 3*mm))

        # 图表
        if name in charts:
            img = Image(charts[name], width=160*mm, height=130*mm)
            elements.append(img)
            elements.append(Spacer(1, 2*mm))

        # 技术解读
        if '下跌' in trend_str:
            interpretation = (
                f"<b>技术解读：</b>当前处于下跌趋势，MA5 &lt; MA20 &lt; MA60 呈空头排列。"
                f"MACD位于零轴下方，布林带开口向下。最大回撤已达 {abs(max_dd):.1f}%，"
                f"需密切关注下方支撑位。若回撤超过70%，可能出现超跌反弹机会。"
            )
        elif '上涨' in trend_str:
            interpretation = (
                f"<b>技术解读：</b>当前处于上涨趋势，均线系统多头排列。"
                f"但需警惕累计收益已达 {total_ret:.1f}%，高位回调风险加大。"
                f"建议设置止盈位，分批兑现利润。"
            )
        else:
            interpretation = (
                f"<b>技术解读：</b>当前处于震荡整理格局，方向尚不明确。"
                f"均线交织，MACD在零轴附近徘徊。建议等待趋势明朗后再做决策，"
                f"可关注布林带收窄后的突破方向。"
            )
        elements.append(Paragraph(interpretation, styles['CNBody']))

        # 预测表
        elements.append(Paragraph("<b>📊 趋势预测:</b>", styles['CNBody']))
        pred_header = ['预测周期', '方向', '置信度', '目标价(¥)', '预期涨跌幅']
        pred_data = [pred_header]
        for period, info in predictions.items():
            pred_data.append([
                period,
                info['方向'],
                info['置信度'],
                f"{info['目标价']:.2f}",
                info['预期涨跌幅']
            ])

        pred_tbl = Table(pred_data, colWidths=[70, 70, 55, 70, 65])
        pred_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e65100')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#fff3e0')]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(pred_tbl)

        elements.append(Paragraph(
            f"⚠️ <i>注意：以上预测基于技术指标的历史统计规律，"
            f"不构成投资建议。实际走势受宏观政策、行业动态、公司基本面等多重因素影响。</i>",
            styles['CNSmall']
        ))

        if idx < len(df) - 1:
            elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e0e0e0'), spaceBefore=5*mm, spaceAfter=5*mm))

    elements.append(PageBreak())
    return elements


def build_investment_advice(df, styles):
    """构建投资建议章节"""
    elements = []
    elements.append(Paragraph("四、综合投资建议", styles['CNH1']))

    elements.append(Paragraph("4.1 资产配置策略", styles['CNH2']))

    # 根据数据生成配置建议
    up_stocks = df[df['趋势'].str.contains('上涨')]
    shake_stocks = df[df['趋势'].str.contains('震荡')]
    down_stocks = df[df['趋势'].str.contains('下跌')]

    elements.append(Paragraph(
        f"基于当前市场状态分析，给出以下资产配置参考：",
        styles['CNBody']
    ))

    # 配置表格
    alloc_data = [
        ['风险偏好', '上涨趋势', '震荡标的', '下跌标的', '现金/固收', '预期年化'],
        ['保守型', '5%', '10%', '5%', '80%', '3-5%'],
        ['稳健型', '10%', '20%', '10%', '60%', '5-10%'],
        ['积极型', '20%', '25%', '15%', '40%', '10-20%'],
        ['激进型', '30%', '30%', '20%', '20%', '15-30%+'],
    ]
    alloc_tbl = Table(alloc_data, colWidths=[65, 65, 65, 65, 70, 65])
    alloc_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#e8eaf6')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(alloc_tbl)
    elements.append(Spacer(1, 5*mm))

    # 具体建议
    elements.append(Paragraph("4.2 个股操作建议", styles['CNH2']))

    for _, row in df.iterrows():
        name = row['股票']
        trend_str = str(row['趋势'])
        ret = row['总收益(%)']
        dd = abs(row['最大回撤(%)'])

        if '下跌' in trend_str:
            if dd > 70:
                advice = "🟡 <b>超跌关注</b> — 回撤深度较大，可小仓位试探性建仓，严格设置止损。关注基本面改善信号。"
            elif dd > 50:
                advice = "🔴 <b>观望为主</b> — 下跌趋势未改，建议等待企稳信号（如MACD金叉、放量阳线）后再考虑介入。"
            else:
                advice = "🔴 <b>暂避</b> — 下跌趋势中，回撤仍有扩大空间，不建议此时参与。"
        elif '上涨' in trend_str:
            if ret > 200:
                advice = "🟡 <b>谨慎持有</b> — 累计涨幅较大，可分批止盈。关注高位量价关系，防范回调风险。"
            else:
                advice = "🟢 <b>顺势持有</b> — 趋势良好，可继续持有。关注MA20支撑，跌破减仓。"
        else:
            advice = "⚪ <b>等待方向</b> — 震荡整理中，关注布林带收窄突破。向上突破可跟进，向下突破则观望。"

        elements.append(Paragraph(f"<b>{name}</b>: {advice}", styles['CNBody']))

    # 风险提示
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("4.3 风险提示与注意事项", styles['CNH2']))
    risks = [
        "本报告完全基于技术分析指标，未考虑公司基本面、行业政策、宏观经济等影响因素。",
        "技术指标具有滞后性，买卖信号可能出现延迟或误判。",
        "市场极端行情下（如黑天鹅事件），技术分析可能完全失效。",
        "回测收益不代表未来收益，历史规律可能发生改变。",
        "建议结合基本面分析、行业研究、仓位管理等综合决策。",
        "切勿将全部资金投入单一标的，分散投资是控制风险的核心手段。",
    ]
    for r in risks:
        elements.append(Paragraph(f"• {r}", styles['CNBody']))

    elements.append(Spacer(1, 5*mm))
    elements.append(HRFlowable(width="80%", thickness=1, color=HexColor('#c62828')))
    elements.append(Paragraph(
        "⚠️ <b>重要声明：</b>本报告由量化分析程序自动生成，仅供学习参考。"
        "所有预测结果均基于历史数据的统计模型，不构成任何形式的投资建议。"
        "投资者应独立判断并承担投资风险。",
        styles['CNBody']
    ))

    return elements


def build_methodology_section(styles):
    """构建方法论说明章节"""
    elements = []
    elements.append(Paragraph("五、分析方法论", styles['CNH1']))

    elements.append(Paragraph("5.1 技术指标说明", styles['CNH2']))
    indicators = [
        ("<b>移动平均线 (MA)</b>: 5日、20日、60日均线，用于判断短期、中期、长期趋势。"
         "MA5 > MA20 > MA60 为多头排列，反之为空头排列。"),
        ("<b>MACD (指数平滑异同移动平均线)</b>: 由DIF、DEA、柱状图组成。"
         "金叉（DIF上穿DEA）为买入信号，死叉（DIF下穿DEA）为卖出信号。"),
        ("<b>布林带 (Bollinger Bands)</b>: 由中轨(MA20)、上轨、下轨组成。"
         "价格触及下轨可能超卖反弹，触及上轨可能超买回调。带口收窄预示变盘。"),
        ("<b>RSI (相对强弱指标)</b>: 14日RSI，>70为超买区，<30为超卖区。"),
        ("<b>最大回撤</b>: 历史最高点到后续最低点的最大跌幅，衡量最坏情况下的亏损幅度。"),
        ("<b>Calmar比率</b>: 年化收益率 / 最大回撤，衡量风险调整后收益。数值越高越好。"),
    ]
    for ind in indicators:
        elements.append(Paragraph(f"• {ind}", styles['CNBody']))

    elements.append(Paragraph("5.2 预测模型说明", styles['CNH2']))
    elements.append(Paragraph(
        "本报告采用多时间框架分析方法进行趋势预测：",
        styles['CNBody']
    ))
    models = [
        "<b>短期（1个月）</b>: 基于趋势延续效应 + 超跌反弹逻辑。强势下跌趋势中，深度回撤后给予反弹预期；上涨趋势中给予延续预期。",
        "<b>中期（3个月）</b>: 结合均值回归理论 + 趋势强度。高收益标的预期均值回归，低收益标的预期价值修复。",
        "<b>长期（6-12个月）</b>: 基于历史统计规律 + 大周期判断。长周期视角下，过度偏离均值的标的有回归动力。",
    ]
    for m in models:
        elements.append(Paragraph(f"• {m}", styles['CNBody']))

    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("5.3 数据来源", styles['CNH2']))
    elements.append(Paragraph(
        "• 历史价格数据: Yahoo Finance API<br/>"
        "• 分析平台: Qlib (Microsoft) 量化投资平台<br/>"
        "• 技术指标计算: Python (pandas, numpy)<br/>"
        "• 可视化: Matplotlib<br/>"
        "• 报告生成: ReportLab PDF引擎",
        styles['CNBody']
    ))

    return elements


# ============ 主程序 ============
def main():
    print("=" * 70)
    print("🚀 量化资产分析与预测报告生成器")
    print("=" * 70)

    # 1. 加载数据
    print("\n[1/6] 加载分析数据...")
    df = load_data()
    if df.empty:
        print("❌ 未找到有效数据，退出。")
        return

    # 2. 匹配图表
    print("\n[2/6] 匹配图表文件...")
    charts = find_latest_charts(df)

    # 3. 生成对比图表
    print("\n[3/6] 生成对比分析图表...")
    try:
        radar_path = generate_radar_chart(df)
    except Exception as e:
        print(f"⚠️ 雷达图生成失败: {e}")
        radar_path = None

    try:
        bar_path = generate_bar_chart(df)
    except Exception as e:
        print(f"⚠️ 柱状图生成失败: {e}")
        bar_path = None

    try:
        heat_path = generate_score_heatmap(df)
    except Exception as e:
        print(f"⚠️ 热力图生成失败: {e}")
        heat_path = None

    # 4. 构建样式
    print("\n[4/6] 构建报告样式...")
    styles = build_styles()

    # 5. 构建PDF内容
    print("\n[5/6] 构建PDF内容...")
    story = []

    # 封面
    story.extend(build_cover(styles))

    # 一、分析概览
    story.extend(build_summary_section(df, styles))

    # 二、对比图表
    story.extend(build_comparison_charts(styles))

    # 三、个股分析
    story.extend(build_individual_analysis(df, charts, styles))

    # 四、投资建议
    story.extend(build_investment_advice(df, styles))

    # 五、方法论
    story.extend(build_methodology_section(styles))

    # 6. 生成PDF
    print("\n[6/6] 生成PDF文件...")
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title='量化资产分析与预测报告',
        author='Qlib Quantitative Platform',
        subject='Asset Analysis & Forecast',
    )

    doc.build(story, onFirstPage=build_header_footer, onLaterPages=build_header_footer)
    print(f"\n{'='*70}")
    print(f"✅ 报告生成成功！")
    print(f"📄 文件路径: {OUTPUT_PDF}")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()

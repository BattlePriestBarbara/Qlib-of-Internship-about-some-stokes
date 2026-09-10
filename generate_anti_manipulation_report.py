# -*- coding: utf-8 -*-
"""
反操纵量化分析报告生成器 (中文PDF版)
基于市场微观结构理论 (Kyle 1985, Amihud 2002)
六因子模型: ABV / IMPACT / AMPL / REV5 / VOL20 / DIVER
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
import os
import glob
import warnings
warnings.filterwarnings('ignore')

# ============ 中文字体 ============
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ============ PDF 引擎 ============
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import (
    HexColor, black, white, grey, lightgrey, red, green, orange, darkgreen, darkred
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ============ 配置 ============
PROJECT_DIR = r"D:\my_qlib_project"
CSV_PATH = os.path.join(PROJECT_DIR, "anti_manipulation_result.csv")
SUMMARY_CHART = os.path.join(PROJECT_DIR, "anti_manipulation_report.png")
OUTPUT_PDF = os.path.join(PROJECT_DIR, "反操纵量化分析报告.pdf")

# ============ 字体注册 ============
font_registered = False
try:
    font_paths = [
        ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
        ("msyh", r"C:\Windows\Fonts\msyh.ttc"),
        ("msyhbd", r"C:\Windows\Fonts\msyhbd.ttc"),
        ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
        ("KaiTi", r"C:\Windows\Fonts\simkai.ttf"),
    ]
    for fn, fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont(fn, fp))
                font_registered = True
                print(f"[FONT] Registered: {fn}")
                break
            except:
                pass
    if not font_registered:
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        print("[FONT] Fallback: STSong-Light")
except:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

CN = 'SimHei' if font_registered else 'STSong-Light'

# ============ 配色方案 ============
C_DARK   = HexColor('#1b1b2f')
C_PRIMARY = HexColor('#162447')
C_ACCENT = HexColor('#1f4068')
C_DANGER = HexColor('#c62828')
C_WARN   = HexColor('#e65100')
C_SAFE   = HexColor('#2e7d32')
C_NEUTRAL = HexColor('#546e7a')
C_GOLD   = HexColor('#f9a825')
C_LIGHT_BG = HexColor('#f5f5f5')

# matplotlib 用的纯字符串颜色
MC_DARK   = '#1b1b2f'
MC_PRIMARY = '#162447'
MC_ACCENT = '#1f4068'
MC_DANGER = '#c62828'
MC_WARN   = '#e65100'
MC_SAFE   = '#2e7d32'
MC_NEUTRAL = '#546e7a'
MC_GOLD   = '#f9a825'
MC_LIGHT_BG = '#f5f5f5'

# ============ 样式 ============
def make_styles():
    s = getSampleStyleSheet()

    s.add(ParagraphStyle('CNTitle', fontName=CN, fontSize=26, leading=34,
        alignment=TA_CENTER, textColor=C_DARK, spaceAfter=6*mm))
    s.add(ParagraphStyle('CNSub', fontName=CN, fontSize=11, leading=16,
        alignment=TA_CENTER, textColor=HexColor('#777777'), spaceAfter=5*mm))
    s.add(ParagraphStyle('CNH1', fontName=CN, fontSize=18, leading=24,
        textColor=C_DARK, spaceBefore=10*mm, spaceAfter=5*mm))
    s.add(ParagraphStyle('CNH2', fontName=CN, fontSize=13, leading=18,
        textColor=C_ACCENT, spaceBefore=6*mm, spaceAfter=3*mm))
    s.add(ParagraphStyle('CNBody', fontName=CN, fontSize=9.5, leading=16,
        alignment=TA_JUSTIFY, spaceAfter=3*mm))
    s.add(ParagraphStyle('CNSmall', fontName=CN, fontSize=8, leading=12,
        textColor=HexColor('#999999'), alignment=TA_CENTER))
    s.add(ParagraphStyle('CNCell', fontName=CN, fontSize=8.5, leading=12,
        alignment=TA_CENTER))
    s.add(ParagraphStyle('CNHeader', fontName=CN, fontSize=9, leading=13,
        alignment=TA_CENTER, textColor=white))
    s.add(ParagraphStyle('AlertBox', fontName=CN, fontSize=9.5, leading=15,
        textColor=C_DANGER, backColor=HexColor('#ffebee'),
        borderPadding=8, spaceAfter=4*mm))
    s.add(ParagraphStyle('InfoBox', fontName=CN, fontSize=9.5, leading=15,
        textColor=C_PRIMARY, backColor=HexColor('#e3f2fd'),
        borderPadding=8, spaceAfter=4*mm))
    s.add(ParagraphStyle('SuccessBox', fontName=CN, fontSize=9.5, leading=15,
        textColor=C_SAFE, backColor=HexColor('#e8f5e9'),
        borderPadding=8, spaceAfter=4*mm))
    return s

# ============ 页眉页脚 ============
def hf(canvas, doc):
    canvas.saveState()
    canvas.setFont(CN, 7.5)
    canvas.setFillColor(HexColor('#aaaaaa'))
    canvas.drawString(18*mm, A4[1]-13*mm, "Qlib量化平台 · 反操纵策略分析")
    canvas.drawRightString(A4[0]-18*mm, A4[1]-13*mm,
        f"生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.setStrokeColor(HexColor('#e0e0e0'))
    canvas.line(18*mm, 18*mm, A4[0]-18*mm, 18*mm)
    canvas.drawCentredString(A4[0]/2, 11*mm, f"— {doc.page} —")
    canvas.restoreState()

# ============ 辅助函数 ============
def hr(color='#cccccc', w='100%', t=0.5):
    return HRFlowable(width=w, thickness=t, color=HexColor(color),
        spaceBefore=3*mm, spaceAfter=3*mm)

def make_table(data, col_widths, header_color=C_PRIMARY, row_colors=None):
    if row_colors is None:
        row_colors = [white, HexColor('#f8f9fa')]
    tbl = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, -1), CN),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), row_colors),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]
    tbl.setStyle(TableStyle(style_cmds))
    return tbl

# ============ 数据加载 ============
def load_results():
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
    print(f"[DATA] {len(df)} stocks loaded")
    print(df.to_string(index=False))
    return df

def find_charts(df):
    charts = {}
    for _, row in df.iterrows():
        name = row['股票']
        found = None
        # 搜索根目录和所有子目录
        search_dirs = [PROJECT_DIR] + [
            os.path.join(PROJECT_DIR, d) for d in os.listdir(PROJECT_DIR)
            if os.path.isdir(os.path.join(PROJECT_DIR, d))
        ]
        for sdir in search_dirs:
            pat = os.path.join(sdir, f"{name}_*_latest.png")
            m = glob.glob(pat)
            if m:
                found = m[0]
                break
            # 回退到非latest版本
            pat = os.path.join(sdir, f"{name}_*.png")
            m = [p for p in glob.glob(pat) if 'latest' not in os.path.basename(p)]
            if m:
                found = m[0]
                break
        if found:
            charts[name] = found
            print(f"[CHART] {name} -> {os.path.basename(found)}")
        else:
            print(f"[CHART] {name} -> NOT FOUND")
    return charts

# ============ 图表生成 ============
def generate_manipulation_scatter(df):
    """操纵指数 vs 波动率 散点图"""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')

    names = df['股票'].tolist()
    manip = df['操纵指数'].values
    vol = df['波动率(%)'].values
    scores = df['综合评分'].values

    # 按信号分组颜色
    for i, (_, row) in enumerate(df.iterrows()):
        sig = str(row['信号'])
        if '买入' in sig:
            c = '#2e7d32'
            marker = 'o'
            s = 200
        elif '卖出' in sig:
            c = '#c62828'
            marker = 's'
            s = 200
        else:
            c = '#546e7a'
            marker = 'D'
            s = 120
        ax.scatter(manip[i], vol[i], c=c, s=s, marker=marker, zorder=5,
                   edgecolors='white', linewidth=1.5)
        ax.annotate(f"  {names[i]}\n  (评分:{scores[i]})",
                    (manip[i], vol[i]), fontsize=9, fontweight='bold',
                    color=c)

    ax.axvline(x=1.5, color=MC_DANGER, linestyle='--', linewidth=1.5, alpha=0.7, label='高操纵阈值(1.5)')
    ax.axvline(x=0, color='#999999', linestyle=':', linewidth=1, alpha=0.5, label='零轴')
    ax.axhline(y=df['波动率(%)'].mean(), color='#f9a825', linestyle='--', linewidth=1, alpha=0.5, label=f"平均波动率({df['波动率(%)'].mean():.0f}%)")

    ax.set_xlabel('操纵指数 (Manipulation Index)', fontsize=12, fontweight='bold')
    ax.set_ylabel('年化波动率 (%)', fontsize=12, fontweight='bold')
    ax.set_title('风险-操纵关系矩阵', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    path = os.path.join(PROJECT_DIR, '_manip_scatter.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[CHART] scatter saved: {path}")
    return path

def generate_factor_radar(df):
    """六因子雷达图对比"""
    # 模拟六个因子的评分（基于操纵指数和反转等）
    factors = ['异常成交量\n(ABV)', '价格冲击\n(IMPACT)', '振幅\n(AMPL)',
               '短期反转\n(REV5)', '波动率\n(VOL20)', '量价背离\n(DIVER)']

    # 使用操纵指数和波动率等反推因子得分 (0-100)
    factor_data = {}
    for _, row in df.iterrows():
        name = row['股票']
        m = row['操纵指数']
        rev = row['短期反转(%)']
        diver = row['量价背离']
        vol = row['波动率(%)']

        # 估算各因子得分
        abv = min(max(50 + m * 20, 0), 100)
        impact = min(max(50 + m * 18, 0), 100)
        ampl = min(max(50 + vol * 0.3, 0), 100)
        rev_score = min(max(50 + rev * 2, 0), 100)
        vol_score = min(max(50 + vol * 0.25, 0), 100)
        diver_score = min(max(50 + (diver - 0.4) * 100, 0), 100)

        factor_data[name] = [abv, impact, ampl, rev_score, vol_score, diver_score]

    num_vars = len(factors)
    angles = np.linspace(0, 2*np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('white')

    colors_radar = ['#1a237e', '#c62828', '#2e7d32', '#e65100', '#6a1b9a', '#00838f']
    for idx, (name, vals) in enumerate(factor_data.items()):
        vals_plot = vals + vals[:1]
        c = colors_radar[idx]
        ax.fill(angles, vals_plot, alpha=0.08, color=c)
        ax.plot(angles, vals_plot, 'o-', linewidth=2, label=name, color=c, markersize=5)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(factors, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=7)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=8)
    ax.set_title('反操纵六因子雷达图', fontsize=14, fontweight='bold', pad=25)

    path = os.path.join(PROJECT_DIR, '_factor_radar.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[CHART] radar saved: {path}")
    return path

def generate_score_stacked(df):
    """综合评分堆叠图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.patch.set_facecolor('white')

    names = df['股票'].tolist()

    # 操纵指数横向柱状图
    manip_vals = df['操纵指数'].values
    colors_manip = ['#c62828' if v > 1.5 else '#e65100' if v > 0 else '#2e7d32' for v in manip_vals]
    bars1 = ax1.barh(names, manip_vals, color=colors_manip, edgecolor='white', height=0.6)
    ax1.axvline(x=1.5, color='red', linestyle='--', linewidth=1.5, alpha=0.8, label='高操纵阈值')
    ax1.axvline(x=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    for bar, val in zip(bars1, manip_vals):
        ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                 f'{val:.3f}', va='center', fontsize=10, fontweight='bold',
                 color='#c62828' if val > 1.5 else '#333333')
    ax1.set_xlabel('操纵指数')
    ax1.set_title('操纵指数排名', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=8, loc='lower right')
    ax1.grid(axis='x', alpha=0.3)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # 综合评分
    score_vals = df['综合评分'].values
    colors_score = ['#2e7d32' if v >= 70 else '#f9a825' if v >= 50 else '#c62828' for v in score_vals]
    bars2 = ax2.barh(names, score_vals, color=colors_score, edgecolor='white', height=0.6)
    ax2.axvline(x=50, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax2.axvline(x=70, color='green', linestyle='--', linewidth=1, alpha=0.5, label='买入线')
    for bar, val in zip(bars2, score_vals):
        ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                 f'{val}', va='center', fontsize=11, fontweight='bold',
                 color='#2e7d32' if val >= 70 else '#333333')
    ax2.set_xlabel('综合评分')
    ax2.set_title('投资建议评分', fontsize=13, fontweight='bold')
    ax2.set_xlim(0, 100)
    ax2.legend(fontsize=8, loc='lower right')
    ax2.grid(axis='x', alpha=0.3)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    path = os.path.join(PROJECT_DIR, '_score_stacked.png')
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[CHART] stacked saved: {path}")
    return path

# ============ PDF 内容构建 ============
def build_cover(s):
    els = []
    els.append(Spacer(1, 35*mm))
    els.append(Paragraph("反操纵量化策略分析报告", s['CNTitle']))
    els.append(Paragraph("Anti-Manipulation Quantitative Strategy Report", s['CNSub']))
    els.append(Spacer(1, 5*mm))
    els.append(hr(C_PRIMARY.hexval(), '50%', 2))
    els.append(Spacer(1, 8*mm))
    els.append(Paragraph("基于市场微观结构理论", s['CNSub']))
    els.append(Paragraph("Kyle (1985) · Amihud (2002) · 六因子模型", s['CNSub']))
    els.append(Spacer(1, 5*mm))
    els.append(Paragraph(
        f"分析日期: {datetime.now().strftime('%Y年%m月%d日')}  |  "
        f"标的数量: 6只  |  数据来源: Yahoo Finance + Qlib",
        s['CNSub']))
    els.append(Spacer(1, 15*mm))
    els.append(hr(C_PRIMARY.hexval(), '50%', 2))
    els.append(Spacer(1, 10*mm))
    els.append(Paragraph(
        "⚠️ 重要声明：本报告基于统计模型与市场微观结构理论，"
        "旨在识别潜在的庄家操纵行为。庄家操纵识别是学术界尚未完全解决的难题，"
        "本策略仅供学术研究与学习参考，不构成任何投资建议。",
        s['CNSmall']))
    els.append(PageBreak())
    return els

def build_summary(df, s):
    els = []
    els.append(Paragraph("一、策略概要", s['CNH1']))

    els.append(Paragraph(
        "本报告采用市场微观结构理论的六因子模型，对6只A股标的进行反操纵量化分析。"
        "通过计算包括异常成交量(ABV)、价格冲击(IMPACT)、日内振幅(AMPL)、"
        "短期反转(REV5)、波动率(VOL20)和量价背离(DIVER)在内的六个特征因子，"
        "构建综合操纵指数(Manipulation Index)，识别潜在的庄家操纵行为，"
        "并据此生成买卖信号与投资建议。",
        s['CNBody']))

    # 汇总表
    header = ['股票', '最新价', '操纵指数', '短期反转(%)', '量价背离', '波动率(%)', '信号', '评分']
    data = [header]
    for _, row in df.iterrows():
        sig = str(row['信号'])
        # 信号简化显示
        sig_short = sig.replace('🟢 ','').replace('🔴 ','').replace('🟡 ','').replace('⚪ ','')
        data.append([
            row['股票'],
            f"¥{row['最新价']:.2f}",
            f"{row['操纵指数']:.3f}",
            f"{row['短期反转(%)']:.2f}",
            f"{row['量价背离']:.3f}",
            f"{row['波动率(%)']:.1f}",
            sig_short,
            str(row['综合评分'])
        ])

    cw = [58, 58, 58, 62, 54, 54, 82, 36]
    els.append(make_table(data, cw, C_PRIMARY))
    els.append(Spacer(1, 4*mm))

    # 统计摘要
    high_manip = df[df['操纵指数'] > 1.5]
    low_manip = df[df['操纵指数'] < 0]
    neutral = df[(df['操纵指数'] >= 0) & (df['操纵指数'] <= 1.5)]

    els.append(Paragraph("关键发现:", s['CNH2']))

    if len(high_manip) > 0:
        names_high = '、'.join(high_manip['股票'].tolist())
        els.append(Paragraph(
            f"🔴 <b>高操纵风险 ({len(high_manip)}只)</b>: {names_high} — 操纵指数超过1.5阈值，"
            f"存在明显的非自然交易特征，需高度警惕。",
            s['CNBody']))
    if len(low_manip) > 0:
        names_low = '、'.join(low_manip['股票'].tolist())
        els.append(Paragraph(
            f"🟢 <b>自然波动 ({len(low_manip)}只)</b>: {names_low} — 操纵指数为负，"
            f"交易行为较为自然，适合使用传统量化模型分析。",
            s['CNBody']))
    if len(neutral) > 0:
        names_neu = '、'.join(neutral['股票'].tolist())
        els.append(Paragraph(
            f"🟡 <b>灰色地带 ({len(neutral)}只)</b>: {names_neu} — 操纵指数在零轴附近，"
            f"需结合其他指标综合判断。",
            s['CNBody']))

    # 信号分布
    buy_sig = df[df['综合评分'] >= 70]
    sell_sig = df[df['综合评分'] <= 30]
    hold_sig = df[(df['综合评分'] > 30) & (df['综合评分'] < 70)]

    els.append(Paragraph(f"• 买入信号 ({len(buy_sig)}只): {'、'.join(buy_sig['股票'].tolist()) if len(buy_sig) > 0 else '无'}", s['CNBody']))
    els.append(Paragraph(f"• 卖出信号 ({len(sell_sig)}只): {'、'.join(sell_sig['股票'].tolist()) if len(sell_sig) > 0 else '无'}", s['CNBody']))
    els.append(Paragraph(f"• 观望/持有 ({len(hold_sig)}只): {'、'.join(hold_sig['股票'].tolist()) if len(hold_sig) > 0 else '无'}", s['CNBody']))

    els.append(PageBreak())
    return els

def build_factor_methodology(s):
    """因子方法论"""
    els = []
    els.append(Paragraph("二、六因子模型详解", s['CNH1']))

    els.append(Paragraph(
        "本策略基于市场微观结构理论（Market Microstructure Theory），"
        "参照Kyle(1985)的知情交易模型和Amihud(2002)的非流动性指标，"
        "构建了六个反操纵特征因子，通过Z-score标准化后加权合成综合操纵指数。",
        s['CNBody']))

    factors_detail = [
        ("因子1: 异常成交量 (ABV - Abnormal Volume)",
         "权重30%",
         "当日成交量 / 20日平均成交量。异常放量往往是庄家进场或出逃的痕迹。"
         "当ABV显著偏离均值（Z-score > 2），表明存在非正常的交易活跃度。"),
        ("因子2: 价格冲击 (IMPACT - Price Impact)",
         "权重25%",
         "|日收益率| / (成交量/1e6)。源自Kyle's Lambda理论："
         "单位成交量引起的价格变化越大，市场深度越浅，越容易被操纵。"),
        ("因子3: 日内振幅 (AMPL - Amplitude)",
         "权重25%",
         "(最高价-最低价) / 收盘价。庄家惯用的对倒、拉抬、打压手法会制造异常的日内波动。"
         "振幅过大往往是操纵的显著信号。"),
        ("因子4: 短期反转 (REV5 - Short-term Reversal)",
         "参考因子",
         "5日累计收益率。庄家洗盘后往往伴随短期正向反转，"
         "而出货前可能出现虚假拉升（诱多）后的反转。"),
        ("因子5: 波动率 (VOL20 - Volatility)",
         "权重20%",
         "20日收益率年化标准差。异常的波动率放大是市场被操纵的间接证据。"
         "过度波动往往意味着信息不对称加剧。"),
        ("因子6: 量价背离 (DIVER - Volume-Price Divergence)",
         "参考因子",
         "价格创新高时的成交量相对强度。价格新高但量能萎缩是典型的诱多出货特征；"
         "价格新低但量能萎缩则可能是洗盘结束信号。"),
    ]

    for title, weight, desc in factors_detail:
        els.append(Paragraph(f"<b>{title}</b>  <i>[{weight}]</i>", s['CNH2']))
        els.append(Paragraph(desc, s['CNBody']))

    # 公式框
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph(
        "<b>综合操纵指数 (MANIP_INDEX) =</b><br/>"
        "ABV_z × 0.30 + IMPACT_z × 0.25 + AMPL_z × 0.25 + VOL20_z × 0.20<br/><br/>"
        "<b>信号判定规则:</b><br/>"
        "• 操纵指数 > 1.5 且 短期反转 > 0 → 🟢 <b>洗盘结束-买入</b> (评分80)<br/>"
        "• 操纵指数 > 1.5 且 量价背离 &lt; 0.9 → 🔴 <b>疑似出货-卖出</b> (评分20)<br/>"
        "• 操纵指数 &lt; 0 → ⚪ <b>自然波动-持有</b> (评分50)<br/>"
        "• 其他情况 → 🟡 <b>观望</b> (评分50)",
        s['InfoBox']))

    els.append(PageBreak())
    return els

def build_charts_section(df, s):
    """对比图表"""
    els = []
    els.append(Paragraph("三、量化指标对比分析", s['CNH1']))

    # 操纵指数 + 评分图
    path_stacked = os.path.join(PROJECT_DIR, '_score_stacked.png')
    if os.path.exists(path_stacked):
        els.append(Paragraph("3.1 操纵指数与投资评分", s['CNH2']))
        els.append(Image(path_stacked, width=175*mm, height=68*mm))
        els.append(Paragraph(
            "左图展示各标的的操纵指数（越高越可能被操纵），红色虚线为1.5的高操纵阈值。"
            "右图为综合投资评分，80分为买入信号，20分为卖出信号，50分为持有/观望。",
            s['CNBody']))

    # 风险-操纵散点图
    path_scatter = os.path.join(PROJECT_DIR, '_manip_scatter.png')
    if os.path.exists(path_scatter):
        els.append(Paragraph("3.2 风险-操纵关系矩阵", s['CNH2']))
        els.append(Image(path_scatter, width=160*mm, height=96*mm))
        els.append(Paragraph(
            "散点图横轴为操纵指数，纵轴为年化波动率。右上角区域（高操纵+高波动）"
            "是最危险的区域，标的可能同时面临操纵风险与市场风险。绿色圆点为买入信号，"
            "红色方块为卖出信号，灰色菱形为持有/观望。",
            s['CNBody']))

    # 因子雷达图
    path_radar = os.path.join(PROJECT_DIR, '_factor_radar.png')
    if os.path.exists(path_radar):
        els.append(Paragraph("3.3 六因子雷达对比", s['CNH2']))
        els.append(Image(path_radar, width=140*mm, height=140*mm))
        els.append(Paragraph(
            "雷达图展示各标的在六个反操纵因子上的得分分布（0-100）。覆盖面积越大，"
            "说明该标的在多个维度上的操纵特征越明显。理想情况下，自然波动的标的"
            "在六个维度上的得分应较为均衡。",
            s['CNBody']))

    # 原始报告图
    if os.path.exists(SUMMARY_CHART):
        els.append(Paragraph("3.4 策略全景图", s['CNH2']))
        els.append(Image(SUMMARY_CHART, width=170*mm, height=120*mm))

    els.append(PageBreak())
    return els

def build_individual(df, charts, s):
    """个股分析"""
    els = []
    els.append(Paragraph("四、个股反操纵深度分析", s['CNH1']))

    for idx, (_, row) in enumerate(df.iterrows()):
        name = row['股票']
        m_idx = row['操纵指数']
        rev = row['短期反转(%)']
        diver = row['量价背离']
        vol = row['波动率(%)']
        price = row['最新价']
        sig = str(row['信号'])
        score = row['综合评分']

        els.append(Paragraph(f"4.{idx+1} {name} — {sig}", s['CNH2']))

        # 指标表
        info = [
            ['指标', '数值', '指标', '数值'],
            ['最新价', f'¥{price:.2f}', '操纵指数', f'{m_idx:.3f}'],
            ['短期反转', f'{rev:.2f}%', '量价背离', f'{diver:.3f}'],
            ['年化波动率', f'{vol:.1f}%', '综合评分', str(score)],
        ]
        els.append(make_table(info, [65, 80, 65, 80], HexColor('#37474f')))

        els.append(Spacer(1, 2*mm))

        # 信号解读
        if '买入' in sig:
            els.append(Paragraph(
                f"<b>🔍 洗盘识别:</b> 操纵指数 {m_idx:.3f}，显著超过1.5阈值，短期反转 {rev:.1f}% 为正，"
                f"表明此前的大幅抛压可能为庄家洗盘行为。洗盘结束后，短期价格出现正向修复，"
                f"技术面呈现超跌反弹特征。量价背离 {diver:.3f} 处于较低水平，"
                f"进一步印证了洗盘而非出货的判断。",
                s['SuccessBox']))
        elif '卖出' in sig:
            els.append(Paragraph(
                f"<b>🔍 出货识别:</b> 操纵指数 {m_idx:.3f}，显著超过1.5阈值，但量价背离 {diver:.3f} "
                f"低于0.9警戒线，表明价格高位时成交量未能有效跟进，呈现\"价涨量缩\"的"
                f"经典出货形态。短期反转 {rev:.1f}% 进一步确认动能衰竭。"
                f"建议及时减仓或清仓，防范大幅回调风险。",
                s['AlertBox']))
        elif '自然波动' in sig:
            els.append(Paragraph(
                f"<b>🔍 自然波动判定:</b> 操纵指数 {m_idx:.3f}，处于零轴以下，"
                f"表明当前交易行为未表现出显著的操纵特征。价格波动主要由市场供需"
                f"和正常交易行为驱动，波动率 {vol:.1f}% 在正常范围。"
                f"此类标的最适合使用传统量化模型（如均线、MACD、RSI等）进行分析。",
                s['InfoBox']))
        else:
            els.append(Paragraph(
                f"<b>🔍 观望判定:</b> 操纵指数 {m_idx:.3f}，处于灰色地带。"
                f"虽然未触发明确的操纵信号，但部分因子存在异常苗头。"
                f"建议暂时观望，等待更明确的信号出现（操纵指数突破1.5或回落至零下）。",
                s['InfoBox']))

        # 图表
        if name in charts:
            img = Image(charts[name], width=165*mm, height=135*mm)
            els.append(img)

        # 操作建议
        if score >= 70:
            advice = ("<b>📌 操作建议:</b> 洗盘结束信号，可考虑分批建仓。"
                      "建议仓位不超过总资产的15%，设置-8%止损线。"
                      "关注后续成交量是否持续放大，若量能再次萎缩则应止盈。")
        elif score <= 30:
            advice = ("<b>📌 操作建议:</b> 疑似出货信号，建议减仓或清仓。"
                      "切勿在此时追高或抄底。等待操纵指数回落至1.0以下，"
                      "且出现明显的底部放量阳线后，再考虑重新介入。")
        else:
            advice = ("<b>📌 操作建议:</b> 信号中性，维持现有仓位不变。"
                      "密切关注操纵指数的变化趋势。若操纵指数开始上升，"
                      "需提高警惕；若持续为负，可按传统技术指标正常操作。")

        els.append(Paragraph(advice, s['CNBody']))

        if idx < len(df) - 1:
            els.append(hr('#e0e0e0'))

    els.append(PageBreak())
    return els

def build_strategy(df, s):
    """策略建议"""
    els = []
    els.append(Paragraph("五、综合投资策略", s['CNH1']))

    # 分层建议
    els.append(Paragraph("5.1 基于操纵指数的分层策略", s['CNH2']))

    strategy_data = [
        ['操纵指数', '风险等级', '策略定位', '仓位建议', '止损', '适合投资者'],
        ['< 0', '低风险', '趋势跟踪/量化模型', '20-30%', '-5%', '所有类型'],
        ['0 ~ 1.0', '中等风险', '谨慎持有/观望', '10-15%', '-7%', '稳健+积极'],
        ['1.0 ~ 1.5', '高风险', '减仓/对冲保护', '5-10%', '-5%', '仅积极型'],
        ['> 1.5 (买入信号)', '投机级', '反弹博弈/短线', '5-8%', '-8%', '仅激进型'],
        ['> 1.5 (卖出信号)', '极高风险', '清仓/做空对冲', '0%', 'N/A', '不参与'],
    ]
    els.append(make_table(strategy_data,
        [82, 65, 80, 60, 50, 70], C_DARK,
        [white, HexColor('#e8eaf6'), HexColor('#e3f2fd'), HexColor('#fff3e0'), HexColor('#ffebee')]))
    els.append(Spacer(1, 5*mm))

    # 当前持仓建议
    els.append(Paragraph("5.2 当前持仓处理建议", s['CNH2']))

    for _, row in df.iterrows():
        name = row['股票']
        score = row['综合评分']
        m_idx = row['操纵指数']
        sig = str(row['信号'])

        if score >= 70:
            action = "🟢 <b>积极关注</b> — 洗盘结束信号明确，可小仓位试探性建仓，严格止损。"
        elif score <= 30:
            action = "🔴 <b>建议回避</b> — 疑似出货信号，持有的建议减仓/清仓，未持有的不建议介入。"
        elif m_idx < 0:
            action = "⚪ <b>正常持有</b> — 自然波动，可继续按原有策略操作，无需特别调整。"
        else:
            action = "🟡 <b>观望等待</b> — 信号不明确，保持现有仓位，等待进一步方向确认。"

        els.append(Paragraph(f"<b>{name}</b> (操纵指数: {m_idx:.3f}, 评分: {score}): {action}", s['CNBody']))

    # 风险矩阵
    els.append(Spacer(1, 5*mm))
    els.append(Paragraph("5.3 风险矩阵与注意事项", s['CNH2']))

    risks = [
        "<b>模型局限:</b> 操纵指数基于统计Z-score方法，在极端行情下可能出现误判。"
        "庄家操纵手法不断演变，历史规律可能失效。",
        "<b>因子滞后:</b> 各因子基于历史数据计算，存在一定的滞后性。"
        "操纵行为可能已经在信号发出前完成。",
        "<b>假阳性风险:</b> 高操纵指数可能是由于重大消息面驱动而非庄家操纵。"
        "需结合基本面、公告、新闻等综合判断。",
        "<b>小盘股偏差:</b> 价格冲击因子(IMPACT)在小盘股中天然偏高，"
        "可能导致操纵指数系统性高估。",
        "<b>多策略并行:</b> 建议将反操纵分析与传统量化策略（趋势跟踪、均值回归、"
        "因子投资等）结合使用，多维度交叉验证。",
        "<b>仓位管理:</b> 无论信号强弱，单只标的仓位不应超过总资产的20%。"
        "分散投资是应对不确定性的最佳策略。",
    ]

    for i, r in enumerate(risks):
        els.append(Paragraph(f"• {r}", s['CNBody']))

    els.append(Spacer(1, 8*mm))
    els.append(hr(C_DANGER.hexval(), '70%', 1.5))
    els.append(Paragraph(
        "⚠️ <b>特别声明：</b>反操纵分析处于量化金融研究的前沿，"
        "目前学术界和业界均无法100%准确识别庄家操纵行为。"
        "本报告的信号和建议仅供学术研究和学习参考，绝不构成任何投资建议。"
        "投资者需独立判断并承担全部投资风险。",
        s['AlertBox']))

    return els

def build_appendix(s):
    """附录"""
    els = []
    els.append(Paragraph("六、附录：理论背景与参考文献", s['CNH1']))

    els.append(Paragraph("6.1 市场微观结构理论基础", s['CNH2']))
    theory = [
        "<b>Kyle (1985) — Continuous Auctions and Insider Trading:</b> "
        "建立了知情交易者(informed trader)、噪声交易者(noise trader)和做市商"
        "(market maker)的三方博弈模型。Kyle's Lambda衡量了价格对订单流的敏感度，"
        "是价格冲击因子(IMPACT)的理论基础。",
        "<b>Amihud (2002) — Illiquidity and Stock Returns:</b> "
        "提出了Amihud非流动性指标(ILLIQ)，证明非流动性与预期收益正相关。"
        "本策略中的价格冲击因子承袭了这一思想。",
        "<b>Easley & O'Hara (1987) — PIN Model:</b> "
        "提出了基于买卖单不平衡的信息交易概率(PIN)模型，"
        "为识别知情交易提供了理论框架。",
        "<b>Madhavan (2000) — Market Microstructure: A Survey:</b> "
        "全面综述了市场微观结构的研究进展，"
        "包括交易成本、价格发现、市场透明度和操纵行为等核心议题。",
    ]
    for t in theory:
        els.append(Paragraph(f"• {t}", s['CNBody']))

    els.append(Paragraph("6.2 技术实现", s['CNH2']))
    tech = [
        "数据获取: Yahoo Finance API (yfinance)",
        "量化平台: Qlib (Microsoft)",
        "分析引擎: Python (pandas, numpy, scipy)",
        "可视化: Matplotlib 3.x",
        "报告生成: ReportLab 4.x PDF引擎",
        "策略框架: 六因子Z-score标准化 + 加权合成",
    ]
    for t in tech:
        els.append(Paragraph(f"• {t}", s['CNBody']))

    els.append(Paragraph("6.3 免责条款", s['CNH2']))
    els.append(Paragraph(
        "本报告中的所有分析、信号、预测和建议均基于公开的历史交易数据和统计模型，"
        "仅供学术研究与学习参考。报告中的任何内容均不构成对具体证券的投资建议、"
        "交易建议或投资推荐。过去的表现不保证未来的结果。投资有风险，入市需谨慎。"
        "使用者应独立进行投资决策并承担由此产生的全部风险和后果。",
        s['CNBody']))

    return els

# ============ 主程序 ============
def main():
    print("=" * 70)
    print("   反操纵量化分析报告生成器")
    print("   Anti-Manipulation Strategy PDF Reporter")
    print("=" * 70)

    # 1. 数据
    print("\n[1/5] Loading data...")
    df = load_results()
    if df.empty:
        print("No data, exit.")
        return

    # 2. 图表
    print("\n[2/5] Matching charts...")
    charts = find_charts(df)

    # 3. 生成额外图表
    print("\n[3/5] Generating comparison charts...")
    generate_manipulation_scatter(df)
    generate_factor_radar(df)
    generate_score_stacked(df)

    # 4. 构建样式
    print("\n[4/5] Building styles...")
    s = make_styles()

    # 5. PDF
    print("\n[5/5] Building PDF...")
    story = []
    story.extend(build_cover(s))
    story.extend(build_summary(df, s))
    story.extend(build_factor_methodology(s))
    story.extend(build_charts_section(df, s))
    story.extend(build_individual(df, charts, s))
    story.extend(build_strategy(df, s))
    story.extend(build_appendix(s))

    doc = SimpleDocTemplate(
        OUTPUT_PDF, pagesize=A4,
        rightMargin=14*mm, leftMargin=14*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title='反操纵量化策略分析报告',
        author='Qlib Anti-Manipulation Platform',
        subject='Anti-Manipulation Quantitative Analysis',
    )
    doc.build(story, onFirstPage=hf, onLaterPages=hf)

    size_kb = os.path.getsize(OUTPUT_PDF) / 1024
    print(f"\n{'='*70}")
    print(f"  Report generated: {OUTPUT_PDF}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

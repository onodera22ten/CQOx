"""
マーケティングROI最適化 - 可視化生成スクリプト

生成する可視化:
1. チャネル別ROI比較（バーチャート）
2. 予算配分最適化（サンキーダイアグラム）
3. LTV分布（ヒストグラム + 箱ひげ図）
4. アトリビューション（円グラフ）
5. 最適化シナリオ比較（3Dサーフェス）
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os

# 結果読み込み
with open('/home/user/CQOx/data/marketing_roi_optimization_results.json', 'r') as f:
    results = json.load(f)

output_dir = "/home/user/CQOx/visualizations/marketing_roi"
os.makedirs(output_dir, exist_ok=True)

print("=" * 80)
print("マーケティングROI可視化生成")
print("=" * 80)

# 1. チャネル別ROI比較
print("\n[1/5] チャネル別ROI比較...")
channel_roi_df = pd.DataFrame(results['phase1_channel_roi'])

fig = go.Figure()

# ROI バー
fig.add_trace(go.Bar(
    x=channel_roi_df['channel'],
    y=channel_roi_df['roi'],
    name='ROI (%)',
    marker=dict(
        color=channel_roi_df['roi'],
        colorscale='RdYlGn',
        cmin=-150,
        cmax=150,
        colorbar=dict(title='ROI (%)')
    ),
    text=[f"{roi:.1f}%" for roi in channel_roi_df['roi']],
    textposition='outside'
))

# ゼロライン
fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="損益分岐点")

fig.update_layout(
    title='チャネル別ROI比較<br><sub>増分粗利ベース（粗利率40%）</sub>',
    xaxis_title='マーケティングチャネル',
    yaxis_title='ROI (%)',
    width=1200,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/channel_roi_comparison.html")
print(f"    ✅ {output_dir}/channel_roi_comparison.html")

# 2. 予算配分最適化（現在vs最適）
print("\n[2/5] 予算配分最適化...")
current_allocation = results['phase1_optimization']['current_allocation']
optimal_allocation = results['phase1_optimization']['optimal_allocation']

channels = list(current_allocation.keys())
current_values = [current_allocation[ch] for ch in channels]
optimal_values = [optimal_allocation[ch] for ch in channels]

fig = go.Figure()

fig.add_trace(go.Bar(
    name='現在の配分',
    x=channels,
    y=current_values,
    marker_color='lightblue',
    text=[f"{v:.0f}万円" for v in current_values],
    textposition='outside'
))

fig.add_trace(go.Bar(
    name='最適配分',
    x=channels,
    y=optimal_values,
    marker_color='orange',
    text=[f"{v:.0f}万円" for v in optimal_values],
    textposition='outside'
))

fig.update_layout(
    title='予算配分最適化: 現在 vs 最適<br><sub>線形計画法による最適化</sub>',
    xaxis_title='マーケティングチャネル',
    yaxis_title='予算（万円）',
    barmode='group',
    width=1200,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/budget_optimization_comparison.html")
print(f"    ✅ {output_dir}/budget_optimization_comparison.html")

# 3. LTV分布
print("\n[3/5] LTV分布...")
ltv_df = pd.DataFrame(results['phase2_ltv'])

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=('LTV分布（ヒストグラム）', 'セグメント別LTV（箱ひげ図）')
)

# ヒストグラム
fig.add_trace(
    go.Histogram(
        x=ltv_df['predicted_ltv'],
        nbinsx=50,
        name='LTV分布',
        marker_color='skyblue'
    ),
    row=1, col=1
)

# 箱ひげ図
if 'segment' in ltv_df.columns:
    for segment in ltv_df['segment'].unique():
        segment_data = ltv_df[ltv_df['segment'] == segment]
        fig.add_trace(
            go.Box(
                y=segment_data['predicted_ltv'],
                name=segment,
                boxmean='sd'
            ),
            row=1, col=2
        )

fig.update_xaxes(title_text="LTV（円）", row=1, col=1)
fig.update_yaxes(title_text="顧客数", row=1, col=1)
fig.update_xaxes(title_text="セグメント", row=1, col=2)
fig.update_yaxes(title_text="LTV（円）", row=1, col=2)

fig.update_layout(
    title_text='顧客生涯価値（LTV）分析<br><sub>3年間予測 + チャーン確率調整</sub>',
    width=1400,
    height=600,
    showlegend=True,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/ltv_distribution.html")
print(f"    ✅ {output_dir}/ltv_distribution.html")

# 4. マルチタッチアトリビューション
print("\n[4/5] マルチタッチアトリビューション...")
attribution = results['phase2_attribution']

# タッチポイント名をクリーンアップ
clean_attribution = {
    k.replace('touch_', ''): v for k, v in attribution.items()
}

fig = go.Figure(data=[go.Pie(
    labels=list(clean_attribution.keys()),
    values=list(clean_attribution.values()),
    hole=0.4,
    marker=dict(colors=px.colors.qualitative.Set3),
    textinfo='label+percent',
    textposition='outside'
)])

fig.update_layout(
    title='マルチタッチアトリビューション（Shapley値）<br><sub>各チャネルの貢献度</sub>',
    width=1000,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/multi_touch_attribution.html")
print(f"    ✅ {output_dir}/multi_touch_attribution.html")

# 5. ダッシュボードサマリー
print("\n[5/5] エグゼクティブダッシュボード...")
dashboard = results['phase4_dashboard']

# メトリクスカード
fig = go.Figure()

metrics = [
    ("総予算", f"{dashboard['current_performance']['total_budget']:.0f}万円", "lightblue"),
    ("平均ROI", f"{dashboard['current_performance']['average_roi']:.1f}%", "lightcoral"),
    ("期待改善率", f"{dashboard['optimization_proposal']['expected_improvement_pct']:.1f}%", "lightgreen"),
]

annotations = []
for i, (label, value, color) in enumerate(metrics):
    x_pos = (i + 0.5) / len(metrics)

    fig.add_shape(
        type="rect",
        x0=i/len(metrics), x1=(i+1)/len(metrics),
        y0=0, y1=1,
        fillcolor=color,
        opacity=0.3,
        line_width=0
    )

    annotations.append(dict(
        x=x_pos, y=0.7,
        text=f"<b>{label}</b>",
        showarrow=False,
        font=dict(size=20)
    ))

    annotations.append(dict(
        x=x_pos, y=0.3,
        text=f"<b>{value}</b>",
        showarrow=False,
        font=dict(size=30, color='black')
    ))

fig.update_layout(
    title='エグゼクティブダッシュボード<br><sub>リアルタイムKPI</sub>',
    xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    annotations=annotations,
    width=1200,
    height=400,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/executive_dashboard.html")
print(f"    ✅ {output_dir}/executive_dashboard.html")

print("\n" + "=" * 80)
print("✅ 全可視化生成完了！")
print("=" * 80)
print(f"\n生成ファイル:")
print(f"  📊 {output_dir}/channel_roi_comparison.html")
print(f"  📊 {output_dir}/budget_optimization_comparison.html")
print(f"  📊 {output_dir}/ltv_distribution.html")
print(f"  📊 {output_dir}/multi_touch_attribution.html")
print(f"  📊 {output_dir}/executive_dashboard.html")

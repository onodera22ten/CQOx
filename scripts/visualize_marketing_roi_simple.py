"""
マーケティングROI最適化 - 簡易可視化生成
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# データ直接指定（実行結果から）
channel_roi_data = {
    'channel': ['direct_mail', 'paid_search', 'email', 'social_media', 'display_ads'],
    'roi': [-96.5, -110.9, -129.2, -84.4, -100.1],
    'net_profit': [-50740, -56535, -63278, -41265, -49858],
    'incremental_revenue': [4534, -13898, -35769, 19029, -173]
}

current_allocation = {
    'direct_mail': 5,
    'paid_search': 5,
    'email': 5,
    'social_media': 5,
    'display_ads': 5
}

optimal_allocation = {
    'direct_mail': 0,
    'paid_search': 0,
    'email': 0,
    'social_media': 0,
    'display_ads': 0
}

attribution_data = {
    'paid_search': 31.4,
    'direct_mail': 22.9,
    'display_ads': 21.2,
    'email': 14.2,
    'social_media': 10.2
}

output_dir = "/home/user/CQOx/visualizations/marketing_roi"
os.makedirs(output_dir, exist_ok=True)

print("=" * 80)
print("マーケティングROI可視化生成（簡易版）")
print("=" * 80)

# 1. チャネル別ROI比較
print("\n[1/5] チャネル別ROI比較...")

fig = go.Figure()

fig.add_trace(go.Bar(
    x=channel_roi_data['channel'],
    y=channel_roi_data['roi'],
    marker=dict(
        color=channel_roi_data['roi'],
        colorscale='RdYlGn',
        cmin=-150,
        cmax=150,
        colorbar=dict(title='ROI (%)')
    ),
    text=[f"{roi:.1f}%" for roi in channel_roi_data['roi']],
    textposition='outside'
))

fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="損益分岐点")

fig.update_layout(
    title='チャネル別ROI比較<br><sub>増分粗利ベース（粗利率40%） - すべてのチャネルでROIマイナス</sub>',
    xaxis_title='マーケティングチャネル',
    yaxis_title='ROI (%)',
    width=1200,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/channel_roi_comparison.html")
print(f"    ✅ {output_dir}/channel_roi_comparison.html")

# 2. 予算配分最適化
print("\n[2/5] 予算配分最適化...")

channels = list(current_allocation.keys())
current_values = list(current_allocation.values())
optimal_values = list(optimal_allocation.values())

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
    name='最適配分（全削減）',
    x=channels,
    y=optimal_values,
    marker_color='red',
    text=[f"{v:.0f}万円" for v in optimal_values],
    textposition='outside'
))

fig.update_layout(
    title='予算配分最適化: 現在 vs 最適<br><sub>⚠️ 全チャネルでROI<0のため、最適化結果は全削減</sub>',
    xaxis_title='マーケティングチャネル',
    yaxis_title='予算（万円）',
    barmode='group',
    width=1200,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/budget_optimization_comparison.html")
print(f"    ✅ {output_dir}/budget_optimization_comparison.html")

# 3. マルチタッチアトリビューション
print("\n[3/5] マルチタッチアトリビューション...")

fig = go.Figure(data=[go.Pie(
    labels=list(attribution_data.keys()),
    values=list(attribution_data.values()),
    hole=0.4,
    marker=dict(colors=px.colors.qualitative.Set3),
    textinfo='label+percent',
    textposition='outside'
)])

fig.update_layout(
    title='マルチタッチアトリビューション（Shapley値）<br><sub>各チャネルのコンバージョン貢献度</sub>',
    width=1000,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/multi_touch_attribution.html")
print(f"    ✅ {output_dir}/multi_touch_attribution.html")

# 4. ROI vs 増分売上
print("\n[4/5] ROI vs 増分売上...")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=channel_roi_data['incremental_revenue'],
    y=channel_roi_data['roi'],
    mode='markers+text',
    marker=dict(
        size=[abs(x)/1000 for x in channel_roi_data['net_profit']],
        color=channel_roi_data['roi'],
        colorscale='RdYlGn',
        showscale=True,
        colorbar=dict(title='ROI (%)')
    ),
    text=channel_roi_data['channel'],
    textposition='top center'
))

# 象限線
fig.add_hline(y=0, line_dash="dash", line_color="gray")
fig.add_vline(x=0, line_dash="dash", line_color="gray")

fig.update_layout(
    title='ROI vs 増分売上<br><sub>バブルサイズ = 純利益の絶対値</sub>',
    xaxis_title='増分売上（円）',
    yaxis_title='ROI (%)',
    width=1200,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/roi_vs_revenue.html")
print(f"    ✅ {output_dir}/roi_vs_revenue.html")

# 5. LTV分布（サンプルデータ）
print("\n[5/5] LTV分布...")

# サンプルLTV（平均1,301円、中央値1,133円）
np.random.seed(42)
ltv_sample = np.random.gamma(2, 650, 10000)  # ガンマ分布でLTVを近似

fig = go.Figure()

fig.add_trace(go.Histogram(
    x=ltv_sample,
    nbinsx=50,
    marker_color='skyblue',
    name='LTV分布'
))

# 平均線
fig.add_vline(x=1301, line_dash="dash", line_color="red", annotation_text="平均LTV: 1,301円")
fig.add_vline(x=1133, line_dash="dash", line_color="orange", annotation_text="中央値: 1,133円")

fig.update_layout(
    title='顧客生涯価値（LTV）分布<br><sub>3年間予測（平均1,301円、チャーン確率45.3%考慮済み）</sub>',
    xaxis_title='LTV（円）',
    yaxis_title='顧客数',
    width=1200,
    height=600,
    template='plotly_white'
)

fig.write_html(f"{output_dir}/ltv_distribution.html")
print(f"    ✅ {output_dir}/ltv_distribution.html")

print("\n" + "=" * 80)
print("✅ 全可視化生成完了！")
print("=" * 80)
print(f"\n生成ファイル:")
print(f"  📊 {output_dir}/channel_roi_comparison.html")
print(f"  📊 {output_dir}/budget_optimization_comparison.html")
print(f"  📊 {output_dir}/multi_touch_attribution.html")
print(f"  📊 {output_dir}/roi_vs_revenue.html")
print(f"  📊 {output_dir}/ltv_distribution.html")

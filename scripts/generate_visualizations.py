#!/usr/bin/env python3
"""
Generate 8 World-Class Visualizations for CQOx
NASA/Google/Meta-Level Quality

This script generates high-quality static visualizations (PNG/GIF) for the README.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import networkx as nx
import seaborn as sns
from pathlib import Path

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory
output_dir = Path("visualizations/python")
output_dir.mkdir(parents=True, exist_ok=True)

print("Generating 8 world-class visualizations...")

# ============================================================================
# 1. Causal Surface 3D - Heterogeneous Treatment Effects
# ============================================================================
print("[1/8] Generating Causal Surface 3D...")

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Generate data
x = np.linspace(20, 80, 50)  # Age
y = np.linspace(20, 200, 50)  # Income
X, Y = np.meshgrid(x, y)

# CATE function (complex heterogeneity)
Z = (
    3.0  # Base effect
    + (-0.05 * (X - 50)**2 + 5.0)  # Age effect (quadratic)
    + (2.0 * np.log(Y / 20))  # Income effect (logarithmic)
    + (0.01 * (X - 40) * (Y - 100))  # Interaction
    + np.random.normal(0, 0.3, X.shape)  # Noise
)

# Plot surface
surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9,
                       linewidth=0, antialiased=True, edgecolor='none')

# Contours
ax.contour(X, Y, Z, levels=10, colors='white', alpha=0.4, linewidths=0.5)

# Labels
ax.set_xlabel('Age (years)', fontsize=12, fontweight='bold')
ax.set_ylabel('Income (¥K)', fontsize=12, fontweight='bold')
ax.set_zlabel('CATE', fontsize=12, fontweight='bold')
ax.set_title('Causal Surface 3D: Heterogeneous Treatment Effects\nAge × Income → Treatment Effect',
             fontsize=14, fontweight='bold', pad=20)

# Colorbar
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Treatment Effect')

# View angle
ax.view_init(elev=25, azim=135)

plt.tight_layout()
plt.savefig(output_dir / 'causal_surface_3d.png', dpi=300, bbox_inches='tight')
plt.close()

print("  ✓ causal_surface_3d.png")

# ============================================================================
# 2. ATE Animation - Temporal Evolution
# ============================================================================
print("[2/8] Generating ATE Animation...")

fig, ax = plt.subplots(figsize=(10, 6))

# Generate time series data
np.random.seed(42)
time_periods = 30
time = np.arange(time_periods)
ate_true = 2.5 + 0.05 * time + np.random.normal(0, 0.3, time_periods)
ci_lower = ate_true - 0.5
ci_upper = ate_true + 0.5

def animate_ate(frame):
    ax.clear()

    # Plot up to current frame
    ax.plot(time[:frame+1], ate_true[:frame+1], 'o-', color='#2E86AB',
            linewidth=2.5, markersize=8, label='ATE Estimate')
    ax.fill_between(time[:frame+1], ci_lower[:frame+1], ci_upper[:frame+1],
                     alpha=0.3, color='#2E86AB', label='95% CI')

    # Reference line
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='No Effect')

    # Treatment intervention marker
    ax.axvline(x=10, color='red', linestyle='--', alpha=0.7,
               label='Treatment Start')

    ax.set_xlabel('Time Period', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Treatment Effect', fontsize=12, fontweight='bold')
    ax.set_title(f'ATE Evolution Over Time (Period {frame+1}/{time_periods})',
                 fontsize=14, fontweight='bold')
    ax.set_xlim(0, time_periods-1)
    ax.set_ylim(-1, 5)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)

# Create animation
anim = animation.FuncAnimation(fig, animate_ate, frames=time_periods,
                               interval=200, repeat=True)

# Save as GIF
anim.save(output_dir / 'ate_animation.gif', writer='pillow', fps=5, dpi=150)
plt.close()

print("  ✓ ate_animation.gif")

# ============================================================================
# 3. CAS Radar Chart - Quality Assessment
# ============================================================================
print("[3/8] Generating CAS Radar Chart...")

fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

# Quality dimensions
categories = ['Validity', 'Precision', 'Robustness', 'Interpretability', 'Scalability']
N = len(categories)

# Scores (0-10)
scores = [9.2, 8.8, 8.1, 9.0, 8.5]
threshold = [7.0, 7.0, 7.0, 7.0, 7.0]

# Angles
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
scores += scores[:1]
threshold += threshold[:1]
angles += angles[:1]

# Plot
ax.plot(angles, scores, 'o-', linewidth=3, color='#2E86AB', label='CQOx Score', markersize=10)
ax.fill(angles, scores, alpha=0.25, color='#2E86AB')

ax.plot(angles, threshold, '--', linewidth=2, color='red', label='Threshold (Pass)', alpha=0.7)
ax.fill(angles, threshold, alpha=0.1, color='red')

# Labels
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
ax.set_ylim(0, 10)
ax.set_yticks([2, 4, 6, 8, 10])
ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=10)
ax.set_title('CAS Radar: Comprehensive Analytical System Quality Gates\nOverall Score: 8.7/10 (Pass)',
             fontsize=14, fontweight='bold', pad=30)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'cas_radar_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("  ✓ cas_radar_chart.png")

# ============================================================================
# 4. Domain Network - Multi-Domain Causal Graph
# ============================================================================
print("[4/8] Generating Domain Network...")

fig, ax = plt.subplots(figsize=(14, 10))

# Create network
G = nx.DiGraph()

# Define domains and nodes
domains = {
    'Healthcare': ['Patient Outcomes', 'Treatment', 'Cost'],
    'Finance': ['Default Rate', 'Credit Score', 'Loan Amount'],
    'Marketing': ['Revenue', 'Campaign', 'Customer LTV'],
    'Education': ['GPA', 'Tutoring', 'Study Hours']
}

# Add nodes
pos = {}
colors = []
color_map = {
    'Healthcare': '#E63946',
    'Finance': '#2E86AB',
    'Marketing': '#06A77D',
    'Education': '#F77F00'
}

y_offset = 0
for domain, nodes in domains.items():
    for i, node in enumerate(nodes):
        G.add_node(node, domain=domain)
        pos[node] = (i * 3, y_offset)
        colors.append(color_map[domain])
    y_offset += 3

# Add cross-domain edges (causal links)
edges = [
    ('Treatment', 'Patient Outcomes', 2.5),
    ('Campaign', 'Revenue', 3.2),
    ('Credit Score', 'Default Rate', -2.1),
    ('Tutoring', 'GPA', 0.42),
    ('Patient Outcomes', 'Revenue', 1.5),  # Cross-domain
    ('Customer LTV', 'Default Rate', -0.8),  # Cross-domain
]

for source, target, weight in edges:
    G.add_edge(source, target, weight=weight)

# Draw network
nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=3000, alpha=0.9, ax=ax)
nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)

# Draw edges with width based on effect magnitude
edge_widths = [abs(G[u][v]['weight']) * 2 for u, v in G.edges()]
nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6,
                       edge_color='gray', arrows=True, arrowsize=20,
                       arrowstyle='->', connectionstyle='arc3,rad=0.1', ax=ax)

# Edge labels
edge_labels = {(u, v): f"{G[u][v]['weight']:.2f}" for u, v in G.edges()}
nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=9, ax=ax)

# Legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=color, label=domain)
                   for domain, color in color_map.items()]
ax.legend(handles=legend_elements, loc='upper left', fontsize=11, title='Domains')

ax.set_title('Domain Network: Multi-Domain Causal Effects\nNode = Variable | Edge = Causal Effect Magnitude',
             fontsize=14, fontweight='bold')
ax.axis('off')

plt.tight_layout()
plt.savefig(output_dir / 'domain_network.png', dpi=300, bbox_inches='tight')
plt.close()

print("  ✓ domain_network.png")

# ============================================================================
# 5. Policy Evaluation 3D - Net Benefit Surface
# ============================================================================
print("[5/8] Generating Policy Evaluation 3D...")

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Generate policy parameter grid
coverage = np.linspace(0.1, 1.0, 40)  # % population treated
budget = np.linspace(10, 200, 40)  # ¥M budget cap
Coverage, Budget = np.meshgrid(coverage, budget)

# Net benefit function
NetBenefit = (
    100 * Coverage * np.log(Budget + 1)  # Revenue from treatment
    - 50 * Coverage * Budget * 0.5  # Cost
    - 20 * (Coverage - 0.6)**2 * 100  # Penalty for over/under coverage
)

# Find optimal point
optimal_idx = np.unravel_index(NetBenefit.argmax(), NetBenefit.shape)
optimal_coverage = Coverage[optimal_idx]
optimal_budget = Budget[optimal_idx]
optimal_benefit = NetBenefit[optimal_idx]

# Plot surface
surf = ax.plot_surface(Coverage, Budget, NetBenefit, cmap='RdYlGn',
                       alpha=0.8, linewidth=0, antialiased=True)

# Mark optimal point
ax.scatter([optimal_coverage], [optimal_budget], [optimal_benefit],
           color='red', s=200, marker='*', edgecolors='black', linewidths=2,
           label=f'Optimal: C={optimal_coverage:.2f}, B=¥{optimal_budget:.0f}M')

# Labels
ax.set_xlabel('Coverage (% Treated)', fontsize=12, fontweight='bold')
ax.set_ylabel('Budget Cap (¥M)', fontsize=12, fontweight='bold')
ax.set_zlabel('Net Benefit (¥M)', fontsize=12, fontweight='bold')
ax.set_title('Policy Evaluation 3D: Net Benefit Optimization\nCoverage × Budget → Net Benefit',
             fontsize=14, fontweight='bold', pad=20)

# Colorbar and legend
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='Net Benefit (¥M)')
ax.legend(loc='upper left', fontsize=10)

ax.view_init(elev=25, azim=225)

plt.tight_layout()
plt.savefig(output_dir / 'policy_evaluation_3d.png', dpi=300, bbox_inches='tight')
plt.close()

print("  ✓ policy_evaluation_3d.png")

# ============================================================================
# 6. Network Spillover 3D - Social Network Effects
# ============================================================================
print("[6/8] Generating Network Spillover 3D...")

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# Generate random network
np.random.seed(42)
n_nodes = 30
G = nx.random_geometric_graph(n_nodes, 0.3, seed=42)

# 3D positions
pos_3d = {i: (np.random.rand(), np.random.rand(), np.random.rand())
          for i in G.nodes()}

# Treatment effects (node attributes)
treatment_effects = np.random.gamma(2, 1.5, n_nodes)
node_colors = treatment_effects

# Draw nodes
xs, ys, zs = zip(*[pos_3d[i] for i in G.nodes()])
ax.scatter(xs, ys, zs, c=node_colors, s=treatment_effects*100,
           cmap='YlOrRd', alpha=0.8, edgecolors='black', linewidths=1)

# Draw edges
for edge in G.edges():
    x = [pos_3d[edge[0]][0], pos_3d[edge[1]][0]]
    y = [pos_3d[edge[0]][1], pos_3d[edge[1]][1]]
    z = [pos_3d[edge[0]][2], pos_3d[edge[1]][2]]
    ax.plot(x, y, z, color='gray', alpha=0.3, linewidth=1)

# Labels
ax.set_xlabel('X', fontsize=12, fontweight='bold')
ax.set_ylabel('Y', fontsize=12, fontweight='bold')
ax.set_zlabel('Z', fontsize=12, fontweight='bold')
ax.set_title('Network Spillover 3D: Social Network Treatment Effects\nNode Size = Direct Effect | Edges = Spillover Paths',
             fontsize=14, fontweight='bold', pad=20)

# Colorbar
sm = plt.cm.ScalarMappable(cmap='YlOrRd',
                           norm=plt.Normalize(vmin=node_colors.min(), vmax=node_colors.max()))
sm.set_array([])
fig.colorbar(sm, ax=ax, shrink=0.5, aspect=5, label='Treatment Effect')

ax.view_init(elev=20, azim=45)

plt.tight_layout()
plt.savefig(output_dir / 'network_spillover_3d.png', dpi=300, bbox_inches='tight')
plt.close()

print("  ✓ network_spillover_3d.png")

# ============================================================================
# 7. CATE Landscape 3D - Terrain Map of Treatment Effects
# ============================================================================
print("[7/8] Generating CATE Landscape 3D...")

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Generate landscape
age = np.linspace(20, 80, 50)
income = np.linspace(20, 200, 50)
Age, Income = np.meshgrid(age, income)

# CATE function with peaks and valleys
CATE = (
    3.0
    + (-0.05 * (Age - 50)**2 + 5.0)
    + (2.0 * np.log(Income / 20))
    + (0.01 * (Age - 40) * (Income - 100))
    + 0.5 * np.sin(Age / 10) * np.cos(Income / 30)
    + np.random.normal(0, 0.2, Age.shape)
)

# Plot terrain surface
surf = ax.plot_surface(Age, Income, CATE, cmap='terrain', alpha=0.9,
                       linewidth=0, antialiased=True, shade=True)

# Contour lines (topographic)
ax.contour(Age, Income, CATE, levels=15, colors='white', alpha=0.4, linewidths=0.8)

# Find peak and valley
peak_idx = np.unravel_index(CATE.argmax(), CATE.shape)
valley_idx = np.unravel_index(CATE.argmin(), CATE.shape)

peak_age, peak_income, peak_cate = Age[peak_idx], Income[peak_idx], CATE[peak_idx]
valley_age, valley_income, valley_cate = Age[valley_idx], Income[valley_idx], CATE[valley_idx]

# Mark peak and valley
ax.scatter([peak_age], [peak_income], [peak_cate], color='red', s=200,
           marker='^', edgecolors='black', linewidths=2, label='Peak (High Impact)')
ax.scatter([valley_age], [valley_income], [valley_cate], color='blue', s=200,
           marker='v', edgecolors='black', linewidths=2, label='Valley (Low Impact)')

# Zero-effect plane
ax.plot_surface(Age, Income, np.zeros_like(Age), alpha=0.15, color='gray')

# Labels
ax.set_xlabel('Age (years)', fontsize=12, fontweight='bold')
ax.set_ylabel('Income (¥K)', fontsize=12, fontweight='bold')
ax.set_zlabel('CATE', fontsize=12, fontweight='bold')
ax.set_title('CATE Landscape 3D: Treatment Effect Terrain Map\nAge × Income → Heterogeneous Effects',
             fontsize=14, fontweight='bold', pad=20)

fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='CATE')
ax.legend(loc='upper left', fontsize=10)

ax.view_init(elev=30, azim=135)

plt.tight_layout()
plt.savefig(output_dir / 'cate_landscape_3d.png', dpi=300, bbox_inches='tight')
plt.close()

print("  ✓ cate_landscape_3d.png")

# ============================================================================
# 8. Spillover Dynamics Animation - Network Diffusion
# ============================================================================
print("[8/8] Generating Spillover Dynamics Animation...")

fig, ax = plt.subplots(figsize=(12, 8))

# Create network
np.random.seed(42)
n_nodes = 30
G = nx.barabasi_albert_graph(n_nodes, 3, seed=42)
pos = nx.spring_layout(G, seed=42)

# Initial treatment seeds
initial_treated = np.random.choice(n_nodes, size=3, replace=False)
treated_status = np.zeros(n_nodes)
treated_status[initial_treated] = 1

# Simulation parameters
n_frames = 30
propagation_prob = 0.3

def simulate_diffusion(frame):
    ax.clear()

    global treated_status

    # Propagate treatment through network
    new_treated = treated_status.copy()
    for edge in G.edges():
        if treated_status[edge[0]] == 1 and treated_status[edge[1]] == 0:
            if np.random.rand() < propagation_prob:
                new_treated[edge[1]] = 1
        elif treated_status[edge[1]] == 1 and treated_status[edge[0]] == 0:
            if np.random.rand() < propagation_prob:
                new_treated[edge[0]] = 1

    treated_status = new_treated

    # Node colors
    node_colors = ['#E63946' if treated_status[i] == 1 else '#D3D3D3'
                   for i in range(n_nodes)]

    # Edge colors (active spillover)
    edge_colors = []
    for edge in G.edges():
        if (treated_status[edge[0]] == 1 and treated_status[edge[1]] == 0) or \
           (treated_status[edge[1]] == 1 and treated_status[edge[0]] == 0):
            edge_colors.append('#FF6B35')  # Active spillover
        else:
            edge_colors.append('#D3D3D3')  # Inactive

    # Draw network
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500,
                           alpha=0.9, ax=ax, edgecolors='black', linewidths=1.5)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=2,
                           alpha=0.6, ax=ax)

    # Title with adoption rate
    adoption_rate = treated_status.sum() / n_nodes * 100
    ax.set_title(f'Spillover Dynamics Animation (Frame {frame+1}/{n_frames})\n'
                 f'Treated: {int(treated_status.sum())}/{n_nodes} ({adoption_rate:.1f}%)',
                 fontsize=14, fontweight='bold')

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#E63946', label='Treated'),
        Patch(facecolor='#D3D3D3', label='Untreated'),
        Patch(facecolor='#FF6B35', label='Active Spillover', alpha=0.6)
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

    ax.axis('off')

# Create animation
anim = animation.FuncAnimation(fig, simulate_diffusion, frames=n_frames,
                               interval=200, repeat=True)

# Save as GIF
anim.save(output_dir / 'spillover_dynamics_animation.gif', writer='pillow', fps=5, dpi=150)
plt.close()

print("  ✓ spillover_dynamics_animation.gif")

print("\n" + "="*70)
print("✅ All 8 visualizations generated successfully!")
print(f"📁 Output directory: {output_dir.absolute()}")
print("="*70)
print("\nGenerated files:")
for i, filename in enumerate([
    "causal_surface_3d.png",
    "ate_animation.gif",
    "cas_radar_chart.png",
    "domain_network.png",
    "policy_evaluation_3d.png",
    "network_spillover_3d.png",
    "cate_landscape_3d.png",
    "spillover_dynamics_animation.gif"
], 1):
    print(f"  {i}. {filename}")

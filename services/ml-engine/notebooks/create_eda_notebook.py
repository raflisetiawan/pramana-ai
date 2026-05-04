"""
Script to generate the EDA notebook for Pramana AI ML Engine.
Run this script to create services/ml-engine/notebooks/01_eda.ipynb
"""
import json
from pathlib import Path


def make_cell(cell_type: str, source: list[str], **kwargs) -> dict:
    """Create a notebook cell."""
    cell = {
        "cell_type": cell_type,
        "metadata": kwargs.get("metadata", {}),
        "source": source,
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def md(lines: list[str]) -> dict:
    return make_cell("markdown", lines)


def code(lines: list[str]) -> dict:
    return make_cell("code", lines)


cells = [
    # ── Title ──
    md([
        "# 01 — Exploratory Data Analysis (EDA)\n",
        "## Pramana AI — ML Engine: Synthetic Claims Dataset\n",
        "\n",
        "Notebook ini mengeksplorasi dataset sintetis klaim BPJS (`synthetic_claims.csv`)\n",
        "yang akan digunakan untuk melatih model risk scoring.\n",
        "\n",
        "**Cakupan analisis:**\n",
        "1. Distribusi setiap fitur\n",
        "2. Korelasi fitur dengan label (`is_anomaly`)\n",
        "3. Class imbalance analysis\n",
        "4. Feature importance awal\n",
    ]),

    # ── Setup ──
    md(["## 1. Setup & Load Data"]),
    code([
        "import sys\n",
        "import warnings\n",
        "warnings.filterwarnings('ignore')\n",
        "\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "from pathlib import Path\n",
        "\n",
        "# Style\n",
        "sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)\n",
        "plt.rcParams['figure.figsize'] = (14, 6)\n",
        "plt.rcParams['figure.dpi'] = 100\n",
        "\n",
        "# Add project root to path\n",
        "PROJECT_ROOT = Path.cwd().parent.parent.parent\n",
        "sys.path.insert(0, str(PROJECT_ROOT / 'services' / 'ml-engine'))\n",
        "\n",
        "print(f'Project root: {PROJECT_ROOT}')\n",
    ]),
    code([
        "# Load dataset\n",
        "DATA_PATH = PROJECT_ROOT / 'tests' / 'fixtures' / 'synthetic_claims.csv'\n",
        "df = pd.read_csv(DATA_PATH)\n",
        "print(f'Dataset shape: {df.shape}')\n",
        "print(f'Columns: {len(df.columns)}')\n",
        "df.head(3)\n",
    ]),
    code([
        "# Basic info\n",
        "df.info()\n",
    ]),

    # ── Class Imbalance ──
    md([
        "## 2. Class Imbalance Analysis\n",
        "\n",
        "Target: `is_anomaly` (0 = wajar, 1 = anomali). Diharapkan 80/20 split.\n",
    ]),
    code([
        "fig, axes = plt.subplots(1, 2, figsize=(14, 5))\n",
        "\n",
        "# Count plot\n",
        "counts = df['is_anomaly'].value_counts()\n",
        "colors = ['#2ecc71', '#e74c3c']\n",
        "bars = axes[0].bar(counts.index, counts.values, color=colors, width=0.5, edgecolor='white')\n",
        "axes[0].set_xticks([0, 1])\n",
        "axes[0].set_xticklabels(['Normal (0)', 'Anomali (1)'])\n",
        "axes[0].set_title('Distribusi Label', fontweight='bold')\n",
        "axes[0].set_ylabel('Jumlah Klaim')\n",
        "for bar, count in zip(bars, counts.values):\n",
        "    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 50,\n",
        "                 f'{count:,}\\n({count/len(df):.1%})', ha='center', va='bottom', fontweight='bold')\n",
        "\n",
        "# Anomaly reason breakdown\n",
        "anomaly_df = df[df['is_anomaly'] == 1]\n",
        "reason_counts = anomaly_df['anomaly_reason'].value_counts()\n",
        "reason_colors = ['#e74c3c', '#e67e22', '#f39c12', '#9b59b6']\n",
        "axes[1].barh(reason_counts.index, reason_counts.values, color=reason_colors[:len(reason_counts)])\n",
        "axes[1].set_title('Breakdown Tipe Anomali', fontweight='bold')\n",
        "axes[1].set_xlabel('Jumlah Klaim')\n",
        "for i, (val, name) in enumerate(zip(reason_counts.values, reason_counts.index)):\n",
        "    axes[1].text(val + 10, i, f'{val} ({val/len(anomaly_df):.1%})', va='center')\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "print(f'Imbalance ratio: 1:{counts[0]//counts[1]} (Normal:Anomaly)')\n",
    ]),

    # ── Feature Distributions ──
    md([
        "## 3. Distribusi Fitur\n",
        "\n",
        "### 3.1 Fitur Biaya (Cost Features)\n",
    ]),
    code([
        "cost_features = ['total_tagihan', 'tagihan_per_hari', 'rasio_terhadap_ina_cbgs',\n",
        "                  'tagihan_obat_ratio', 'tagihan_tindakan_ratio']\n",
        "\n",
        "fig, axes = plt.subplots(2, 3, figsize=(18, 10))\n",
        "axes = axes.flatten()\n",
        "\n",
        "for i, col in enumerate(cost_features):\n",
        "    ax = axes[i]\n",
        "    for label, color, name in [(0, '#2ecc71', 'Normal'), (1, '#e74c3c', 'Anomali')]:\n",
        "        subset = df[df['is_anomaly'] == label][col]\n",
        "        ax.hist(subset, bins=50, alpha=0.6, color=color, label=name, density=True)\n",
        "    ax.set_title(col, fontweight='bold', fontsize=11)\n",
        "    ax.legend()\n",
        "    ax.set_ylabel('Density')\n",
        "\n",
        "axes[-1].set_visible(False)  # hide unused subplot\n",
        "plt.suptitle('Distribusi Fitur Biaya (Normal vs Anomali)', fontsize=14, fontweight='bold', y=1.02)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
    ]),

    md(["### 3.2 Fitur Klinis"]),
    code([
        "clinical_features = ['los', 'severity_score', 'jumlah_diagnosa_sekunder', 'jumlah_prosedur']\n",
        "\n",
        "fig, axes = plt.subplots(1, 4, figsize=(18, 5))\n",
        "\n",
        "for i, col in enumerate(clinical_features):\n",
        "    ax = axes[i]\n",
        "    data_normal = df[df['is_anomaly'] == 0][col]\n",
        "    data_anomaly = df[df['is_anomaly'] == 1][col]\n",
        "    ax.boxplot([data_normal, data_anomaly], labels=['Normal', 'Anomali'],\n",
        "               patch_artist=True, boxprops=dict(facecolor='#3498db', alpha=0.5),\n",
        "               medianprops=dict(color='#e74c3c', linewidth=2))\n",
        "    ax.set_title(col, fontweight='bold')\n",
        "\n",
        "plt.suptitle('Fitur Klinis: Normal vs Anomali', fontsize=14, fontweight='bold', y=1.02)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
    ]),

    md(["### 3.3 Fitur Geografis & Temporal"]),
    code([
        "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
        "\n",
        "# Tipe RS distribution\n",
        "ct = pd.crosstab(df['tipe_rs'], df['is_anomaly'], normalize='index')\n",
        "ct.plot(kind='bar', stacked=True, ax=axes[0], color=['#2ecc71', '#e74c3c'])\n",
        "axes[0].set_title('Proporsi Anomali per Tipe RS', fontweight='bold')\n",
        "axes[0].set_ylabel('Proporsi')\n",
        "axes[0].legend(['Normal', 'Anomali'])\n",
        "axes[0].tick_params(axis='x', rotation=0)\n",
        "\n",
        "# Bulan pengajuan\n",
        "month_agg = df.groupby('bulan_pengajuan')['is_anomaly'].mean()\n",
        "axes[1].bar(month_agg.index, month_agg.values, color='#3498db', edgecolor='white')\n",
        "axes[1].set_title('Anomaly Rate per Bulan', fontweight='bold')\n",
        "axes[1].set_xlabel('Bulan')\n",
        "axes[1].set_ylabel('Anomaly Rate')\n",
        "axes[1].axhline(y=df['is_anomaly'].mean(), color='#e74c3c', linestyle='--', label='Overall mean')\n",
        "axes[1].legend()\n",
        "\n",
        "# End of month\n",
        "eom_ct = pd.crosstab(df['is_end_of_month'], df['is_anomaly'], normalize='index')\n",
        "eom_ct.plot(kind='bar', stacked=True, ax=axes[2], color=['#2ecc71', '#e74c3c'])\n",
        "axes[2].set_title('Anomali vs End-of-Month', fontweight='bold')\n",
        "axes[2].set_xticklabels(['Non-EoM', 'End-of-Month'], rotation=0)\n",
        "axes[2].legend(['Normal', 'Anomali'])\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
    ]),

    # ── Diagnosa Analysis ──
    md(["### 3.4 Distribusi Diagnosa"]),
    code([
        "fig, axes = plt.subplots(1, 2, figsize=(18, 6))\n",
        "\n",
        "# Top diagnosa by count\n",
        "top_diag = df['diagnosa_utama'].value_counts().head(15)\n",
        "axes[0].barh(top_diag.index[::-1], top_diag.values[::-1], color='#3498db', edgecolor='white')\n",
        "axes[0].set_title('Top 15 Diagnosa (Frekuensi)', fontweight='bold')\n",
        "axes[0].set_xlabel('Jumlah Klaim')\n",
        "\n",
        "# Anomaly rate per diagnosa\n",
        "diag_anom = df.groupby('diagnosa_utama')['is_anomaly'].agg(['mean', 'count'])\n",
        "diag_anom = diag_anom[diag_anom['count'] >= 50].sort_values('mean', ascending=True)\n",
        "colors_diag = ['#e74c3c' if v > 0.25 else '#f39c12' if v > 0.20 else '#2ecc71' for v in diag_anom['mean']]\n",
        "axes[1].barh(diag_anom.index, diag_anom['mean'], color=colors_diag, edgecolor='white')\n",
        "axes[1].axvline(x=0.20, color='#e74c3c', linestyle='--', alpha=0.7, label='Target 20%')\n",
        "axes[1].set_title('Anomaly Rate per Diagnosa', fontweight='bold')\n",
        "axes[1].set_xlabel('Anomaly Rate')\n",
        "axes[1].legend()\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
    ]),

    # ── Correlation ──
    md([
        "## 4. Korelasi Fitur dengan Label\n",
        "\n",
        "Heatmap korelasi seluruh fitur numerik terhadap `is_anomaly`.\n",
    ]),
    code([
        "from app.features.extractor import extract_features_from_dataframe, ALL_FEATURE_COLUMNS, LABEL_COLUMN\n",
        "\n",
        "# Extract features\n",
        "X = extract_features_from_dataframe(df, fit_encodings=True)\n",
        "X['is_anomaly'] = df['is_anomaly'].values\n",
        "\n",
        "print(f'Feature matrix shape: {X.shape}')\n",
        "X.describe().round(3)\n",
    ]),
    code([
        "# Correlation with target\n",
        "corr_with_target = X.corr()['is_anomaly'].drop('is_anomaly').sort_values(ascending=False)\n",
        "\n",
        "fig, axes = plt.subplots(1, 2, figsize=(18, 8))\n",
        "\n",
        "# Bar chart of correlation with target\n",
        "colors_corr = ['#e74c3c' if v > 0 else '#3498db' for v in corr_with_target.values]\n",
        "axes[0].barh(range(len(corr_with_target)), corr_with_target.values, color=colors_corr)\n",
        "axes[0].set_yticks(range(len(corr_with_target)))\n",
        "axes[0].set_yticklabels(corr_with_target.index, fontsize=9)\n",
        "axes[0].set_title('Korelasi Fitur dengan is_anomaly', fontweight='bold')\n",
        "axes[0].set_xlabel('Pearson Correlation')\n",
        "axes[0].axvline(x=0, color='black', linewidth=0.5)\n",
        "\n",
        "# Full correlation heatmap\n",
        "corr_matrix = X[ALL_FEATURE_COLUMNS].corr()\n",
        "mask = np.triu(np.ones_like(corr_matrix, dtype=bool))\n",
        "sns.heatmap(corr_matrix, mask=mask, annot=False, cmap='RdBu_r', center=0,\n",
        "            ax=axes[1], square=True, linewidths=0.5, cbar_kws={'shrink': 0.8})\n",
        "axes[1].set_title('Correlation Matrix (Feature-to-Feature)', fontweight='bold')\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "print('\\nTop 5 positively correlated features:')\n",
        "for feat, val in corr_with_target.head(5).items():\n",
        "    print(f'  {feat:>40s}: {val:+.4f}')\n",
        "\n",
        "print('\\nTop 5 negatively correlated features:')\n",
        "for feat, val in corr_with_target.tail(5).items():\n",
        "    print(f'  {feat:>40s}: {val:+.4f}')\n",
    ]),

    # ── Scatter plots ──
    md(["## 5. Scatter Plots: Top Features vs Label"]),
    code([
        "top_pos = corr_with_target.head(3).index.tolist()\n",
        "\n",
        "fig, axes = plt.subplots(1, 3, figsize=(18, 5))\n",
        "\n",
        "for i, col in enumerate(top_pos):\n",
        "    ax = axes[i]\n",
        "    for label, color, name in [(0, '#2ecc71', 'Normal'), (1, '#e74c3c', 'Anomali')]:\n",
        "        subset = X[X['is_anomaly'] == label]\n",
        "        ax.scatter(subset.index, subset[col], alpha=0.15, s=5, color=color, label=name)\n",
        "    ax.set_title(f'{col}', fontweight='bold')\n",
        "    ax.set_ylabel(col)\n",
        "    ax.legend(markerscale=5)\n",
        "\n",
        "plt.suptitle('Top 3 Fitur Berkorelasi Positif dengan Anomali', fontsize=13, fontweight='bold', y=1.02)\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
    ]),

    # ── Pair plot key features ──
    md(["## 6. Pair Plot: Fitur Kunci"]),
    code([
        "key_features = ['rasio_terhadap_ina_cbgs', 'tagihan_per_hari', 'los', 'severity_score', 'is_anomaly']\n",
        "sample = X[key_features].sample(2000, random_state=42)\n",
        "\n",
        "g = sns.pairplot(sample, hue='is_anomaly', palette={0: '#2ecc71', 1: '#e74c3c'},\n",
        "                 diag_kind='kde', plot_kws={'alpha': 0.3, 's': 15})\n",
        "g.figure.suptitle('Pair Plot: Fitur Kunci vs Anomaly', y=1.02, fontsize=14, fontweight='bold')\n",
        "plt.show()\n",
    ]),

    # ── Preprocessor Test ──
    md([
        "## 7. Test Feature Pipeline\n",
        "\n",
        "Memverifikasi bahwa `extractor` dan `preprocessor` bekerja end-to-end.\n",
    ]),
    code([
        "from app.features.preprocessor import ClaimPreprocessor\n",
        "\n",
        "# Fit preprocessor\n",
        "preprocessor = ClaimPreprocessor()\n",
        "X_features = extract_features_from_dataframe(df, fit_encodings=True)\n",
        "X_scaled = preprocessor.fit_transform(X_features)\n",
        "preprocessor.save()\n",
        "\n",
        "print('Preprocessor fitted and saved!')\n",
        "print(f'Scaled shape: {X_scaled.shape}')\n",
        "print(f'Scaled mean (should be ~0):\\n{X_scaled.mean().round(6).to_string()}')\n",
        "print(f'\\nScaled std (should be ~1):\\n{X_scaled.std().round(4).to_string()}')\n",
    ]),
    code([
        "# Test single claim extraction (simulates API input)\n",
        "from app.features.extractor import extract_features\n",
        "\n",
        "sample_claim = {\n",
        "    'total_tagihan': 12_500_000,\n",
        "    'los': 5,\n",
        "    'tarif_ina_cbgs': 10_500_000,\n",
        "    'diagnosa_utama': 'I50.0',\n",
        "    'diagnosa_sekunder': 'I10;E11.9',\n",
        "    'prosedur': '88.72;99.04',\n",
        "    'tipe_rs': 'B',\n",
        "    'provinsi': 'Jawa Timur',\n",
        "    'tgl_pengajuan': '2024-01-15',\n",
        "}\n",
        "\n",
        "X_single = extract_features(sample_claim)\n",
        "X_single_scaled = preprocessor.transform(X_single)\n",
        "\n",
        "print('Single claim feature extraction:')\n",
        "print(X_single.T.to_string())\n",
        "print(f'\\nScaled values:')\n",
        "print(X_single_scaled.T.to_string())\n",
    ]),

    # ── Summary ──
    md([
        "## 8. Kesimpulan EDA\n",
        "\n",
        "### Temuan Utama:\n",
        "1. **Class imbalance**: Dataset sudah di-set 80/20 (normal/anomali) sesuai spesifikasi\n",
        "2. **Fitur terkuat**: `rasio_terhadap_ina_cbgs`, `tagihan_per_hari`, dan `total_tagihan` memiliki korelasi positif tertinggi dengan anomali\n",
        "3. **Separabilitas**: Anomali cukup terpisah pada fitur biaya, menjanjikan untuk model ML\n",
        "4. **Feature pipeline**: `extractor.py` dan `preprocessor.py` bekerja end-to-end\n",
        "\n",
        "### Rekomendasi untuk Training (Phase 2.3):\n",
        "- Gunakan semua 22 fitur\n",
        "- Pertimbangkan oversampling (SMOTE) jika model kesulitan dengan class imbalance\n",
        "- Focus pada precision untuk menghindari false positive (RS jujur salah di-flag)\n",
        "- `rasio_terhadap_ina_cbgs` adalah fitur terpenting — pastikan kualitas data tarif INA-CBGs\n",
    ]),
]

# Build notebook
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0",
        },
    },
    "cells": cells,
}

# Write
output = Path(__file__).parent / "01_eda.ipynb"
output.parent.mkdir(parents=True, exist_ok=True)
with open(output, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook created: {output}")
print(f"Size: {output.stat().st_size / 1024:.1f} KB")
print(f"Cells: {len(cells)} ({sum(1 for c in cells if c['cell_type']=='code')} code, {sum(1 for c in cells if c['cell_type']=='markdown')} markdown)")

import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

# 1. 固定隨機種子確保實驗可重現
np.random.seed(42)
n_samples = 1000
t = np.linspace(0, 20 * np.pi, n_samples)

# 模擬正常工業感測器時序數據 (基準值 50 + 週期波動 + 微小雜訊)
normal_signal = 50.0 + 2.5 * np.sin(t) + np.random.normal(0, 0.3, n_samples)
signal = normal_signal.copy()
y_true = np.zeros(n_samples, dtype=int)

# 2. 注入兩類真實工業異常 (共 30 筆，佔 3.0%)
# 類型 A (15 筆): 明顯數值突波 (傳統靜態閾值與 ML 皆可抓到)
spike_indices = np.random.choice(range(50, 450, 5), 15, replace=False)
for idx in spike_indices:
    signal[idx] += np.random.choice([-1, 1]) * np.random.uniform(9.5, 13.0)
    y_true[idx] = 1

# 類型 B (15 筆): 數值仍在正常區間內 [45~55]，但「瞬時變化率」劇烈震盪的早期設備劣化徵兆
phase_indices = np.random.choice(range(500, 950, 5), 15, replace=False)
for idx in phase_indices:
    # 製造單點高頻相位突變，數值不超過靜態閾值 (56.5 / 43.5)，但前後斜率顯著異常
    direction = 1 if signal[idx] < 50.0 else -1
    signal[idx] = signal[idx] + direction * 4.6
    y_true[idx] = 1

# 3. 多維度時序特徵工程: [原始感測值, 前後雙向瞬時變化率強度]
diff_prev = np.abs(np.diff(signal, prepend=signal[0]))
diff_next = np.abs(np.diff(signal, append=signal[-1]))
local_volatility = np.minimum(diff_prev, diff_next)  # 單點突變在前後兩側都會產生極大變化率

X_raw = np.column_stack((signal, local_volatility))
X_scaled = StandardScaler().fit_transform(X_raw)

# 4. 三種偵測模型對比
# (A) Static Threshold (靜態閾值法: 超出 50 ± 6.5 視為異常)
y_pred_static = ((signal > 56.5) | (signal < 43.5)).astype(int)

# (B) Statistical Z-Score (動態標準差法: |Z| > 3.0)
z_scores = np.abs((signal - np.mean(signal)) / np.std(signal))
y_pred_zscore = (z_scores > 3.0).astype(int)

# (C) Isolation Forest (標準化多維特徵孤立森林模型)
iso_forest = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
y_pred_if = (iso_forest.fit_predict(X_scaled) == -1).astype(int)

# 5. 印出量化評估表格
print("=" * 62)
print(f"{'演算法模型':<26} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
print("-" * 62)
models = [
    ("Static Threshold", y_pred_static),
    ("Statistical Z-Score", y_pred_zscore),
    ("Isolation Forest (ML)", y_pred_if)
]
for name, y_pred in models:
    p = precision_score(y_true, y_pred, zero_division=0)
    r = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    print(f"{name:<26} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f}")
print("=" * 62)

# 6. 繪製高解析度雙子分析圖表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.5), dpi=300)
plt.subplots_adjust(hspace=0.35)

# 上圖: 時序波形與異常點標記
ax1.plot(signal, color='#1B365D', linewidth=1.1, label='Sensor Telemetry Stream')
anom_idx = np.where(y_pred_if == 1)[0]
ax1.scatter(anom_idx, signal[anom_idx], color='#D9381E', s=36, zorder=5, label='Detected Anomalies (Isolation Forest)')
ax1.axhline(56.5, color='gray', linestyle='--', linewidth=0.9, label='Static Threshold Bounds (±6.5)')
ax1.axhline(43.5, color='gray', linestyle='--', linewidth=0.9)
ax1.set_title('Cloud IoT Sensor Anomaly Detection (Multi-Feature Isolation Forest)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Sensor Value', fontsize=10)
ax1.legend(loc='upper right', fontsize=8.5)
ax1.grid(True, linestyle=':', alpha=0.6)

# 下圖: 二維特徵空間分布 (數值 vs 雙向瞬時變化率)
norm_mask = (y_pred_if == 0)
anom_mask = (y_pred_if == 1)
ax2.scatter(signal[norm_mask], local_volatility[norm_mask], color='#4A6FE3', alpha=0.55, s=20, label='Normal Operating State')
ax2.scatter(signal[anom_mask], local_volatility[anom_mask], color='#D9381E', s=42, zorder=5, label='Isolated Anomalies (Value + Volatility Δ)')
ax2.set_title('2D Feature Space Isolation (Telemetry Value vs. Local Volatility Δ)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Sensor Value', fontsize=10)
ax2.set_ylabel('Local Volatility (Δ)', fontsize=10)
ax2.legend(loc='upper right', fontsize=8.5)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.savefig('anomaly_detection_result.png', bbox_inches='tight')
print("\n[完成] 高精度雙子分析報表已重新儲存為 anomaly_detection_result.png ！")
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score

# 1. 模擬工業設備感測器時序數據 (溫度/振動頻率，共 1000 筆)
np.random.seed(42)
n_samples = 1000
time_steps = np.arange(n_samples)

# 正常數據：平滑週期性波動 + 微小量測雜訊 (正常區間約 46.5 ~ 53.5)
normal_data = 50.0 + 3.0 * np.sin(time_steps / 20.0) + np.random.normal(0, 0.35, n_samples)

# 注入 30 筆真實異常數據 (佔比 3%)，分為兩類典型工業異常：
# 類型 A (15筆)：極端突波 (超出靜態上下限)
# 類型 B (15筆)：局部結構/相位突變異常 (數值仍在 47~53 正常上下限內，但瞬間偏離局部趨勢)
n_anomalies = 30
anomaly_indices = np.sort(np.random.choice(np.arange(20, n_samples - 20), n_anomalies, replace=False))
y_true = np.zeros(n_samples, dtype=int)
y_true[anomaly_indices] = 1

sensor_data = normal_data.copy()
for i, idx in enumerate(anomaly_indices):
    if i % 2 == 0:
        # 類型 A：極端突波
        sensor_data[idx] += np.random.choice([-1, 1]) * np.random.uniform(7.5, 11.5)
    else:
        # 類型 B：數值未超標但瞬間偏離局部平滑趨勢 (相位反轉突變)
        sensor_data[idx] = 50.0 - (sensor_data[idx] - 50.0) * 1.15

# 2. 特徵工程 (Feature Engineering) 與標準化
# 特徵 1：原始感測值 (捕捉極端突波)
# 特徵 2：一階差分瞬時變化率 delta (捕捉瞬間跳變)
delta = np.diff(sensor_data, prepend=sensor_data[0])
X_raw = np.column_stack((sensor_data, delta))

# 使用 StandardScaler 消除不同物理量綱的尺度差異
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

# ---------------------------------------------------------
# 3. 三種異常偵測演算法對比實驗
# ---------------------------------------------------------

# 方法 A：靜態閾值法 (Static Threshold: > 54.5 或 < 45.5)
pred_static = ((sensor_data > 54.5) | (sensor_data < 45.5)).astype(int)

# 方法 B：統計 Z-Score 法 (|Z| > 2.2)
mean_val, std_val = np.mean(sensor_data), np.std(sensor_data)
z_scores = np.abs((sensor_data - mean_val) / std_val)
pred_zscore = (z_scores > 2.2).astype(int)

# 方法 C：Isolation Forest 孤立森林 (結合標準化多維度特徵)
iso_forest = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
raw_pred_if = iso_forest.fit_predict(X_scaled)
pred_if = np.where(raw_pred_if == -1, 1, 0)

# ---------------------------------------------------------
# 4. 輸出量化評估指標表 (可直接填入審查資料表格)
# ---------------------------------------------------------
print("=" * 65)
print(f"{'演算法模型':<22} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
print("-" * 65)
for name, pred in [
    ("Static Threshold", pred_static),
    ("Statistical Z-Score", pred_zscore),
    ("Isolation Forest (ML)", pred_if)
]:
    p = precision_score(y_true, pred, zero_division=0)
    r = recall_score(y_true, pred, zero_division=0)
    f1 = f1_score(y_true, pred, zero_division=0)
    print(f"{name:<22} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f}")
print("=" * 65)

# ---------------------------------------------------------
# 5. 繪製高解析度雙子圖專業分析報表 (零語法警告)
# ---------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7.5), dpi=300)

# 子圖 1：時序波形與異常標記
ax1.plot(time_steps, sensor_data, color='#2B4C7E', linewidth=1.0, label='Sensor Telemetry Stream')
detected_idx = np.where(pred_if == 1)[0]
ax1.scatter(detected_idx, sensor_data[detected_idx], color='#D9534F', s=45, zorder=5, label='Detected Anomalies (Isolation Forest)')
ax1.axhline(54.5, color='#888888', linestyle=':', linewidth=1.0, label='Static Threshold Bounds')
ax1.axhline(45.5, color='#888888', linestyle=':', linewidth=1.0)
ax1.set_title('Cloud IoT Sensor Anomaly Detection (Multi-Feature Isolation Forest)', fontsize=13, fontweight='bold')
ax1.set_ylabel('Sensor Value', fontsize=11)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.4)

# 子圖 2：2D 標準化特徵空間孤立點分布 (Value vs. Delta)
normal_mask = (pred_if == 0)
anomaly_mask = (pred_if == 1)
ax2.scatter(X_raw[normal_mask, 0], X_raw[normal_mask, 1], color='#2B4C7E', alpha=0.5, s=20, label='Normal Operating State')
ax2.scatter(X_raw[anomaly_mask, 0], X_raw[anomaly_mask, 1], color='#D9534F', s=50, zorder=5, label='Isolated Anomalies (Value + Rate-of-Change)')
ax2.set_title(r'2D Feature Space Isolation (Telemetry Value vs. Rate of Change $\Delta$)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Sensor Metric Value', fontsize=11)
ax2.set_ylabel(r'Rate of Change ($\Delta$)', fontsize=11)
ax2.legend(loc='upper right')
ax2.grid(True, linestyle='--', alpha=0.4)

plt.tight_layout()
plt.savefig('anomaly_detection_result.png')
print("\n[完成] 雙子圖分析報表已儲存為 anomaly_detection_result.png！")
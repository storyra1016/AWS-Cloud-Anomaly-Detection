# 基於 AWS 無伺服器架構與機器學習之雲端異常偵測與自動化告警系統
**Cloud IoT Anomaly Detection & Automated Alerting System via AWS Serverless & Machine Learning**

## 📌 專案簡介 (Project Overview)
本專案針對工業物聯網（IIoT）與智慧監控情境，設計一套具備高可用性與零閒置成本的雲端異常偵測系統。系統結合無監督式機器學習演算法 **Isolation Forest（孤立森林）** 與 **AWS 無伺服器架構（Serverless Architecture）**，能即時分析感測器時序數據、自動識別異常突波，並同步完成雲端日誌歸檔與自動化告警通知。

---

## 🏗️ 系統架構流程 (System Architecture)
1. **數據模擬與演算法驗證 (`benchmark_experiment.py`)**：
   * 模擬 1,000 筆帶有週期性波動與高斯雜訊的工業感測器時序數據（含 3% 異常注入）。
   * 量化比較 **Static Threshold（靜態閾值法）**、**Statistical Z-Score** 與 **Isolation Forest** 之 Precision、Recall 與 F1-Score 表現。
2. **雲端事件驅動推論 (`lambda_function.py`)**：
   * 透過 **AWS Lambda** 接收感測器遙測數據（Telemetry Payload），執行輕量化異常評分推論。
3. **歷史數據歸檔 (`Amazon S3`)**：
   * 將每筆推論結果、異常評分與端到端延遲時間（End-to-End Latency）封裝為 JSON 格式，自動寫入 **Amazon S3** 儲存貯體進行長期留存。
4. **即時自動化告警 (`Amazon SNS`)**：
   * 當異常評分超過設定閾值（`score >= 0.85`）時，自動觸發 **Amazon SNS** 發送即時電子郵件告警通知。

---

## 📂 檔案結構說明 (Repository Structure)
| 檔案名稱 | 功能說明 |
| :--- | :--- |
| `benchmark_experiment.py` | 本地端感測器數據模擬、三種異常偵測演算法量化評估與波形圖繪製腳本 |
| `lambda_function.py` | 部署於 AWS Lambda 之無伺服器推論核心，整合 S3 歸檔與 SNS 告警邏輯 |
| `anomaly_detection_result.png` | 演算法偵測結果高解析度時序波形圖 |
| `README.md` | 專案架構、技術規格與執行說明文件 |

---

## 🚀 本地端實驗執行方式 (Local Benchmark Execution)
1. 安裝所需 Python 科學運算與視覺化套件：
   ```bash
   pip install numpy scikit-learn matplotlib
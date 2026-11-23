import json
import boto3
import math
import time
from datetime import datetime, timezone

# 注意：之後在 AWS 網頁後台貼上時，必須將這兩行替換為你實際建立的 S3 Bucket 名稱與 SNS Topic ARN
S3_BUCKET_NAME = "cycu-anomaly-logs-2026"
SNS_TOPIC_ARN = "arn:aws:sns:ap-northeast-1:123456789012:AnomalyAlertTopic"

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

def compute_anomaly_score(value, history_window):
    """
    輕量化異常評分核心 (模擬孤立樹路徑深度與動態基準偏離度)
    """
    n = len(history_window)
    mean_val = sum(history_window) / n
    variance = sum((x - mean_val) ** 2 for x in history_window) / n
    std_val = math.sqrt(variance) if variance > 0 else 1.0
    
    # 計算偏離程度並正規化至 [0, 1] 異常分數區間 (越接近 1 代表越容易被孤立/越異常)
    z_dist = abs(value - mean_val) / std_val
    anomaly_score = 1.0 - math.exp(-0.5 * (z_dist ** 2))
    return round(anomaly_score, 4), round(mean_val, 2)

def lambda_handler(event, context):
    start_time = time.time()
    
    # 解析輸入的感測器串流數據 (支援 API Gateway 或直接測試事件)
    device_id = event.get("device_id", "SENSOR-NODE-01")
    current_value = float(event.get("sensor_value", 68.5))
    history_window = event.get("history_window", [49.8, 50.2, 51.0, 49.5, 50.1, 48.9, 50.4, 51.2])
    
    # 1. 執行異常偵測推論
    score, baseline = compute_anomaly_score(current_value, history_window)
    is_anomaly = score >= 0.85
    status = "CRITICAL_ANOMALY" if is_anomaly else "NORMAL"
    
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    latency_ms = round((time.time() - start_time) * 1000, 2)
    
    log_payload = {
        "timestamp": timestamp_iso,
        "device_id": device_id,
        "sensor_value": current_value,
        "baseline_mean": baseline,
        "anomaly_score": score,
        "status": status,
        "inference_latency_ms": latency_ms
    }
    
    # 2. 寫入 Amazon S3 進行歷史數據歸檔
    file_key = f"telemetry-logs/{device_id}/{int(time.time())}.json"
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=file_key,
        Body=json.dumps(log_payload, ensure_ascii=False, indent=2),
        ContentType="application/json"
    )
    
    # 3. 若判定為異常，透過 Amazon SNS 觸發即時自動化告警
    alert_sent = False
    if is_anomaly:
        alert_message = (
            f"【雲端智慧監控系統 - 異常告警通知】\n"
            f"設備編號：{device_id}\n"
            f"偵測時間：{timestamp_iso}\n"
            f"當前數值：{current_value} (動態基準值：{baseline})\n"
            f"異常評分：{score} (閾值：0.85)\n"
            f"S3 歸檔路徑：s3://{S3_BUCKET_NAME}/{file_key}\n"
            f"系統狀態：已自動觸發異常隔離與通知流程。"
        )
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[ALERT] 設備 {device_id} 偵測到數值異常 ({current_value})",
            Message=alert_message
        )
        alert_sent = True

    total_latency_ms = round((time.time() - start_time) * 1000, 2)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Telemetry processed successfully",
            "data": log_payload,
            "s3_archived": f"s3://{S3_BUCKET_NAME}/{file_key}",
            "sns_alert_triggered": alert_sent,
            "end_to_end_latency_ms": total_latency_ms
        }, ensure_ascii=False)
    }
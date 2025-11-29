모델 Training 단계
1) YAMNet Embeddings 추출
    train_embeddings.py
    출력:
	•	X.npy (1024차원 embedding)
	•	y.npy (0=negative, 1=positive)

2) Binary Classifier 학습 (추천: Linear SVM + calibrated probability)
    train_classifier.py
    출력:
	•	classifier.pkl
	•	scaler.pkl (선택)

3) 실시간 감지
    realtime_detector.py
    결과 예시:
    [2025-…] HUMAN_EVENT=True Prob=0.93 RMS=0.21
    [2025-…] HUMAN_EVENT=False Prob=0.08 RMS=0.01

요구사항 → binary human-event detector

✔️ sniff 제외
✔️ cough+sneeze+snore = positive
✔️ 나머지 = negative
✔️ SVM 기반 → 가장 안전하고 정확함
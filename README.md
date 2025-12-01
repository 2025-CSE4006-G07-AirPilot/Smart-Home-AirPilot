# PuriPilot Project
AI 기반 예측형 스마트 홈 공기질 제어 시스템

PuriPilot은 Edge AI, Kafka 스트림, Supabase Room Graph, Predictive Control을 결합해 집 전체 공기청정기를 사전에 제어하는 스마트홈 자동화 시스템입니다.

## ⭐ 프로젝트 목표

- 사람의 기침, 재채기, 코골이 감지
- 현재 + 미래 공기질 분석
- Room Graph 기반 실내 공기 흐름 구조 파악
- 오염될 방을 사전에 강풍으로 제어하는 Predictive Smart Control 구현

## ⭐ 전체 아키텍처

```
[Edge Device]
├─ Telemetry (PM25/VOC/CO2)
├─ Human Events (cough/sneeze/snore)
├─ Prediction (10/30min AQ forecast)
↓
Kafka Topics
(telemetry-events / human-events / prediction-events)
↓
[Backend API]
	•	인증, CRUD
	•	Room Graph 관리
↓
[Supabase]
	•	house_graphs
	•	telemetry
	•	human_events
	•	predictions
	•	recommendations
↓
[Worker]
	•	Kafka Consumer 통합 처리
	•	Predictive Control (fanLevel 결정 → Supabase)
↓
[Frontend]
	•	Room Graph Editor
	•	실시간 Dashboard
	•	Fan Level 적용 UI

```

## 디렉토리 구조
```
PuriPilot/
├── backend-api/          # FastAPI (Room Graph / Supabase / Kafka)
├── edge/                 # Edge AI (휴먼 이벤트 + Telemetry)
│   ├── human-event/      # YAMNet 임베딩 + Binary Classifier
│   ├── prediction/       # 예측 모델 (준비중)
│   └── telemetry/        # 센서 데이터 수집기
├── frontend/             # Next.js (Graph Editor + Dashboard)
├── kafka/                # Kafka 설정 및 토픽
├── supabase/             # DB schema, RLS, migrations
├── worker/               # Kafka Consumer + Predictive Control
└── docs/                 # 설계 문서/아키텍처 노트
```

## Edge Human Event Detection

### 목표
- Positive: cough, sneeze, snore
- Negative: 그 외 모든 생활 소리
- Multi-class보다 성능이 높은 Binary Classifier 전략 사용

### 구성 요소
```
edge/human-event/
├── datasets/
│   ├── positive/     # cough + sneeze + snore
│   └── negative/     # 생활소음
├── train_embeddings.py     # YAMNet → 1024 embedding 생성
├── train_classifier.py     # SVM / RF binary classifier 학습
├── embeddings/             # X.npy / y.npy
├── models/                 # classifier.pkl
└── realtime_detector.py    # 마이크 실시간 감지기
```

## 데이터 흐름
```
[Mic]
→ YAMNet Embedding
→ Classifier (Positive/Negative)
→ backend-api POST
→ Kafka
→ Worker
→ Supabase.recommendations
→ Frontend Dashboard
```

## Supabase 데이터 스키마

테이블 목록:
- house_graphs
- rooms
- edges
- telemetry_events
- human_events
- prediction_events
- recommendations

Kafka 토픽:
- telemetry-events
- human-events
- prediction-events
- recommendation-events (optional)

## 스프린트 진행 계획 (Project 참고)

### Sprint 0 — 설계 단계
[목표]
- 시스템 기초 구조 확립

[해야 할 것]
- 프로젝트 스코프 확정
- Supabase schema 확정 및 적용
- API 명세 통일
- Kafka Topic 생성
- Binary Human Event Detector 구축
- Positive/Negative dataset 구성
- train_embeddings.py
- train_classifier.py
- realtime_detector.py 테스트

[완료 기준]
- Edge → Backend → Kafka end-to-end 연결

### Sprint 1 — Graph + API 기본 구축
[목표]
- Room Graph 기능 구축

[해야 할 것]
- Backend: Graph GET/POST 완성
- Frontend: Room Graph Editor UI 기본 구성
- Edge: Telemetry/Human/Prediction 더미 이벤트
- Test: Graph 저장/불러오기 e2e 확인

[완료 기준]
- Frontend ↔ Backend ↔ Supabase 저장/로드 정상 작동

### Sprint 2 — Kafka Producer + Edge 이벤트

[목표]
- Edge → Backend → Kafka 데이터 흐름 구축

[해야 할 것]
- Kafka Producer 완성
- Edge 이벤트 자동 POST
- Kafka 메시지 정상 적재 확인
- Frontend Dashboard 기본 구성

[완료 기준]
- 3종 Kafka 스트림이 정상적으로 들어와 대시보드 반영

### Sprint 3 — Predictive Control + Worker

[목표]
- fanLevel 자동 추천 기능 완성

[해야 할 것]
- Worker: Kafka Consumer 통합
- Predictive Control 로직 구현
- Supabase recommendations 저장
- Frontend: fanLevel 실시간 반영

[완료 기준]
- 예측 기반 fanLevel 제어가 전체 시스템에서 동작

### Final Sprint — Polish + Demo

[목표]
- 데모 완성과 안정화

[해야 할 것]
- 오류 수정
- UI 마감
- 전체 End-to-End 테스트
- 발표 자료 완성

## Quick Start

1) Supabase
```
cd supabase
supabase start
psql < schema.sql
```
2) Kafka
```
cd kafka
docker-compose up -d
```
3) Backend
```
uvicorn app:app --reload
```
4) Edge Human Event Detector
```
cd edge/human-event
python train_embeddings.py
python train_classifier.py
python realtime_detector.py
```
5) Frontend
```
npm install
npm run dev
```
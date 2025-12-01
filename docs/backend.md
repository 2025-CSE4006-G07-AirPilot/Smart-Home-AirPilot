## ⭐️ Room/Edge/Device SQLModel는 전부 app/models 아래에 둘 거임.

- Room / Edge / Device SQLModel 정의는 `app/models/` 아래 각각 파일로 저장.
- DB 엔진/세션은 `app/core/db.py`.
- FastAPI 시작점은 `app/main.py`, 여기서 `init_db()` 호출 + 라우터 등록.
- 나중에 ESP32/HTTP 통신 로직은 `routers/devices.py` + `services/devices.py`에 미리 분리하면 MQTT로 바꾸기도 쉬움.

## ⭐️ Device 전용 “모드만 바꾸는 API” (POST /devices/{id}/mode)
### 왜 필요한지 ?
- 기존 `PUT /devices/{id}`는 `room_id`, `name`, `mode`, `smell_class`, `last_seen` 전부를 한 번에 보내야 함.
- 근데 웹에서 사용자가 하는 일은 대부분: “이 기기 모드만 HIGH로 바꿔줘” 같은 단순 모드 변경.
- 그래서 “모드만 바꾸는 전용 엔드포인트”를 만들면, 프론트엔드 코드가 단순해지고 실수로 다른 필드를 덮어쓸 위험이 줄어듦.

### 포인트:
- DeviceModeUpdate는 mode만 포함하는 Pydantic 모델 → “모드만 바꿀게”라는 의도가 분명해짐.
- last_seen도 같이 갱신하면 “최근에 서버와 통신한 시간”이 유지된다.

## ⭐️ ESP32 상태 보고용 API (last_seen 자동 업데이트)
### 왜 필요한지 ?
- ESP32는 주기적으로: “나는 device‑1이고, 지금 모드는 NORMAL, 냄새 클래스는 BAD야” 같은 상태를 서버에 보내줘야 한다.
- 이때 `last_seen`을 ESP32가 직접 보내도록 만들면: 보드 시간이 틀어져 있거나 타임존/포맷이 꼬일 수 있음.
- 서버가 요청을 받은 시점의 시간을 기준으로 `last_seen`을 찍어주는 게 더 정확하고 단순하다.

### 그래서:
- ESP32는 `room_id`, `name`, `mode`, `smell_class`만 보내고,
- 서버는
    - 해당 id의 Device가 있으면 업데이트,
    - 없으면 새로 생성(선택),
    - 그리고 `last_seen = datetime.utcnow()`로 자동 기록.

## ⭐️ /devices에서 왜 두 API를 두는지 정리
### `/devices/{id}/mode` (웹용)
- 사람이 웹에서 수동으로 모드를 바꾸는 전용 채널.
- 프론트엔드 동작: 사용자 인터랙션 → 이 엔드포인트에 요청 → Device 모드 변경.

### `/devices/report` (ESP32용)
- ESP32가 주기적으로 자기 상태를 서버에 알려주는 채널.
- 센서/제어 로직은 ESP32에서 돌아가고,
- 서버는 그 결과(현재 모드, 냄새 클래스, last_seen)를 DB에 저장해서 대시보드에서 보여주고, Room‑Graph 기반으로 추가 로직을 결정.

역할을 분리해두면:
- “사람이 모드를 강제로 바꾸는 것”과
- “센서/로직이 자동으로 모드를 바꾼 결과를 보고하는 것”이 섞이지 않아서,
- 코드와 구조를 이해하거나 디버깅할 때 훨씬 쉽다.


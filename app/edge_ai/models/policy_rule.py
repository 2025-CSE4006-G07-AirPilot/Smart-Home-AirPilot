# app/edge_ai/models/policy_rule.py
from app.edge_ai.schemas.control import (
    State, Preference, Control, TempMode, HumidMode,
)
from app.edge_ai.schemas.profile import DeviceProfile

def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))

def decide_control_rule(
    state: State,
    pref: Preference,
    profile: DeviceProfile,
) -> Control:
    # 1) 온도
    temp_target = (
        pref.temp_target
        if pref.temp_pref == "set" and pref.temp_target is not None
        else profile.temp_target
    )
    dT = state.temperature - temp_target

    bc = profile.temp_band_comfort
    bm = profile.temp_band_mild
    bs = profile.temp_band_strong

    if -bc <= dT <= bc:
        temp_mode: TempMode = "OFF"
        temp_level = 0
    elif dT > bc:
        temp_mode = "COOL"
        if dT <= bm:        temp_level = 2
        elif dT <= bs:      temp_level = 3
        elif dT <= bs + 2:  temp_level = 4
        else:               temp_level = 5
    else:
        temp_mode = "HEAT"
        if -dT <= bm:       temp_level = 2
        elif -dT <= bs:     temp_level = 3
        elif -dT <= bs + 2: temp_level = 4
        else:               temp_level = 5

    # 2) 습도
    humid_target = (
        pref.humid_target
        if pref.humid_pref == "set" and pref.humid_target is not None
        else profile.humid_target
    )
    dH = state.humidity - humid_target

    hc = profile.humid_band_comfort
    hm = profile.humid_band_mild
    hs = profile.humid_band_strong

    if -hc <= dH <= hc:
        humid_mode: HumidMode = "OFF"
        humid_level = 0
    elif dH > hc:
        humid_mode = "DEHUMID"
        if dH <= hm:        humid_level = 2
        elif dH <= hs:      humid_level = 3
        elif dH <= hs + 10: humid_level = 4
        else:               humid_level = 5
    else:
        humid_mode = "HUMID"
        if -dH <= hm:       humid_level = 2
        elif -dH <= hs:     humid_level = 3
        elif -dH <= hs + 10:humid_level = 4
        else:               humid_level = 5

    # 3) 공기질 → 팬 세기
    pm25_norm = max(0.0, min(1.0, (state.pm25 - 10) / 40))
    co2_norm  = max(0.0, min(1.0, (state.co2  - 800) / 800))
    tvoc_norm = max(0.0, min(1.0, state.tvoc))
    odor_norm = max(0.0, min(1.0, state.odor))

    w_sum = profile.w_pm25 + profile.w_co2 + profile.w_tvoc + profile.w_odor
    if w_sum <= 0:
        w_sum = 1.0

    air_score = (
        profile.w_pm25 * pm25_norm +
        profile.w_co2  * co2_norm +
        profile.w_tvoc * tvoc_norm +
        profile.w_odor * odor_norm
    ) / w_sum

    if air_score < 0.1:   fan_level = 1
    elif air_score < 0.3: fan_level = 2
    elif air_score < 0.5: fan_level = 3
    elif air_score < 0.7: fan_level = 4
    else:                 fan_level = 5

    fan_level = _clamp(fan_level + profile.fan_bias, 1, 5)

    return Control(
        fan_level=fan_level,
        temp_mode=temp_mode,
        temp_level=temp_level,
        humid_mode=humid_mode,
        humid_level=humid_level,
        duration_sec=600,
    )

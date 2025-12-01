# app/edge_ai/services/feedback_service.py
from app.edge_ai.schemas.feedback import Feedback
from app.edge_ai.schemas.profile import DeviceProfile
from app.edge_ai.core.profile_store import load_profile, save_profile

def _update_profile_with_feedback(
    profile: DeviceProfile,
    fb: Feedback,
) -> DeviceProfile:
    # 팬 세기 override
    if fb.user_overridden and fb.user_final_fan_level is not None:
        delta_fan = fb.user_final_fan_level - fb.control_applied.fan_level
        if delta_fan < 0:
            profile.fan_bias = max(-2, profile.fan_bias - 1)
        elif delta_fan > 0:
            profile.fan_bias = min(2, profile.fan_bias + 1)

    # 온도/습도 타겟 조정 (유저가 명시적으로 바꿨다면 조금 따라감)
    if fb.user_final_temp_target is not None:
        profile.temp_target = (
            0.8 * profile.temp_target + 0.2 * fb.user_final_temp_target
        )
    if fb.user_final_humid_target is not None:
        profile.humid_target = (
            0.8 * profile.humid_target + 0.2 * fb.user_final_humid_target
        )

    profile.overrides_count += 1
    return profile

def apply_feedback(fb: Feedback) -> DeviceProfile:
    profile = load_profile(fb.device_id)
    profile = _update_profile_with_feedback(profile, fb)
    save_profile(profile)
    return profile

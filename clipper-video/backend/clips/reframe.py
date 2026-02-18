import cv2
import logging
import statistics
from typing import Optional, Tuple


Aspect = 9 / 16
LOGGER = logging.getLogger(__name__)


def _get_target_crop_size(frame_w: float, frame_h: float, person_w: float, person_h: float):
    """
    Hitung ukuran crop 9:16 yang cukup menampung bounding person + margin,
    lalu clamp ke batas frame.
    """
    margin = 1.2
    pw = person_w * margin
    ph = person_h * margin

    # Pastikan aspect 9:16 dan cukup untuk person box
    crop_w = max(pw, Aspect * ph)
    crop_h = crop_w / Aspect
    if crop_h < ph:
        crop_h = ph
        crop_w = crop_h * Aspect

    # Clamp ke ukuran frame
    scale = min(1.0, frame_w / crop_w, frame_h / crop_h)
    crop_w *= scale
    crop_h *= scale
    return crop_w, crop_h


def compute_dominant_person_crop(
    video_path: str,
    sample_fps: float = 2.0,
    min_visibility: float = 0.45,
    min_height_ratio: float = 0.22,
    debug: bool = False,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Balikkan (crop_x, crop_y, crop_w, crop_h) untuk portrait 9:16
    yang mengikuti orang paling dominan di video.
    """
    try:
        import mediapipe as mp
    except Exception as exc:
        if debug:
            LOGGER.warning("reframe: mediapipe import failed: %s", exc)
        return None

    if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "pose"):
        if debug:
            LOGGER.warning("reframe: mediapipe.solutions.pose not available")
        return None

    torso_landmarks = [
        mp.solutions.pose.PoseLandmark.NOSE,
        mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
        mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
        mp.solutions.pose.PoseLandmark.LEFT_HIP,
        mp.solutions.pose.PoseLandmark.RIGHT_HIP,
    ] if hasattr(mp.solutions.pose, 'PoseLandmark') else [
        0,  # NOSE
        11, # LEFT_SHOULDER
        12, # RIGHT_SHOULDER
        23, # LEFT_HIP
        24, # RIGHT_HIP
    ]

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        if debug:
            LOGGER.warning("reframe: failed to open video: %s", video_path)
        return None

    frame_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    frame_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    step = max(1, int(round(fps / sample_fps)))

    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    centers_x, centers_y, widths, heights, visibilities = [], [], [], [], []
    frame_idx = 0
    sampled = 0
    success, frame = cap.read()
    while success:
        if frame_idx % step == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)
            if result.pose_landmarks:
                xs, ys, vs = [], [], []
                for lm_id in torso_landmarks:
                    # Handle both enum and integer landmark IDs
                    if hasattr(mp.solutions.pose, 'PoseLandmark'):
                        landmark_enum = lm_id
                        lm = result.pose_landmarks.landmark[landmark_enum]
                    else:
                        landmark_idx = lm_id
                        lm = result.pose_landmarks.landmark[landmark_idx]
                    if lm.visibility < min_visibility:
                        continue
                    xs.append(lm.x)
                    ys.append(lm.y)
                    vs.append(lm.visibility)
                if len(xs) < 3:
                    frame_idx += 1
                    success, frame = cap.read()
                    continue
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                w = (max_x - min_x) * frame_w
                h = (max_y - min_y) * frame_h
                cx = (min_x + max_x) * 0.5 * frame_w
                cy = (min_y + max_y) * 0.5 * frame_h
                if w > 1 and h > 1:
                    centers_x.append(cx)
                    centers_y.append(cy)
                    widths.append(w)
                    heights.append(h)
                    visibilities.append(statistics.mean(vs))
                    sampled += 1
        frame_idx += 1
        success, frame = cap.read()

    cap.release()
    pose.close()

    if not centers_x:
        if debug:
            LOGGER.info("reframe: no pose detections for %s", video_path)
        return None

    center_x = statistics.median(centers_x)
    center_y = statistics.median(centers_y)
    person_w = statistics.median(widths)
    person_h = statistics.median(heights)
    visibility = statistics.median(visibilities)

    if person_h < frame_h * min_height_ratio:
        if debug:
            LOGGER.info(
                "reframe: detection too small (h=%.1f, frame_h=%.1f) for %s",
                person_h,
                frame_h,
                video_path,
            )
        return None
    if visibility < min_visibility:
        if debug:
            LOGGER.info(
                "reframe: low visibility (%.2f) for %s",
                visibility,
                video_path,
            )
        return None

    crop_w, crop_h = _get_target_crop_size(frame_w, frame_h, person_w, person_h)
    crop_x = center_x - crop_w / 2
    crop_y = center_y - crop_h / 2

    crop_x = max(0, min(crop_x, frame_w - crop_w))
    crop_y = max(0, min(crop_y, frame_h - crop_h))

    if debug:
        LOGGER.info(
            "reframe: samples=%d center=(%.1f,%.1f) person=(%.1fx%.1f) crop=(%d,%d,%d,%d)",
            sampled,
            center_x,
            center_y,
            person_w,
            person_h,
            int(round(crop_x)),
            int(round(crop_y)),
            int(round(crop_w)),
            int(round(crop_h)),
        )

    return (
        int(round(crop_x)),
        int(round(crop_y)),
        int(round(crop_w)),
        int(round(crop_h)),
    )

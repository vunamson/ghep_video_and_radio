import sys
import random
from pathlib import Path
from typing import List
import cv2
import numpy as np
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_audioclips,
    concatenate_videoclips
)

# ==========================================================
#                    ⚙️ CẤU HÌNH THƯ MỤC
# ==========================================================
AUDIO_DIR = r"C:\Youtobe\audio youtobe\Ngày 15-11-2025"
VIDEO_OPENING = r"C:\Youtobe\video youtobe\Video mở đầu"
VIDEO_MAIN = r"C:\Youtobe\video youtobe\Video tổng hợp"
VIDEO_ENDING = r"C:\Youtobe\video youtobe\Video kết thúc"
OUTPUT_DIR = r"C:\Youtobe\output video youtobe\Ngày 15-11-2025"
ORIG_AUDIO_DIRNAME = "_original_audio"

# ==========================================================
#                     🎞️ CẤU HÌNH VIDEO
# ==========================================================
TARGET_W = 1920
TARGET_H = 1080

VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
BITRATE = "6M"
PRESET = "medium"
CRF = 18

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}

# ==========================================================
#                    🔧 HÀM HỖ TRỢ
# ==========================================================

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def scan(folder: Path, allowed_exts):
    return sorted(
        [p for p in folder.glob("*") if p.is_file() and p.suffix.lower() in allowed_exts],
        key=lambda x: x.name.lower()
    )

def safe_resize(clip):
    """Resize video thành 1920x1080 bằng OpenCV."""
    def resize_frame(frame):
        h, w, _ = frame.shape
        target_ratio = TARGET_W / TARGET_H
        clip_ratio = w / h

        if clip_ratio < target_ratio:
            new_h = TARGET_H
            new_w = int(clip_ratio * new_h)
        else:
            new_w = TARGET_W
            new_h = int(new_w / clip_ratio)

        frame_resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        canvas = np.zeros((TARGET_H, TARGET_W, 3), dtype=np.uint8)

        x = (TARGET_W - new_w) // 2
        y = (TARGET_H - new_h) // 2
        canvas[y:y+new_h, x:x+new_w] = frame_resized
        return canvas

    return clip.fl_image(resize_frame)

def extract_original_audio(video_clip: VideoFileClip, out_path: Path):
    if video_clip.audio is None:
        return
    video_clip.audio.write_audiofile(str(out_path), verbose=False, logger=None)

# ==========================================================
#           🔊 GHÉP TẤT CẢ AUDIO THÀNH 1 FILE
# ==========================================================

def merge_all_audio(audio_files: List[Path], out_path: Path) -> float:
    print("\n🔊 Ghép tất cả audio...")

    clips = []
    for p in audio_files:
        try:
            clips.append(AudioFileClip(str(p)))
            print(f"  + {p.name}")
        except:
            print(f"  ⚠ Không đọc được: {p.name}")

    final = concatenate_audioclips(clips)
    final.write_audiofile(str(out_path), verbose=False, logger=None)
    duration = final.duration

    final.close()
    for c in clips:
        c.close()

    return duration

# ==========================================================
#        🎬 CHỌN DANH SÁCH MAIN VIDEO TỐI ƯU
# ==========================================================

def pick_main_video_sequence(main_files, total_audio_len):
    """Random trước danh sách video đủ để đạt thời lượng audio."""
    selected = []
    duration_sum = 0
    last_name = None

    print("  • Chọn danh sách video Main:")

    random.shuffle(main_files)

    for choice in main_files:
        if duration_sum >= total_audio_len:
            break

        if choice.name == last_name:
            continue

        try:
            mv = VideoFileClip(str(choice))
            d = mv.duration
            mv.close()
        except:
            print(f"  ⚠ Lỗi đọc: {choice.name}")
            continue

        print(f"     + {choice.name} ({d:.1f}s)")
        selected.append(choice)
        duration_sum += d
        last_name = choice.name

    return selected

# ==========================================================
#        🎬 GHÉP VIDEO OPENING → MAIN → ENDING
# ==========================================================

def build_video(opening_files, main_files, ending_files, total_audio_len, orig_audio_root: Path):
    print("\n🎬 Bắt đầu ghép video...")

    clips_ready = []

    # 1️⃣ Opening
    opening = random.choice(opening_files)
    print(f"  • Opening: {opening.name}")

    vo = VideoFileClip(str(opening))
    vo = safe_resize(vo)
    extract_original_audio(vo, orig_audio_root / f"{opening.stem}.wav")
    clips_ready.append(vo.without_audio())
    vo.close()

    # 2️⃣ Main videos – loop đến khi đủ audio, nhưng không cho 2 video giống nhau cạnh nhau
    print("  • Main videos (looping, no duplicates next to each other):")

    main_duration = 0
    last_name = None  # lưu video trước đó

    while main_duration < total_audio_len:
        mv_path = random.choice(main_files)

        # ❌ Nếu trùng video ngay trước đó → random lại
        if mv_path.name == last_name:
            continue

        # Load video
        mv = VideoFileClip(str(mv_path))
        mv = safe_resize(mv)

        # Extract audio
        extract_original_audio(mv, orig_audio_root / f"{mv_path.stem}.wav")

        # Add video
        clips_ready.append(mv.without_audio())

        main_duration += mv.duration
        print(f"     + {mv_path.name} ({mv.duration:.1f}s) => Tổng: {main_duration:.1f}s")

        last_name = mv_path.name  # cập nhật để tránh video trùng
        mv.close()

    # 3️⃣ Ending
    ending = random.choice(ending_files)
    print(f"  • Ending: {ending.name}")

    ve = VideoFileClip(str(ending))
    ve = safe_resize(ve)
    extract_original_audio(ve, orig_audio_root / f"{ending.stem}.wav")
    clips_ready.append(ve.without_audio())
    ve.close()

    print("\n⏳ Đang nối toàn bộ video...")
    merged_video = concatenate_videoclips(clips_ready, method="chain")

    return merged_video


# ==========================================================
#                     🚀 MAIN
# ==========================================================

def main():
    audio_dir = Path(AUDIO_DIR)
    opening_dir = Path(VIDEO_OPENING)
    main_dir = Path(VIDEO_MAIN)
    ending_dir = Path(VIDEO_ENDING)
    out_dir = Path(OUTPUT_DIR)
    orig_audio_root = out_dir / ORIG_AUDIO_DIRNAME

    ensure_dir(out_dir)
    ensure_dir(orig_audio_root)

    audios = scan(audio_dir, AUDIO_EXTS)
    opening_videos = scan(opening_dir, VIDEO_EXTS)
    main_videos = scan(main_dir, VIDEO_EXTS)
    ending_videos = scan(ending_dir, VIDEO_EXTS)

    if not audios:
        print("⚠ Không có audio.")
        return
    if not opening_videos or not main_videos or not ending_videos:
        print("⚠ Thiếu video opening/main/ending.")
        return

    merged_audio_path = out_dir / "merged_audio.wav"
    total_audio_len = merge_all_audio(audios, merged_audio_path)

    merged_video = build_video(
        opening_videos, main_videos, ending_videos,
        total_audio_len, orig_audio_root
    )

    if merged_video.duration > total_audio_len:
        merged_video = merged_video.subclip(0, total_audio_len)

    out_final = out_dir / "final_output.mp4"

    print("\n🎞 Xuất video cuối cùng...")
    merged_video.set_audio(AudioFileClip(str(merged_audio_path))).write_videofile(
        str(out_final),
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        audio_bitrate=AUDIO_BITRATE,
        bitrate=BITRATE,
        preset=PRESET,
        ffmpeg_params=["-crf", str(CRF)],
    )

    print("\n✅ Hoàn tất!")

# ==========================================================
#                 ▶️ CHẠY CHƯƠNG TRÌNH
# ==========================================================
if __name__ == "__main__":
    main()

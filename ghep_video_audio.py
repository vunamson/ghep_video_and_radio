import sys
import random
from pathlib import Path
from typing import List
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_audioclips,
    concatenate_videoclips
)

# ==========================================================
#                    ⚙️ CẤU HÌNH THƯ MỤC
# ==========================================================
AUDIO_DIR = r"C:\Youtobe\audio youtobe\Ngày 14-11-2025"
VIDEO_OPENING = r"C:\Youtobe\video youtobe\Video mở đầu"
VIDEO_MAIN = r"C:\Youtobe\video youtobe\Video tổng hợp"
VIDEO_ENDING = r"C:\Youtobe\video youtobe\Video kết thúc"
OUTPUT_DIR = r"C:\Youtobe\output video youtobe\Ngày 14-11-2025"
ORIG_AUDIO_DIRNAME = "_original_audio"     # thư mục để lưu audio gốc tách từ video

# ==========================================================
#                    🎞️ CẤU HÌNH XUẤT VIDEO
# ==========================================================
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
BITRATE = "6M"
PRESET = "medium"
CRF = 18

# Các loại file được chấp nhận
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}

# ==========================================================
#                    🔧 HÀM HỖ TRỢ
# ==========================================================

def ensure_dir(p: Path):
    """Tạo thư mục nếu chưa có."""
    p.mkdir(parents=True, exist_ok=True)

def scan(folder: Path, allowed_exts):
    """
    Quét thư mục và trả về danh sách file có đuôi hợp lệ.
    Sắp xếp theo tên để đồng bộ.
    """
    return sorted(
        [p for p in folder.glob("*") if p.is_file() and p.suffix.lower() in allowed_exts],
        key=lambda x: x.name.lower()
    )

def extract_original_audio(video_clip: VideoFileClip, out_path: Path):
    """
    Tách audio gốc của video ra file WAV.
    Dùng WAV vì chuẩn, không nén, đọc dễ.
    """
    if video_clip.audio is None:
        return
    video_clip.audio.write_audiofile(str(out_path), verbose=False, logger=None)

# ==========================================================
#         🔊 GHÉP TẤT CẢ AUDIO THÀNH 1 FILE DUY NHẤT
# ==========================================================

def merge_all_audio(audio_files: List[Path], out_path: Path) -> float:
    print("\n🔊 Ghép tất cả audio...")

    clips = []

    # Mở từng file audio và đưa vào danh sách
    for p in audio_files:
        try:
            clips.append(AudioFileClip(str(p)))
            print(f"  + {p.name}")
        except:
            print(f"  ⚠ Không đọc được: {p.name}")

    # Concatenate audio
    final = concatenate_audioclips(clips)

    # Xuất ra file WAV duy nhất
    final.write_audiofile(str(out_path), verbose=False, logger=None)

    duration = final.duration

    # Giải phóng bộ nhớ
    final.close()
    for c in clips:
        c.close()

    return duration  # trả về tổng thời lượng audio

# ==========================================================
#       🎬 GHÉP VIDEO THEO 3 PHẦN: OPENING → MAIN → ENDING
# ==========================================================

def build_video(opening_files, main_files, ending_files, total_audio_len, orig_audio_root: Path):
    print("\n🎬 Bắt đầu ghép video...")

    final_clips = []

    # ------------------------------------------------------
    # 1️⃣ VIDEO MỞ ĐẦU (OPENING)
    # ------------------------------------------------------
    opening = random.choice(opening_files)
    print(f"  • Opening: {opening.name}")

    vo = VideoFileClip(str(opening))

    # Nếu video có audio → tách ra
    if vo.audio:
        ensure_dir(orig_audio_root)
        extract_original_audio(vo, orig_audio_root / f"{opening.stem}.wav")

    # Thêm vào danh sách (KHÔNG dùng with để không đóng clip)
    final_clips.append(vo.without_audio())

    # ------------------------------------------------------
    # 2️⃣ VIDEO CHÍNH (MAIN) – GHÉP CHO TỚI KHI ĐỦ THỜI LƯỢNG AUDIO
    # ------------------------------------------------------
    print("  • Main videos:")

    main_duration = 0
    last_name = None      # để tránh lặp 2 video giống nhau liền nhau

    while main_duration < total_audio_len:
        choice = random.choice(main_files)

        # Không cho cùng tên đứng cạnh nhau
        if choice.name == last_name:
            continue
        last_name = choice.name

        print(f"     + {choice.name}")

        mv = VideoFileClip(str(choice))

        # Tách audio gốc trước khi xóa audio
        if mv.audio:
            extract_original_audio(mv, orig_audio_root / f"{choice.stem}.wav")

        final_clips.append(mv.without_audio())
        main_duration += mv.duration

    # ------------------------------------------------------
    # 3️⃣ VIDEO KẾT THÚC (ENDING)
    # ------------------------------------------------------
    ending = random.choice(ending_files)
    print(f"  • Ending: {ending.name}")

    ve = VideoFileClip(str(ending))
    if ve.audio:
        extract_original_audio(ve, orig_audio_root / f"{ending.stem}.wav")

    final_clips.append(ve.without_audio())

    # ------------------------------------------------------
    # 🔗 NỐI TẤT CẢ VIDEO LẠI THÀNH MỘT CLIP
    # ------------------------------------------------------
    print("\n⏳ Đang nối toàn bộ video...")

    merged_video = concatenate_videoclips(final_clips, method="chain")

    return merged_video


# ==========================================================
#                     🚀 CHƯƠNG TRÌNH CHÍNH
# ==========================================================

def main():

    # Chuẩn bị thư mục
    audio_dir = Path(AUDIO_DIR)
    opening_dir = Path(VIDEO_OPENING)
    main_dir = Path(VIDEO_MAIN)
    ending_dir = Path(VIDEO_ENDING)
    out_dir = Path(OUTPUT_DIR)
    orig_audio_root = out_dir / ORIG_AUDIO_DIRNAME

    ensure_dir(out_dir)

    # Quét lấy danh sách file
    audios = scan(audio_dir, AUDIO_EXTS)
    opening_videos = scan(opening_dir, VIDEO_EXTS)
    main_videos = scan(main_dir, VIDEO_EXTS)
    ending_videos = scan(ending_dir, VIDEO_EXTS)

    # Kiểm tra dữ liệu
    if not audios:
        print("⚠ Không có audio nào.")
        return

    if not opening_videos or not main_videos or not ending_videos:
        print("⚠ Thiếu thư mục opening / main / ending.")
        return

    # ======================================================
    # 1️⃣ GHÉP TOÀN BỘ AUDIO → audio lớn
    # ======================================================
    merged_audio_path = out_dir / "merged_audio.wav"
    total_audio_len = merge_all_audio(audios, merged_audio_path)

    # ======================================================
    # 2️⃣ GHÉP VIDEO → opening + main + ending
    # ======================================================
    merged_video = build_video(
        opening_files=opening_videos,
        main_files=main_videos,
        ending_files=ending_videos,
        total_audio_len=total_audio_len,
        orig_audio_root=orig_audio_root
    )

    # Nếu video dài hơn audio → cắt về đúng thời lượng audio
    if merged_video.duration > total_audio_len:
        merged_video = merged_video.subclip(0, total_audio_len)

    out_final = out_dir / "final_output.mp4"

    # ======================================================
    # 3️⃣ GHÉP AUDIO CUỐI VÀ XUẤT VIDEO HOÀN CHỈNH
    # ======================================================
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
#                    ▶️ CHẠY CHƯƠNG TRÌNH
# ==========================================================
if __name__ == "__main__":
    main()

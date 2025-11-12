import sys
import random
from pathlib import Path
from typing import List
from moviepy.editor import VideoFileClip, AudioFileClip

# ============ CẤU HÌNH ============
AUDIO_DIR = r"C:\Code\ghep_video_and_radio\audios"              # thư mục audio nguồn
VIDEO_DIR = r"C:\Code\ghep_video_and_radio\videos"              # thư mục video nguồn
OUTPUT_DIR = r"C:\Code\ghep_video_and_radio\output"             # thư mục xuất mp4
ORIG_AUDIO_DIRNAME = "_original_audio"        # thư mục con chứa audio gốc đã tách
EXPORT_ORIGINAL_AUDIO = True                  # True = xuất audio gốc của video trước khi ghép
RANDOM_SEED = None                            # ví dụ: 123 để tái lập, hoặc None để thật ngẫu nhiên

# Tùy chọn xuất
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
BITRATE = "6M"
AUDIO_BITRATE = "192k"
PRESET = "medium"
CRF = 18

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}


# ============ HÀM PHỤ ============
def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def scan_sorted(folder: Path, allow_exts) -> List[Path]:
    return sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in allow_exts],
                  key=lambda x: x.name.lower())

def extract_original_audio(video_clip: VideoFileClip, out_wav_path: Path):
    """
    Xuất audio gốc của video thành WAV (an toàn, phổ biến).
    Nếu video không có audio, bỏ qua.
    """
    if video_clip.audio is None:
        return
    # MoviePy sẽ tự chọn codec phù hợp theo đuôi .wav
    video_clip.audio.write_audiofile(str(out_wav_path), verbose=False, logger=None)

def mux_trim_to_shorter(video_path: Path, audio_path: Path, out_path: Path, orig_audio_root: Path):
    print(f"\n>> Video: {video_path.name}")
    print(f"   Audio ngẫu nhiên: {audio_path.name}")

    with VideoFileClip(str(video_path)) as v, AudioFileClip(str(audio_path)) as a:
        # 1) Tách audio gốc (nếu bật)
        if EXPORT_ORIGINAL_AUDIO:
            ensure_dir(orig_audio_root)
            orig_audio_out = orig_audio_root / f"{video_path.stem}.wav"
            try:
                extract_original_audio(v, orig_audio_out)
                print(f"   • Đã tách audio gốc: {orig_audio_out.name}")
            except Exception as e:
                print(f"   • Không thể tách audio gốc ({e}), tiếp tục ghép...")

        # 2) Cắt cái dài về bằng cái ngắn
        vd, ad = v.duration or 0, a.duration or 0
        if vd <= 0 or ad <= 0:
            raise RuntimeError("Không đọc được duration hợp lệ (video hoặc audio).")

        T = min(vd, ad)
        v_t = v.subclip(0, T)
        a_t = a.subclip(0, T)

        v_out = v_t.set_audio(a_t).set_duration(T)

        # 3) Xuất file
        fps = getattr(v, "fps", None)
        write_kwargs = {
            "codec": VIDEO_CODEC,
            "audio_codec": AUDIO_CODEC,
            "audio_bitrate": AUDIO_BITRATE,
            "bitrate": BITRATE,
            "preset": PRESET,
            "threads": "auto",
            "temp_audiofile": str(out_path.with_suffix(".temp-audio.m4a")),
            "remove_temp": True,
            "ffmpeg_params": ["-crf", str(CRF)],
        }
        if fps and fps > 0:
            write_kwargs["fps"] = fps

        print(f"   • Xuất: {out_path.name} (T = {T:.2f}s)")
        v_out.write_videofile(str(out_path), **write_kwargs)

def main():
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    audio_dir = Path(AUDIO_DIR)
    video_dir = Path(VIDEO_DIR)
    out_dir = Path(OUTPUT_DIR)
    orig_audio_root = out_dir / ORIG_AUDIO_DIRNAME

    if not audio_dir.exists() or not video_dir.exists():
        print("⚠️  Kiểm tra lại đường dẫn AUDIO_DIR / VIDEO_DIR.")
        sys.exit(1)

    ensure_dir(out_dir)

    audios = scan_sorted(audio_dir, AUDIO_EXTS)
    videos = scan_sorted(video_dir, VIDEO_EXTS)

    if not audios:
        print("⚠️  Không tìm thấy file audio.")
        sys.exit(1)
    if not videos:
        print("⚠️  Không tìm thấy file video.")
        sys.exit(1)

    print(f"Tổng số video sẽ xử lý: {len(videos)}")
    for vpath in videos:
        # chọn ngẫu nhiên 1 audio cho video này
        apath = random.choice(audios)
        out_name = f"{vpath.stem}__{apath.stem}.mp4"
        out_path = out_dir / out_name

        if out_path.exists():
            print(f"- BỎ QUA (đã tồn tại): {out_path.name}")
            continue

        try:
            mux_trim_to_shorter(vpath, apath, out_path, orig_audio_root)
        except Exception as e:
            print(f"❌ Lỗi khi xử lý {vpath.name}: {e}")

if __name__ == "__main__":
    main()

import whisper
import subprocess
import sys
import os

# Custom logging function
def log(message):
    print(f"[LOG {os.times().elapsed:.2f}s] {message}")

# Helper function for ASS time format
def format_time_ass(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{cs:02d}"

def process_video(video_path, output_path):
    audio_file = "uploads/audio.mp3"
    subtitle_file = "uploads/captions.ass"

    # Ensure uploads directory exists
    if not os.path.exists("uploads"):
        os.makedirs("uploads")

    # Step 1: Log input/output paths
    log(f"Input video: {video_path}")
    log(f"Output video: {output_path}")
    if not os.path.exists(video_path):
        log(f"Error: Input video {video_path} does not exist")
        sys.exit(1)
    log(f"Input video size: {os.path.getsize(video_path)} bytes")

    # Step 2: Extract audio
    log(f"Extracting audio to {audio_file}")
    result = subprocess.run(
        ["ffmpeg", "-i", video_path, "-vn", "-acodec", "mp3", "-y", audio_file],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"Audio extraction failed: {result.stderr}")
        sys.exit(1)
    log(f"Audio extracted: {audio_file}, size: {os.path.getsize(audio_file)} bytes")
    log(f"FFmpeg stdout: {result.stdout}")
    log(f"FFmpeg stderr: {result.stderr}")

    # Step 3: Transcribe using Whisper with word-level timestamps
    log("Loading Whisper model (medium)")
    try:
        model = whisper.load_model("medium")  # "tiny" for faster testing if needed
        log("Whisper model loaded")
        log(f"Transcribing audio with word timestamps: {audio_file}")
        result = model.transcribe(audio_file, word_timestamps=True)
        log(f"Transcription complete, segments: {len(result['segments'])}, text: '{result['text']}'")
        if not result["segments"]:
            log("Warning: No speech detected in audio")
    except Exception as e:
        log(f"Whisper error: {str(e)}")
        sys.exit(1)

    # Step 4: Generate captions.ass with center alignment using word timestamps
    log(f"Generating ASS subtitles: {subtitle_file}")
    with open(subtitle_file, "w") as f:
        # ASS Header
        f.write("[Script Info]\n")
        f.write("Title: Whisper Captions\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1280\n")
        f.write("PlayResY: 720\n")
        f.write("WrapStyle: 0\n")
        f.write("ScaledBorderAndShadow: yes\n")
        f.write("YCbCr Matrix: TV.601\n\n")

        # Styles (Alignment 5 = center)
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
                "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, "
                "Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,"
                "0,0,0,0,100,100,0,0,1,1,0,5,10,10,10,1\n\n")

        # Events
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        # Create word-level subtitles with accurate timestamps
        counter = 0
        for segment in result["segments"]:
            if "words" not in segment or not segment["words"]:
                log(f"Segment at {segment['start']}-{segment['end']} has no word timestamps")
                continue
            for word_info in segment["words"]:
                word = word_info["word"]
                word_start = word_info["start"]
                word_end = word_info["end"]
                # Handle cases where timestamps might be missing or invalid
                if word_start is None or word_end is None:
                    log(f"Skipping word '{word}' due to missing timestamps")
                    continue
                start_ass = format_time_ass(word_start)
                end_ass = format_time_ass(word_end)
                f.write(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{word}\n")
                counter += 1
    log(f"Subtitles written: {subtitle_file}, {counter} entries, size: {os.path.getsize(subtitle_file)} bytes")
    if counter == 0:
        log("Warning: No subtitle entries generated")

    # Step 5: Burn the centered ASS captions into video
    log(f"Burning subtitles into video: {output_path}")
    result = subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", f"ass={subtitle_file}",
        "-c:a", "copy", "-y", output_path
    ], capture_output=True, text=True)
    log(f"FFmpeg stdout: {result.stdout}")
    log(f"FFmpeg stderr: {result.stderr}")
    if result.returncode != 0:
        log(f"FFmpeg subtitle burning failed with exit code {result.returncode}")
        sys.exit(1)
    log(f"Video processing complete: {output_path}, size: {os.path.getsize(output_path)} bytes")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        log("Usage: python process_video.py <input_video> <output_video>")
        sys.exit(1)
    video_path = sys.argv[1]
    output_path = sys.argv[2]
    process_video(video_path, output_path)
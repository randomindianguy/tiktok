from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
from dotenv import load_dotenv
import os
import tempfile
import subprocess
import whisper

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Claude client
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Load Whisper model (runs locally - no API needed)
# Options: "tiny", "base", "small", "medium", "large"
print("Loading Whisper model (this may take a minute first time)...")
whisper_model = whisper.load_model("base")
print("Whisper model loaded!")


def get_context_before(segments, pause_time, seconds=15):
    """Get transcript text from ~15 seconds before the pause"""
    cutoff = pause_time - seconds
    
    context_words = []
    for seg in segments:
        if seg["start"] >= cutoff and seg["end"] <= pause_time:
            context_words.append(seg["text"].strip())
    
    return " ".join(context_words)


def detect_pauses(segments, threshold=3.0):
    """Find gaps > threshold seconds between segments"""
    pauses = []
    
    if not segments or len(segments) < 2:
        return pauses
    
    for i in range(1, len(segments)):
        gap = segments[i]["start"] - segments[i-1]["end"]
        if gap >= threshold:
            pauses.append({
                "pause_start": segments[i-1]["end"],
                "pause_end": segments[i]["start"],
                "duration": round(gap, 2),
                "context_before": get_context_before(segments, segments[i]["start"])
            })
    
    return pauses


def generate_prompt_with_claude(context):
    """Generate a continuation prompt using Claude"""
    if not context or len(context.strip()) < 10:
        return "What's the main point you want to share?"
    
    message = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": f"""You help TikTok creators who freeze while recording videos.

Given the last 15 seconds of what they said, generate ONE short prompt (under 15 words) to help them continue naturally.

Rules:
- Be specific to their topic, not generic
- Phrase as a question or gentle suggestion
- Conversational, friendly tone
- No motivational fluff like "you got this"
- No generic prompts like "tell us more"
- Reference something specific they mentioned

Creator was saying: "{context}"

They froze. Give them a specific prompt to continue (just the prompt, nothing else):"""
            }
        ]
    )
    
    return message.content[0].text.strip().strip('"')


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Receives a video/audio file, transcribes with local Whisper,
    detects pauses, and generates coaching prompts with Claude.
    """
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    video_file = request.files["video"]
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        video_file.save(tmp.name)
        tmp_path = tmp.name
    
    # Convert webm to wav (Whisper works better with wav)
    wav_path = tmp_path.replace(".webm", ".wav")
    
    try:
        # Use ffmpeg to extract audio
        print("Converting to wav...")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-i", tmp_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            wav_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr}")
            return jsonify({"error": "Failed to process audio. Make sure ffmpeg is installed."}), 500
        
        # Transcribe with local Whisper
        print("Transcribing with Whisper...")
        result = whisper_model.transcribe(
            wav_path,
            word_timestamps=True,
            verbose=False
        )
        
        full_text = result["text"]
        segments = result["segments"]
        
        # Extract word-level data
        words = []
        for segment in segments:
            if "words" in segment:
                for word in segment["words"]:
                    words.append({
                        "word": word["word"],
                        "start": word["start"],
                        "end": word["end"]
                    })
        
        # Detect pauses (gaps > 3 seconds)
        pauses = detect_pauses(segments, threshold=3.0)
        
        # Generate Claude prompts for each pause
        print(f"Found {len(pauses)} pauses, generating prompts with Claude...")
        for pause in pauses:
            if pause["context_before"]:
                pause["ai_prompt"] = generate_prompt_with_claude(pause["context_before"])
            else:
                pause["ai_prompt"] = "What's the main point you want to share?"
        
        duration = segments[-1]["end"] if segments else 0
        
        return jsonify({
            "success": True,
            "transcript": full_text,
            "words": words,
            "pauses": pauses,
            "stats": {
                "duration": duration,
                "word_count": len(words),
                "pause_count": len(pauses)
            }
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Clean up temp files
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("🎤 Confidence Coach Backend Starting...")
    print("   Using: Local Whisper (free) + Claude API")
    print("   Make sure ANTHROPIC_API_KEY is set in .env")
    app.run(debug=True, port=5001)

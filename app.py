"""
Confidence Coach - Backend API
Helps first-time TikTok creators overcome the "freeze" moment

Target Segment: 0-1K followers, high watch time, never posted or abandoned 3+ recordings
Core Insight: High motivation, low ability at the critical moment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === CORE FUNCTIONS ===

def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribe audio using Whisper API with word-level timestamps.
    Returns transcript text and word timings for pause detection.
    """
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    
    return {
        "text": transcript.text,
        "words": [{"word": w.word, "start": w.start, "end": w.end} for w in transcript.words]
    }


def detect_pauses(words: list, threshold: float = 3.0) -> list:
    """
    Find gaps > threshold seconds between words.
    These are the "freeze" moments where creators need help.
    
    B=MAT Application:
    - The pause is the TRIGGER
    - The prompt reduces ABILITY barrier (mental effort)
    - Completion drives MOTIVATION for next attempt
    """
    pauses = []
    
    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i-1]["end"]
        
        if gap >= threshold:
            # Get context: last ~15 seconds before the pause
            context = get_context_before(words, i, seconds=15)
            
            pauses.append({
                "pause_start": round(words[i-1]["end"], 2),
                "pause_end": round(words[i]["start"], 2),
                "duration": round(gap, 2),
                "word_before": words[i-1]["word"],
                "word_after": words[i]["word"],
                "context_before": context
            })
    
    return pauses


def get_context_before(words: list, index: int, seconds: float = 15) -> str:
    """
    Extract transcript text from ~15 seconds before the pause.
    This context makes prompts SPECIFIC, not generic.
    
    Key insight: Generic prompts ("you got this!") don't help.
    Context-aware prompts ("what's an example of that?") do.
    """
    if index == 0:
        return ""
    
    pause_time = words[index]["start"]
    cutoff = pause_time - seconds
    
    context_words = []
    for w in words[:index]:
        if w["start"] >= cutoff:
            context_words.append(w["word"])
    
    return " ".join(context_words)


def generate_prompt(context: str, full_transcript: str = "") -> str:
    """
    Generate a continuation prompt using GPT-4.
    
    Prompt Engineering Principles:
    1. Be SPECIFIC to their topic (not generic encouragement)
    2. Phrase as question or suggestion (actionable)
    3. Conversational tone (matches TikTok vibe)
    4. Under 15 words (quick to read while recording)
    """
    
    if not context or len(context.strip()) < 10:
        # Not enough context - give a gentle starter
        return "What's the main point you want to make?"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """You help TikTok creators who freeze while recording.

Given the last 15 seconds of what they said, generate ONE short prompt to help them continue.

RULES:
- Be specific to their topic, not generic
- Phrase as a question or suggestion  
- Conversational TikTok tone
- Under 15 words
- No "you got this" fluff - that doesn't help
- Think: what would a supportive friend whisper to help them continue?

GOOD EXAMPLES:
- "What's a specific example of that?"
- "Why does that matter to you personally?"
- "What would you tell someone who disagrees?"

BAD EXAMPLES:
- "Keep going, you're doing great!" (generic, unhelpful)
- "Continue with your thought" (too vague)
- "Consider elaborating on the aforementioned topic" (too formal)"""
            },
            {
                "role": "user",
                "content": f"Creator was saying: \"{context}\"\n\nThey froze. Give them ONE prompt to continue:"
            }
        ],
        max_tokens=50,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip().strip('"')


def calculate_metrics(transcript: str, pauses: list, prompts_generated: int) -> dict:
    """
    Calculate metrics for the practice session.
    
    These tie to our growth loops:
    - Completion signals → feeds confidence flywheel
    - Pause patterns → data flywheel for ML improvement
    """
    word_count = len(transcript.split())
    pause_count = len(pauses)
    total_pause_time = sum(p["duration"] for p in pauses)
    
    # Fluency score: penalize long/frequent pauses
    # This becomes a gamification lever for habit formation
    if word_count > 0:
        fluency = max(0, 100 - (total_pause_time * 5) - (pause_count * 10))
    else:
        fluency = 0
    
    return {
        "word_count": word_count,
        "pause_count": pause_count,
        "total_pause_seconds": round(total_pause_time, 1),
        "prompts_generated": prompts_generated,
        "fluency_score": round(fluency)
    }


# === API ROUTES ===

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "confidence-coach"})


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Main analysis endpoint.
    
    Flow:
    1. Receive audio recording
    2. Transcribe with Whisper (word-level timestamps)
    3. Detect pauses > 3 seconds
    4. Generate context-aware prompts for each pause
    5. Return results for side-by-side display
    
    Privacy Design:
    - Audio saved to temp file, deleted immediately after processing
    - Nothing stored permanently
    - Encrypted in transit (HTTPS)
    """
    start_time = time.time()
    
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files["audio"]
    
    # Save to temp file (will be deleted)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)
    
    try:
        # Step 1: Transcribe
        transcription = transcribe_audio(audio_path)
        
        # Step 2: Detect pauses
        pauses = detect_pauses(transcription["words"], threshold=3.0)
        
        # Step 3: Generate prompts for each pause
        for pause in pauses:
            if pause["context_before"]:
                pause["ai_prompt"] = generate_prompt(
                    pause["context_before"],
                    transcription["text"]
                )
            else:
                pause["ai_prompt"] = "What's the main point you want to make?"
        
        # Step 4: Calculate metrics
        metrics = calculate_metrics(
            transcription["text"],
            pauses,
            len(pauses)
        )
        
        processing_time = round(time.time() - start_time, 2)
        
        return jsonify({
            "success": True,
            "transcript": transcription["text"],
            "words": transcription["words"],
            "pauses": pauses,
            "metrics": metrics,
            "processing_time_seconds": processing_time
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        # CRITICAL: Delete audio file immediately
        # Privacy commitment: nothing stored
        if os.path.exists(audio_path):
            os.remove(audio_path)


@app.route("/quick-prompt", methods=["POST"])
def quick_prompt():
    """
    Quick prompt generation from text only (no audio).
    Useful for testing prompt quality without full recording flow.
    """
    data = request.get_json()
    context = data.get("context", "")
    
    if not context:
        return jsonify({"error": "No context provided"}), 400
    
    prompt = generate_prompt(context)
    
    return jsonify({
        "success": True,
        "context": context,
        "prompt": prompt
    })


# === MAIN ===

if __name__ == "__main__":
    print("\n🎤 Confidence Coach API")
    print("=" * 40)
    print("Target: First-time creators (0-1K followers)")
    print("Problem: Freezing mid-recording")
    print("Solution: Context-aware continuation prompts")
    print("=" * 40)
    print("\nEndpoints:")
    print("  POST /analyze - Analyze recording, detect pauses, generate prompts")
    print("  POST /quick-prompt - Generate prompt from text context")
    print("  GET  /health - Health check")
    print("\nStarting server on http://localhost:5001")
    print("=" * 40 + "\n")
    
    app.run(debug=True, port=5001)

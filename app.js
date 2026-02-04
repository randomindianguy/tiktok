/**
 * Confidence Coach - Frontend Application
 * 
 * Target Segment: First-time TikTok creators (0-1K followers)
 * Core Problem: Freezing mid-recording
 * Solution: Context-aware AI prompts at pause moments
 * 
 * Growth Loops Enabled:
 * 1. Confidence Flywheel: Practice → Prompt → Complete → Post → Engagement → More attempts
 * 2. Data Flywheel: More users → Better prompts → Higher completion → More users
 */

// === CONFIGURATION ===
const API_URL = 'http://localhost:5001';

// === DOM ELEMENTS ===
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const status = document.getElementById('status');
const statusText = status.querySelector('.status-text');
const timer = document.getElementById('timer');
const waveform = document.getElementById('waveform');
const placeholder = document.getElementById('placeholder');
const resultsContent = document.getElementById('resultsContent');
const transcriptBox = document.getElementById('transcriptBox');
const promptsList = document.getElementById('promptsList');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingStep = document.getElementById('loadingStep');

// Metrics
const metricWords = document.getElementById('metricWords');
const metricPauses = document.getElementById('metricPauses');
const metricFluency = document.getElementById('metricFluency');
const metricTime = document.getElementById('metricTime');

// === STATE ===
let mediaRecorder = null;
let audioChunks = [];
let audioBlob = null;
let recordingStartTime = null;
let timerInterval = null;

// === RECORDING FUNCTIONS ===

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
            }
        });
        
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            stream.getTracks().forEach(track => track.stop());
            onRecordingComplete();
        };
        
        mediaRecorder.start(100); // Collect data every 100ms
        recordingStartTime = Date.now();
        
        // Update UI
        recordBtn.disabled = true;
        recordBtn.classList.add('recording');
        stopBtn.disabled = false;
        analyzeBtn.disabled = true;
        
        status.className = 'status recording';
        statusText.textContent = 'Recording... Talk like you\'re making a TikTok';
        
        waveform.classList.add('recording');
        
        // Start timer
        startTimer();
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        statusText.textContent = 'Error: Could not access microphone. Please allow microphone access.';
        status.className = 'status';
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        stopTimer();
        
        // Update UI
        recordBtn.disabled = false;
        recordBtn.classList.remove('recording');
        stopBtn.disabled = true;
        
        waveform.classList.remove('recording');
        
        status.className = 'status ready';
        statusText.textContent = 'Recording saved. Ready to analyze.';
    }
}

function onRecordingComplete() {
    analyzeBtn.disabled = false;
    
    // Calculate duration
    const duration = (Date.now() - recordingStartTime) / 1000;
    statusText.textContent = `Recording saved (${formatTime(duration)}). Hit "Analyze" to get AI prompts.`;
}

// === TIMER FUNCTIONS ===

function startTimer() {
    let seconds = 0;
    timerInterval = setInterval(() => {
        seconds++;
        timer.textContent = formatTime(seconds);
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function formatTime(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// === ANALYSIS FUNCTIONS ===

async function analyzeRecording() {
    if (!audioBlob) {
        statusText.textContent = 'No recording to analyze. Record something first.';
        return;
    }
    
    // Show loading
    showLoading('Sending audio to Whisper AI...');
    
    analyzeBtn.disabled = true;
    status.className = 'status processing';
    statusText.textContent = 'Analyzing with AI...';
    
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    try {
        // Update loading steps
        setTimeout(() => updateLoadingStep('Transcribing with word-level timestamps...'), 1000);
        setTimeout(() => updateLoadingStep('Detecting pause moments...'), 2500);
        setTimeout(() => updateLoadingStep('Generating context-aware prompts with GPT-4...'), 4000);
        
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            status.className = 'status ready';
            statusText.textContent = 'Analysis complete! See your results on the right.';
        } else {
            throw new Error(data.error || 'Analysis failed');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        status.className = 'status';
        statusText.textContent = `Error: ${error.message}. Is the backend running?`;
    } finally {
        hideLoading();
        analyzeBtn.disabled = false;
    }
}

// === DISPLAY FUNCTIONS ===

function displayResults(data) {
    // Hide placeholder, show results
    placeholder.style.display = 'none';
    resultsContent.style.display = 'flex';
    
    // Update metrics
    metricWords.textContent = data.metrics.word_count;
    metricPauses.textContent = data.metrics.pause_count;
    metricFluency.textContent = data.metrics.fluency_score;
    metricTime.textContent = `${data.processing_time_seconds}s`;
    
    // Build transcript with pause markers
    displayTranscript(data.transcript, data.pauses, data.words);
    
    // Display prompts
    displayPrompts(data.pauses);
}

function displayTranscript(transcript, pauses, words) {
    if (!transcript || transcript.trim() === '') {
        transcriptBox.innerHTML = '<p style="color: var(--text-tertiary);">No speech detected. Try recording again.</p>';
        return;
    }
    
    // If no pauses, just show the transcript
    if (pauses.length === 0) {
        transcriptBox.innerHTML = `<p>${escapeHtml(transcript)}</p>`;
        return;
    }
    
    // Build transcript with pause markers inserted
    // This is a simplified approach - insert markers between words
    let html = '';
    let pauseIndex = 0;
    
    for (let i = 0; i < words.length; i++) {
        const word = words[i];
        
        // Check if there's a pause after this word
        if (pauseIndex < pauses.length && i < words.length - 1) {
            const pause = pauses[pauseIndex];
            const nextWord = words[i + 1];
            
            // If this pause is between current word and next word
            if (Math.abs(word.end - pause.pause_start) < 0.5) {
                html += escapeHtml(word.word) + ' ';
                html += `<span class="pause-marker">⏸️ ${pause.duration}s pause</span> `;
                pauseIndex++;
                continue;
            }
        }
        
        html += escapeHtml(word.word) + ' ';
    }
    
    transcriptBox.innerHTML = `<p>${html}</p>`;
}

function displayPrompts(pauses) {
    if (pauses.length === 0) {
        promptsList.innerHTML = `
            <div class="no-pauses">
                <div class="no-pauses-icon">🎉</div>
                <p>No long pauses detected! You had great flow.</p>
                <p style="margin-top: 8px; font-size: 0.9rem; opacity: 0.7;">
                    Try recording again and pause deliberately to see AI prompts in action.
                </p>
            </div>
        `;
        return;
    }
    
    const promptCards = pauses.map((pause, index) => `
        <div class="prompt-card">
            <div class="prompt-meta">
                <span>Pause ${index + 1}</span>
                <span class="prompt-duration">${pause.duration}s</span>
                <span>at ${pause.pause_start}s</span>
            </div>
            <div class="prompt-text">💡 "${escapeHtml(pause.ai_prompt)}"</div>
            ${pause.context_before ? `
                <div class="prompt-context">
                    Context: "...${escapeHtml(truncate(pause.context_before, 80))}"
                </div>
            ` : ''}
        </div>
    `).join('');
    
    promptsList.innerHTML = promptCards;
}

// === LOADING FUNCTIONS ===

function showLoading(message) {
    loadingStep.textContent = message;
    loadingOverlay.classList.add('active');
}

function updateLoadingStep(message) {
    loadingStep.textContent = message;
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

// === UTILITY FUNCTIONS ===

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(text.length - maxLength) + '...';
}

// === EVENT LISTENERS ===

recordBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);
analyzeBtn.addEventListener('click', analyzeRecording);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Space to toggle recording
    if (e.code === 'Space' && e.target === document.body) {
        e.preventDefault();
        if (!recordBtn.disabled) {
            startRecording();
        } else if (!stopBtn.disabled) {
            stopRecording();
        }
    }
    
    // Enter to analyze
    if (e.code === 'Enter' && !analyzeBtn.disabled) {
        e.preventDefault();
        analyzeRecording();
    }
});

// === INITIALIZATION ===

console.log(`
🎤 Confidence Coach - Practice Mode
====================================
Target: First-time creators (0-1K followers)
Problem: Freezing mid-recording  
Solution: Context-aware AI prompts

Growth Loops:
1. Confidence Flywheel: Practice → Prompt → Complete → Post → Engagement
2. Data Flywheel: More users → Better prompts → Higher completion

Keyboard shortcuts:
- Space: Start/Stop recording
- Enter: Analyze recording
====================================
`);

// Check if backend is available
fetch(`${API_URL}/health`)
    .then(res => res.json())
    .then(data => {
        console.log('✅ Backend connected:', data);
    })
    .catch(err => {
        console.warn('⚠️ Backend not available. Start it with: cd backend && python app.py');
        statusText.textContent = 'Backend not connected. Start the server first.';
    });

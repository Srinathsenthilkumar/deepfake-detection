/**
 * Deepfake Detector | Multimodal AI Forensics Frontend Engine
 */

let activeMode = 'upload';
let currentFile = null;
let currentFileUrl = null;
let latestReportData = null;
let scanTimer = null;

// DOM Elements
const tabUpload = document.getElementById('tab-upload');
const tabUrl = document.getElementById('tab-url');
const tabDemo = document.getElementById('tab-demo');

const sectionUpload = document.getElementById('section-upload');
const sectionUrl = document.getElementById('section-url');
const sectionDemo = document.getElementById('section-demo');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const mediaPreview = document.getElementById('media-preview');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const fileIcon = document.getElementById('file-icon');
const videoPreview = document.getElementById('video-preview');
const audioPreview = document.getElementById('audio-preview');

const actionFooter = document.getElementById('action-footer');
const analyzeBtn = document.getElementById('analyze-btn');
const loadingState = document.getElementById('loading-state');
const resultsSection = document.getElementById('results-section');

const scanStatusTitle = document.getElementById('scan-status-title');
const scanStatusSubtext = document.getElementById('scan-status-subtext');
const progressBarFill = document.getElementById('progress-bar-fill');

// Mode Switching
function switchMode(mode) {
    activeMode = mode;

    [tabUpload, tabUrl, tabDemo].forEach(t => t.classList.remove('active'));
    [sectionUpload, sectionUrl, sectionDemo].forEach(s => {
        s.classList.add('hidden');
        s.classList.remove('active');
    });

    if (mode === 'upload') {
        tabUpload.classList.add('active');
        sectionUpload.classList.remove('hidden');
        sectionUpload.classList.add('active');
        actionFooter.classList.remove('hidden');
    } else if (mode === 'url') {
        tabUrl.classList.add('active');
        sectionUrl.classList.remove('hidden');
        sectionUrl.classList.add('active');
        actionFooter.classList.remove('hidden');
    } else if (mode === 'demo') {
        tabDemo.classList.add('active');
        sectionDemo.classList.remove('hidden');
        sectionDemo.classList.add('active');
        actionFooter.classList.add('hidden'); // Demos have self-trigger buttons
    }
}

// Drag & Drop Listeners
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processSelectedFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files.length > 0) {
        processSelectedFile(fileInput.files[0]);
    }
});

// Media Handling & Preview
function processSelectedFile(file) {
    currentFile = file;
    fileName.textContent = file.name;

    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    fileSize.textContent = `${sizeMb} MB`;

    // Revoke old object URL if exists
    if (currentFileUrl) {
        URL.revokeObjectURL(currentFileUrl);
    }
    currentFileUrl = URL.createObjectURL(file);

    const isAudio = file.type.startsWith('audio/') || /\.(wav|mp3|m4a|flac|ogg)$/i.test(file.name);

    if (isAudio) {
        fileIcon.className = 'ph ph-file-audio file-type-icon';
        videoPreview.classList.add('hidden');
        videoPreview.src = '';
        audioPreview.src = currentFileUrl;
        audioPreview.classList.remove('hidden');
    } else {
        fileIcon.className = 'ph ph-file-video file-type-icon';
        audioPreview.classList.add('hidden');
        audioPreview.src = '';
        videoPreview.src = currentFileUrl;
        videoPreview.classList.remove('hidden');
    }

    dropZone.classList.add('hidden');
    mediaPreview.classList.remove('hidden');
}

function clearSelectedFile() {
    currentFile = null;
    fileInput.value = '';
    if (currentFileUrl) {
        URL.revokeObjectURL(currentFileUrl);
        currentFileUrl = null;
    }
    videoPreview.src = '';
    audioPreview.src = '';
    videoPreview.classList.add('hidden');
    audioPreview.classList.add('hidden');
    mediaPreview.classList.add('hidden');
    dropZone.classList.remove('hidden');
}

// Forensic Scanning Animation
function startScanningAnimation() {
    // Hide inputs & show scanning state
    document.querySelector('.mode-tabs').classList.add('hidden');
    sectionUpload.classList.add('hidden');
    sectionUrl.classList.add('hidden');
    sectionDemo.classList.add('hidden');
    actionFooter.classList.add('hidden');

    loadingState.classList.remove('hidden');
    resultsSection.classList.add('hidden');

    progressBarFill.style.width = '0%';
    resetStepBadges();

    let step = 1;
    updateStepBadge(1);
    progressBarFill.style.width = '20%';

    scanTimer = setInterval(() => {
        step++;
        if (step === 2) {
            updateStepBadge(2);
            scanStatusTitle.textContent = "Analyzing 468-Point Facial Mesh...";
            scanStatusSubtext.textContent = "Tracking Eye Aspect Ratio (EAR) involuntary blinking dynamics";
            progressBarFill.style.width = '45%';
        } else if (step === 3) {
            updateStepBadge(3);
            scanStatusTitle.textContent = "Decomposing Acoustic Spectrogram...";
            scanStatusSubtext.textContent = "Auditing Fourier transform bands for vocoder synthesis cutoffs";
            progressBarFill.style.width = '70%';
        } else if (step === 4) {
            updateStepBadge(4);
            scanStatusTitle.textContent = "Computing Cross-Modal Synchronization...";
            scanStatusSubtext.textContent = "Aligning temporal phoneme energy with visual lip kinematics";
            progressBarFill.style.width = '90%';
        }
    }, 1100);
}

function stopScanningAnimation() {
    if (scanTimer) {
        clearInterval(scanTimer);
        scanTimer = null;
    }
    progressBarFill.style.width = '100%';
}

function resetStepBadges() {
    for (let i = 1; i <= 4; i++) {
        const badge = document.getElementById(`step-${i}`);
        if (badge) {
            badge.className = 'step-badge';
            badge.innerHTML = `<i class="ph ph-circle"></i> ${getStepTitle(i)}`;
        }
    }
}

function updateStepBadge(current) {
    for (let i = 1; i <= 4; i++) {
        const badge = document.getElementById(`step-${i}`);
        if (!badge) continue;
        if (i < current) {
            badge.className = 'step-badge done';
            badge.innerHTML = `<i class="ph ph-check-circle"></i> ${getStepTitle(i)}`;
        } else if (i === current) {
            badge.className = 'step-badge active';
            badge.innerHTML = `<i class="ph ph-spinner ph-spin"></i> ${getStepTitle(i)}`;
        } else {
            badge.className = 'step-badge';
            badge.innerHTML = `<i class="ph ph-circle"></i> ${getStepTitle(i)}`;
        }
    }
}

function getStepTitle(idx) {
    const titles = {
        1: '1. Ingestion',
        2: '2. Facial Mesh',
        3: '3. Acoustic FFT',
        4: '4. AV-Sync'
    };
    return titles[idx] || '';
}

// Submit Real Media Analysis
async function initiateAnalysis() {
    const formData = new FormData();

    if (activeMode === 'upload') {
        if (!currentFile) {
            alert('Please select or drop a video or audio file first.');
            return;
        }
        formData.append('input_type', 'file');
        formData.append('file', currentFile);
    } else if (activeMode === 'url') {
        const urlValue = document.getElementById('url-input').value.trim();
        if (!urlValue) {
            alert('Please enter a valid media stream or YouTube URL.');
            return;
        }
        formData.append('input_type', 'url');
        formData.append('url', urlValue);
    }

    startScanningAnimation();

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        stopScanningAnimation();

        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Server encountered an issue analyzing media.');
        }

        setTimeout(() => {
            renderResultsDashboard(data);
        }, 300);

    } catch (err) {
        stopScanningAnimation();
        alert(`Analysis Error: ${err.message}`);
        resetApp();
    }
}

// Instant Demo Sample
async function runDemoSample(sampleType) {
    startScanningAnimation();

    try {
        const response = await fetch('/demo-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: sampleType })
        });

        const data = await response.json();
        stopScanningAnimation();

        setTimeout(() => {
            renderResultsDashboard(data);
        }, 1200);

    } catch (err) {
        stopScanningAnimation();
        alert(`Demo execution failed: ${err.message}`);
        resetApp();
    }
}

// Render Results Dashboard
function renderResultsDashboard(data) {
    latestReportData = {
        ...data,
        timestamp: new Date().toISOString(),
        analyzed_file: currentFile ? currentFile.name : (document.getElementById('url-input').value || 'Demo Sample')
    };

    loadingState.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    const finalProb = data.final_fake_prob;
    const category = data.verdict_category || (finalProb >= 65 ? 'danger' : finalProb >= 40 ? 'warning' : 'authentic');

    // 1. Verdict Banner
    const verdictBanner = document.getElementById('verdict-banner');
    const verdictIcon = document.getElementById('verdict-icon');
    const verdictTitle = document.getElementById('verdict-title');
    const verdictExplanation = document.getElementById('verdict-explanation');
    const finalProbValue = document.getElementById('final-prob-value');

    verdictBanner.className = `verdict-banner state-${category}`;
    verdictTitle.textContent = data.verdict_title || (category === 'danger' ? 'High Probability Deepfake' : category === 'warning' ? 'Suspicious Media' : 'Likely Authentic Media');
    verdictExplanation.textContent = data.explanation || 'Multimodal inspection complete.';
    finalProbValue.textContent = `${finalProb}%`;

    if (category === 'danger') {
        verdictIcon.className = 'ph ph-warning-octagon';
    } else if (category === 'warning') {
        verdictIcon.className = 'ph ph-warning';
    } else {
        verdictIcon.className = 'ph ph-shield-check';
    }

    // 2. Visual Metric Card
    const vidScoreEl = document.getElementById('video-score');
    const vidStatusEl = document.getElementById('video-status');
    const vidBar = document.getElementById('video-bar');

    if (data.video_fake_prob !== null && data.video_fake_prob !== undefined) {
        const score = data.video_fake_prob;
        vidScoreEl.textContent = `${score}%`;
        vidBar.style.width = `${Math.min(100, Math.max(5, score))}%`;
        applyMetricColor(vidBar, vidStatusEl, score, ['Organic', 'Flagged', 'Rigid / Jittery']);
    } else {
        vidScoreEl.textContent = 'N/A';
        vidStatusEl.textContent = 'Audio Only';
        vidStatusEl.className = 'metric-status';
        vidBar.style.width = '0%';
    }

    // 3. Acoustic Metric Card
    const audScoreEl = document.getElementById('audio-score');
    const audStatusEl = document.getElementById('audio-status');
    const audBar = document.getElementById('audio-bar');

    if (data.audio_fake_prob !== null && data.audio_fake_prob !== undefined) {
        const score = data.audio_fake_prob;
        audScoreEl.textContent = `${score}%`;
        audBar.style.width = `${Math.min(100, Math.max(5, score))}%`;
        applyMetricColor(audBar, audStatusEl, score, ['Natural', 'Artifacts', 'TTS / Vocoder']);
    } else {
        audScoreEl.textContent = 'N/A';
        audStatusEl.textContent = 'No Audio';
        audStatusEl.className = 'metric-status';
        audBar.style.width = '0%';
    }

    // 4. Cross-Modal Sync Card
    const syncScoreEl = document.getElementById('sync-score');
    const syncStatusEl = document.getElementById('sync-status');
    const syncBar = document.getElementById('sync-bar');

    if (data.sync_mismatch_prob !== null && data.sync_mismatch_prob !== undefined) {
        const score = data.sync_mismatch_prob;
        syncScoreEl.textContent = `${score}%`;
        syncBar.style.width = `${Math.min(100, Math.max(5, score))}%`;
        applyMetricColor(syncBar, syncStatusEl, score, ['Aligned', 'Drifting', 'Desynchronized']);
    } else {
        syncScoreEl.textContent = 'N/A';
        syncStatusEl.textContent = 'Unimodal';
        syncStatusEl.className = 'metric-status';
        syncBar.style.width = '0%';
    }
}

function applyMetricColor(barEl, statusEl, score, labels) {
    barEl.classList.remove('bar-success', 'bar-warning', 'bar-danger');
    statusEl.classList.remove('text-success', 'text-warning', 'text-danger');

    if (score >= 60) {
        barEl.classList.add('bar-danger');
        statusEl.classList.add('text-danger');
        statusEl.textContent = labels[2];
    } else if (score >= 40) {
        barEl.classList.add('bar-warning');
        statusEl.classList.add('text-warning');
        statusEl.textContent = labels[1];
    } else {
        barEl.classList.add('bar-success');
        statusEl.classList.add('text-success');
        statusEl.textContent = labels[0];
    }
}

// Export Forensic JSON Report
function exportReportJSON() {
    if (!latestReportData) return;

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(latestReportData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `forensic_report_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
}

// Reset App State
function resetApp() {
    stopScanningAnimation();

    resultsSection.classList.add('hidden');
    loadingState.classList.add('hidden');

    document.querySelector('.mode-tabs').classList.remove('hidden');
    clearSelectedFile();
    document.getElementById('url-input').value = '';

    switchMode(activeMode);
}

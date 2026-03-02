let currentMode = 'upload';
let selectedFile = null;

// Tab Switching Logic
function switchTab(mode) {
    currentMode = mode;

    // Update Buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('onclick').includes(mode)) {
            btn.classList.add('active');
        }
    });

    // Update Sections
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('url-section').classList.add('hidden');

    document.getElementById(`${mode}-section`).classList.remove('hidden');
    document.getElementById(`${mode}-section`).classList.add('active');
}

// Drag & Drop / File Input Logic
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const filePreview = document.getElementById('file-preview');
const fileName = document.getElementById('file-name');

fileInput.addEventListener('change', handleFileSelect);

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
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
    }
});

function handleFileSelect() {
    if (fileInput.files.length > 0) {
        selectedFile = fileInput.files[0];
        fileName.textContent = selectedFile.name;
        dropZone.classList.add('hidden');
        filePreview.classList.remove('hidden');
    }
}

function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    filePreview.classList.add('hidden');
    dropZone.classList.remove('hidden');
}

// Form Submission & API Interaction
async function submitAnalysis() {
    const formData = new FormData();

    if (currentMode === 'upload') {
        if (!selectedFile) {
            alert('Please select a file first.');
            return;
        }
        formData.append('input_type', 'file');
        formData.append('file', selectedFile);
    } else {
        const urlInput = document.getElementById('url-input').value;
        if (!urlInput) {
            alert('Please enter a valid URL.');
            return;
        }
        formData.append('input_type', 'url');
        formData.append('url', urlInput);
    }

    // Enter Loading State
    document.querySelector('.tab-container').classList.add('hidden');
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('url-section').classList.add('hidden');
    document.getElementById('analyze-btn').classList.add('hidden');

    document.getElementById('loading-state').classList.remove('hidden');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Something went wrong processing the media.');
        }

        displayResults(data);

    } catch (error) {
        alert(`Error: ${error.message}`);
        resetForm(); // Bounce back on failure
    }
}

function displayResults(data) {
    // Hide Loading
    document.getElementById('loading-state').classList.add('hidden');

    // Show Results Section
    document.getElementById('results-section').classList.remove('hidden');

    // Populate Metrics
    const finalScore = data.final_fake_prob;

    // Set individual metrics
    document.getElementById('video-score').textContent = `${data.video_fake_prob}%`;
    document.getElementById('audio-score').textContent = data.has_audio ? `${data.audio_fake_prob}%` : 'N/A';
    document.getElementById('sync-score').textContent = data.has_audio ? `${data.sync_mismatch_prob}%` : 'N/A';

    // Style the Verdict Banner
    const banner = document.getElementById('verdict-banner');
    const verdictIcon = document.getElementById('verdict-icon');
    const verdictTitle = document.getElementById('verdict-title');
    const overallScore = document.getElementById('overall-score');

    // Clear previous classes
    banner.classList.remove('border-danger', 'border-warning', 'border-success');
    verdictIcon.classList.remove('text-danger', 'text-warning', 'text-success', 'ph-warning-circle', 'ph-check-circle', 'ph-warning');

    if (finalScore >= 60) {
        banner.classList.add('border-danger');
        verdictIcon.classList.add('text-danger', 'ph-warning-circle');
        verdictTitle.textContent = "Likely AI Manipulated";
        verdictTitle.classList.add('text-danger');
    } else if (finalScore >= 40) {
        banner.classList.add('border-warning');
        verdictIcon.classList.add('text-warning', 'ph-warning');
        verdictTitle.textContent = "Suspicious Content";
        verdictTitle.classList.add('text-warning');
    } else {
        banner.classList.add('border-success');
        verdictIcon.classList.add('text-success', 'ph-check-circle');
        verdictTitle.textContent = "Likely Authentic";
        verdictTitle.classList.add('text-success');
    }

    overallScore.innerHTML = `Overall Fake Probability: <span class="${verdictTitle.className}">${finalScore}%</span>`;
}

function resetForm() {
    // Hide Results/Loading
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('loading-state').classList.add('hidden');

    // Restore Form Elements
    document.querySelector('.tab-container').classList.remove('hidden');
    document.getElementById('analyze-btn').classList.remove('hidden');

    // Clear selections
    clearFile();
    document.getElementById('url-input').value = "";

    // Return to current tab UI
    switchTab(currentMode);
}

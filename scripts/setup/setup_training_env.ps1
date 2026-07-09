# setup_training_env.ps1
# Automates setting up the Python virtual environment for deep learning training.

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  STVDS AI Training Environment Setup     " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Verify Python Installation
Write-Host "`n[Step 1] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>&1
    Write-Host "  Found: $pythonVersion"
} catch {
    Write-Error "Python is not installed or not in your PATH. Please install Python 3.10+."
}

# 2. Setup Virtual Environment
Write-Host "`n[Step 2] Setting up virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $PSScriptRoot "..\..\venv"
$venvExists = Test-Path $venvPath

if ($venvExists) {
    Write-Host "  Virtual environment already exists at: $venvPath"
} else {
    Write-Host "  Creating virtual environment..."
    & python -m venv venv
    Write-Host "  Created successfully."
}

# Resolve paths to pip and python inside venv
$pipPath = Join-Path $venvPath "Scripts\pip.exe"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"

# 3. Upgrade pip and core tools
Write-Host "`n[Step 3] Upgrading core pip packages..." -ForegroundColor Yellow
& $pipPath install --upgrade pip setuptools wheel

# 4. Check for NVIDIA CUDA GPU
Write-Host "`n[Step 4] Checking for NVIDIA GPU & CUDA capability..." -ForegroundColor Yellow
$cudaDetected = $false
try {
    # Check if nvidia-smi command works
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvidiaSmi) {
        Write-Host "  NVIDIA Graphics Card detected."
        # Run a quick check using python to see if CUDA wheels are needed
        $cudaCheck = & python -c "import subprocess; print('OK')" 2>&1
        if ($cudaCheck -eq "OK") {
            $cudaDetected = $true
        }
    } else {
        Write-Host "  No NVIDIA GPU detected (nvidia-smi not found). Installing CPU packages."
    }
} catch {
    Write-Host "  Check failed. Defaulting to CPU packages."
}

# 5. Install PyTorch and Deep Learning Libraries
Write-Host "`n[Step 5] Installing PyTorch..." -ForegroundColor Yellow
if ($cudaDetected) {
    Write-Host "  Installing PyTorch with CUDA 11.8 support..."
    & $pipPath install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
} else {
    Write-Host "  Installing PyTorch (CPU version)..."
    & $pipPath install torch torchvision torchaudio
}

# 6. Install Ultralytics and OCR dependencies
Write-Host "`n[Step 6] Installing Ultralytics (YOLOv8) & EasyOCR..." -ForegroundColor Yellow
& $pipPath install ultralytics easyocr

# 7. Install other backend requirements
Write-Host "`n[Step 7] Installing remaining dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path $PSScriptRoot "..\..\requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "  Installing from requirements.txt..."
    & $pipPath install -r $requirementsPath
}

$backendRequirementsPath = Join-Path $PSScriptRoot "..\..\backend\requirements.txt"
if (Test-Path $backendRequirementsPath) {
    Write-Host "  Installing from backend/requirements.txt..."
    & $pipPath install -r $backendRequirementsPath
}

# 8. Verify installation
Write-Host "`n[Step 8] Verifying environment setup..." -ForegroundColor Yellow
& $pythonPath -c "import torch; print('  Torch Version:', torch.__version__); print('  CUDA Available:', torch.cuda.is_available())"
& $pythonPath -c "import ultralytics; print('  Ultralytics (YOLOv8) Version:', ultralytics.__version__)"
& $pythonPath -c "import easyocr; print('  EasyOCR Version: loaded successfully')"

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "  SETUP COMPLETE!                        " -ForegroundColor Green
Write-Host "  Activate the environment using:        " -ForegroundColor Green
Write-Host "  .\venv\Scripts\activate                " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

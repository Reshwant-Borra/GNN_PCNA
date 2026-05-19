@echo off
REM GNN-PCNA dependency installer for Windows.
REM Usage:
REM   install.bat          (CPU-only, default)
REM   install.bat cu118    (NVIDIA GPU, CUDA 11.8)
REM   install.bat cu121    (NVIDIA GPU, CUDA 12.1)

SET CUDA=%1
IF "%CUDA%"=="" SET CUDA=cpu

echo === Step 1: PyTorch (%CUDA%) ===
pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/%CUDA%
IF ERRORLEVEL 1 GOTO error

echo === Step 2: PyG sparse ops (%CUDA%) ===
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.1.0+%CUDA%.html
IF ERRORLEVEL 1 GOTO error

echo === Step 3: PyTorch Geometric ===
pip install torch-geometric==2.5.3
IF ERRORLEVEL 1 GOTO error

echo === Step 4: All other dependencies ===
pip install biopython==1.83 scipy==1.13.1 numpy==1.26.4 scikit-learn==1.5.2 tqdm==4.66.5 requests==2.32.3 beautifulsoup4==4.12.3 streamlit==1.38.0 matplotlib==3.9.2 pandas==2.2.3
IF ERRORLEVEL 1 GOTO error

echo.
echo === Verify ===
python -c "import torch; import torch_geometric; import torch_scatter; print('OK -- torch', torch.__version__, '| pyg', torch_geometric.__version__)"
GOTO end

:error
echo INSTALL FAILED. Check error above.
exit /b 1

:end

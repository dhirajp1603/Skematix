@echo off
REM Install PyTorch and required packages for semantic segmentation inference

echo.
echo Installing PyTorch (CPU version) and dependencies...
echo This may take a few minutes...
echo.

REM Install PyTorch CPU version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Install other dependencies
pip install opencv-python numpy pillow

echo.
echo ✓ Installation complete!
echo.
echo To verify installation, run:
echo   python -c "import torch; print('PyTorch version:', torch.__version__)"
echo.
echo To test semantic segmentation:
echo   python test_semantic_segmentation.py
echo.

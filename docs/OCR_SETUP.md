# OCR Setup for Image Text Extraction

## Install Tesseract OCR

### macOS:
```bash
brew install tesseract
```

### Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr
```

### Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Install Python Package
```bash
pip install pytesseract
```

## Verify Installation
```python
import pytesseract
print(pytesseract.get_tesseract_version())
```

The image text extraction will work automatically once Tesseract is installed.
# Installing Tesseract OCR (Optional)

Tesseract is only needed if you're working with scanned PDFs. For regular digital PDFs, you can safely ignore the warning.

## macOS (using Homebrew)
```bash
brew install tesseract
```

## Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

## Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your PATH

## Verify Installation
```bash
tesseract --version
```

## After Installation
The warning should disappear when you restart the app:
```bash
uv run streamlit run apps/pdf_manager_app.py
```

## Note
- If you don't process scanned PDFs, you can safely ignore this warning
- The app works perfectly fine without Tesseract for 99% of PDFs
- This is an optional enhancement, not a requirement
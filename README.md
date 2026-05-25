# Automated Invoice Processing and Anomaly Detection

A complete end-to-end pipeline that reads invoice images, extracts structured data using OCR, and flags suspicious invoices using Machine Learning.

---


## What does this project do?

Iinstead of someone manually going through hundreds of invoices and typing out the details, this system does it automatically. It reads the invoice image, extracts things like the invoice number, vendor name, total amount, and line items — and then runs some checks to see if anything looks off (like an unusually high amount or a zero-dollar invoice).

The pipeline has four main steps:

1. **Clean up the image** — remove noise and make the text sharp using OpenCV
2. **Read the text** — use Tesseract OCR to extract text from the cleaned image
3. **Pull out the fields** — use regex to find invoice number, date, vendor, amount etc.
4. **Detect anomalies** — use Z-score + Isolation Forest ML to flag suspicious invoices

---

## Project files

```
invoice_project/
│
├── invoices/                   ← put your invoice images here
│
├── output/
│   ├── extracted_texts/        ← OCR output saved as .txt (one per invoice)
│   ├── invoices.csv            ← all extracted data in structured format
│   ├── anomaly_results.csv     ← anomaly detection results with reasons
│   └── final_results.csv      ← final output 
│
├── preprocessing.py            ← cleans the invoice image before OCR
├── ocr_engine.py               ← runs Tesseract OCR and saves .txt files
├── parser.py                   ← extracts specific fields using regex
├── anomaly_detector.py         ← detects suspicious invoices using ML
├── visualizations.py           ← generates box plots and scatter plots
├── main.py                     ← runs everything from start to finish
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Meghna-K03/Invoice-processing-and-anomaly-detection-project
cd OCR
```

### 2. Install Python libraries

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract

Tesseract is the OCR engine this project uses — it needs to be installed separately from Python.

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

After installing, make sure this line in `ocr_engine.py` points to the right path:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt install tesseract-ocr
```

### 4. Add your invoice images

Download the dataset from Kaggle:
https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr

Put the images inside the `invoices/` folder.

---

## How to run

### Run everything at once:
```bash
python main.py
```

### Or step by step:

```bash
# Step 1 — OCR (only need to run this once, it's slow)
python ocr_engine.py

# Step 2 — Parse the extracted text into CSV
python parser.py

# Step 3 — Detect anomalies
python anomaly_detector.py

# Step 4 — Generate visualizations
python visualizations.py
```

> **Note:**  run `ocr_engine.py` only once and save the text as `.txt` files. After that, `parser.py` reads directly from those files — so if we need to tweak the regex, we don't have to wait for OCR to run again every time. This saved a lot of time during development.

---

## Results

| Metric | Value |
|--------|-------|
| Total invoices processed | 117 |
| Successfully parsed | 111 |
| Parsing success rate | 94.8% |
| Anomalies detected | 22 |
| Duplicate pairs found | 0 |

### What kinds of anomalies were found?

| Type | Count |
|------|-------|
| Flagged by Isolation Forest ML | 12 |
| Zero total amount | 6 |
| Suspiciously low (< $10) | 4 |
| Unusually high (> $50,000) | 4 |

---

## Anomaly detection approach

used three methods together so nothing gets missed:

- **Z-score** — checks if a vendor's invoice amount is unusual compared to their own history
- **Isolation Forest** — ML model that learns what "normal" looks like and flags anything different
- **Rule-based checks** — simple thresholds like zero amounts, very low amounts, future dates

---

## Dataset

| Detail | Info |
|--------|------|
| Source | Kaggle |
| Link | https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr |
| Images used | 117 from Batch 1 |
| Date range | 2011-2021 |

---

## Known limitations

- Some invoices have a two-column layout where OCR reads the left and right sides as completely separate blocks of text — this makes it hard to match quantities with prices
- Vendor name extraction is not perfect when seller and client names end up on the same line
- The 90-day old invoice check is disabled here since this is a historical dataset — in a real system it would be on

---

## Author

Meghna K


Machine Learning intern project

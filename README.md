# Automated Invoice Processing and Anomaly Detection

A complete end-to-end pipeline that reads invoice images, extracts structured data using OCR, and flags suspicious invoices using Machine Learning.

---

## Project Overview

Manual invoice processing in Accounts Payable (AP) departments is slow, error-prone, and vulnerable to fraud. This project automates the entire workflow — from reading a raw invoice image to flagging suspicious entries — simulating a real-world task.

---

## What This Project Does

1. Reads raw invoice images from a folder
2. Cleans and prepares each image for OCR (grayscale, noise reduction, binarization)
3. Extracts raw text from each image using Tesseract OCR
4. Parses the raw text to pull out key fields (invoice number, date, vendor, amount, line items)
5. Validates the extracted data using rule-based checks
6. Detects anomalies using Z-score analysis and Isolation Forest ML model
7. Saves everything to CSV files with is_anomaly and anomaly_reason columns

---

## Project Structure


invoice_project/
│
├── invoices/                   ← put your invoice images 
│
├── output/
│   ├── extracted_texts/        ← OCR output saved as .txt files (one per invoice)
│   ├── invoices.csv            ← structured parsed data from all invoices
│   ├── anomaly_results.csv     ← anomaly detection results with reasons
│   └── final_results.csv       ← complete final output
│
├── preprocessing.py            ← cleans up invoice images before OCR
├── ocr_engine.py               ← extracts text from images using Tesseract
├── parser.py                   ← pulls out specific fields from raw OCR text
├── anomaly_detector.py         ← detects suspicious invoices using ML
├── main.py                     ← runs the full pipeline from start to finish
├── requirements.txt            ← list of all Python libraries needed
└── README.md                   ← this file



---

## How to Set Up

### Step 1 — Clone the repository

```bash
git clone https://github.com/yourusername/invoice-project.git
cd invoice-project
```

### Step 2 — Install Python libraries

```bash
pip install -r requirements.txt
```

### Step 3 — Install Tesseract OCR engine

Tesseract is the OCR engine this project uses. It needs to be installed separately.

**Windows:**
Download the installer from:
https://github.com/UB-Mannheim/tesseract/wiki

After installing, make sure this line in `ocr_engine.py` points to the correct path:
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

### Step 4 — Add invoice images

Download the dataset from Kaggle:
https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr

Place your invoice images inside the `invoices/` folder.

---

## How to Run

### Run the full pipeline at once (recommended):

```bash
python main.py
```

This runs all steps automatically and saves the results.

### Or run step by step:

```bash
# Step 1 — extract text from all images and save as .txt files
# only need to run this once — takes a few minutes
python ocr_engine.py

# Step 2 — parse the .txt files and build the invoices CSV
python parser.py

# Step 3 — detect anomalies and save results
python anomaly_detector.py
```

---

## Results on This Dataset

| Metric | Value |
|--------|-------|
| Total invoices processed | 117 |
| OCR extraction accuracy | 94.8% |
| Invoices passing validation | 111 |
| Anomalies detected | 22 |
| Duplicate invoice pairs | 0 |

### Breakdown of anomalies found:

| Anomaly Type | Count |
|-------------|-------|
| Flagged by Isolation Forest ML | 12 |
| Zero total amount | 6 |
| Suspiciously low amount (< $10) | 4 |
| Unusually high amount (> $50,000) | 4 |

---

## Output Files Explained

| File | What it contains |
|------|-----------------|
| `output/invoices.csv` | All 117 invoices with extracted fields like invoice number, date, vendor, total amount |
| `output/anomaly_results.csv` | Same data with added columns: zscore, is_anomaly, anomaly_reason |
| `output/final_results.csv` | Final combined output from the complete pipeline |

---

## Libraries Used

| Library | What it is used for |
|---------|-------------------|
| opencv-python | Reading and preprocessing invoice images |
| pytesseract | Running Tesseract OCR to extract text |
| pandas | Storing and saving invoice data as DataFrames |
| numpy | Numerical operations |
| scikit-learn | Isolation Forest anomaly detection model |
| thefuzz | Fuzzy string matching for duplicate detection |
| Pillow | Image handling support for pytesseract |

---

## Anomaly Detection Approach

This project uses a combination of three methods to detect suspicious invoices:

**1. Z-score Analysis (Statistical)**
Calculates how far each invoice amount is from that vendor's average. A Z-score above 2 means the amount is unusually high or low for that specific vendor.

**2. Isolation Forest (Machine Learning)**
An unsupervised ML algorithm that identifies invoices that behave differently from the rest of the dataset based on Total Amount and Line Items Count. contamination is set to 0.1 meaning we expect about 10% anomalies.

**3. Rule-Based Checks**
Simple but important checks:
- Zero or near-zero amounts (< $10)
- Extremely high amounts (> $50,000)
- Future dates
- Missing dates or invalid date formats

---

## Known Limitations

- Vendor name extraction works well for most invoices but can merge seller and client names together in cases where OCR places them on the same line with single spacing (affects about 10-15% of invoices)
- Math validation (Quantity x Unit Price = Line Total) only applies to invoices where all fields appear on a single line. Split-column invoice layouts make line-level matching unreliable
- Old invoice flagging (> 90 days) is disabled because this dataset contains historical invoices from 2011 to 2021. In a live production system this rule would be enabled

---

## Dataset

| Detail | Info |
|--------|------|
| Name | High Quality Invoice Images for OCR |
| Source | Kaggle |
| Link | https://www.kaggle.com/datasets/osamahosamabdellatif/high-quality-invoice-images-for-ocr |
| Images used | 117 images from Batch 1 |

---

## Author

**Meghna**
ML intern project
Automated Invoice Processing and Anomaly Detection

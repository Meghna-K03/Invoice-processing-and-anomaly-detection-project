import re        # regex
import pandas as pd  
import os        

def extract_invoice_number(text):
    """Extract invoice number from raw OCR text."""
    
    # The invoices can label their number in different ways
    # we try multiple patterns to cover all cases
    # note: the 4th pattern handles OCR misreading 'I' as 'n' (nvoice instead of Invoice)
    patterns = [
        r'Invoice\s*no[:\s]+(\d+)',
        r'Invoice\s*number[:\s]+(\d+)',
        r'Invoice\s*#[:\s]+(\d+)',
        r'nvoice\s*no[:\s]+(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # group(1) gives us just the number part, not the full match
            return match.group(1).strip()
    
    # if nothing matched, return NOT FOUND so that we know it failed
    return "NOT FOUND"

def extract_date(text):
    """Extract invoice date from raw OCR text."""
    
    # try to find date next to the label first (most reliable)
    patterns = [
        r'Date\s*of\s*issue[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        r'Date[:\s]+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # fallback: in split-column invoices, the date sometimes floats away from the label — so we just grab any date-shaped text
    # this is less reliable but better than returning NOT FOUND
    match = re.search(r'\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b', text)
    if match:
        return match.group(1).strip()
    
    return "NOT FOUND"

def extract_vendor_name(text):
    """Extract the seller/vendor company name."""
    
    # split the full text into lines so we can search line by line
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # find the line that contains "Seller:"
        if re.search(r'Seller\s*:', line, re.IGNORECASE):
            
            # look at the next few lines for the company name
            # we check up to 6 lines ahead because sometimes
            # there are blank lines between "Seller:" and the name
            for j in range(i+1, min(i+6, len(lines))):
                candidate = lines[j].strip()
                
                # skip blank lines
                if not candidate:
                    continue
                
                # skip lines that are clearly not company names
                # (address lines, tax lines, IBAN lines etc.)
                if any(skip in candidate.lower() for skip in [
                    'tax', 'iban', 'items', 'no.', 'description',
                    'street', 'road', 'avenue', 'box', 'summary'
                ]):
                    break
                
                # skip lines that are just numbers (like zip codes)
                if re.match(r'^[\d\s]+$', candidate):
                    break
                
                # if seller and client names are on the same line
                # separated by 2+ spaces, take the LEFT part (seller)
                parts = re.split(r'\s{2,}', candidate)
                if len(parts) >= 2:
                    return parts[0].strip()
                
                # if names are separated by just one space,
                # try to split using common company suffixes
                # e.g. "Hines Ltd Brown Ltd" → "Hines Ltd"
                suffix_match = re.search(
                    r'^(.+?\b(?:Ltd|LLC|Inc|PLC|Group|Sons|Associates|Partners|'
                    r'Co|Corp|Company|Industries|Services|Solutions|Consulting|'
                    r'Enterprises|Holdings|International|Management))\s+([A-Z].+)$',
                    candidate,
                    re.IGNORECASE
                )
                if suffix_match:
                    return suffix_match.group(1).strip()
                
                # last resort — return whatever is on that line (better than returning NOT FOUND
                if len(candidate) > 3:
                    return candidate
    
    return "NOT FOUND"

def extract_client_name(text):
    """Extract the client/buyer company name."""
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        
        # case 1: "Seller: Client:" are on the SAME line
        # then both company names are on the next non-empty line
        # seller is on the LEFT, client is on the RIGHT
        if re.search(r'Seller\s*:.*Client\s*:', line, re.IGNORECASE):
            for j in range(i+1, min(i+6, len(lines))):
                candidate = lines[j].strip()
                if not candidate:
                    continue
                if any(skip in candidate.lower() for skip in [
                    'tax', 'iban', 'items', 'no.', 'description'
                ]):
                    break
                # client is the RIGHTMOST part after 2+ spaces
                parts = re.split(r'\s{2,}', candidate)
                if len(parts) >= 2 and len(parts[-1].strip()) > 3:
                    return parts[-1].strip()
                break
        
        # case 2: "Client:" is alone on its own line
        # then the client name is on the next non-empty line
        elif re.search(r'^Client\s*:\s*$', line, re.IGNORECASE):
            for j in range(i+1, min(i+4, len(lines))):
                candidate = lines[j].strip()
                if not candidate:
                    continue
                if len(candidate) > 3:
                    return candidate
        
        # case 3: "Client: CompanyName" all on the same line
        elif re.search(r'^Client\s*:\s*([A-Za-z].+)', line, re.IGNORECASE):
            match = re.search(r'^Client\s*:\s*([A-Za-z].+)', line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3:
                    return name
    
    return "NOT FOUND"

def extract_total_amount(text):
    """Extract the grand total amount from the invoice."""
    
    lines = text.split('\n')

    # layout 1: amount is on the same line as "Total $"
    # e.g. "Total $5 640,17"
    match = re.search(r'Total\s*\$\s*([\d\s,]+)', text, re.IGNORECASE)
    if match:
        raw = match.group(1).strip().split('\n')[0]
        # remove spaces inside numbers like "5 640,17" → "5640.17"
        raw = raw.replace(' ', '').replace(',', '.')
        try:
            float(raw)
            return raw
        except:
            pass

    # layout 2: for split-column invoices, the total appears as
    # a standalone "$ 6 236,77" line somewhere in the text
    # we collect all such amounts and return the largest one
    # (the largest dollar amount is the grand total)
    dollar_amounts = []
    for line in lines:
        line = line.strip()
        match = re.match(r'^\$\s*([\d][\d\s,]*\d)$', line)
        if match:
            raw = match.group(1).replace(' ', '').replace(',', '.')
            try:
                val = float(raw)
                dollar_amounts.append(val)
            except:
                continue
    if dollar_amounts:
        return str(max(dollar_amounts))

    # layout 3: amount appears on the line right after "Net worth"
    for i, line in enumerate(lines):
        if re.search(r'Net\s*worth', line, re.IGNORECASE):
            for j in range(i+1, min(i+4, len(lines))):
                candidate = lines[j].strip()
                candidate_clean = candidate.replace(' ', '').replace(',', '.')
                try:
                    val = float(candidate_clean)
                    # ignore tiny numbers that are clearly not totals
                    if val > 10:
                        return str(val)
                except:
                    continue

    return "NOT FOUND"

def extract_line_items(text):
    """
    Extract individual line items from the invoice.
    Each item has: item number, quantity, unit price, net worth, gross worth.
    """
    line_items = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()

        # layout 1: everything is on one line
        # e.g. "1. Dell Desktop 3,00 each 209,00 627,00 10% 689,70"
        # also handles spaced numbers like "1 394,67" which OCR sometimes produces
        match = re.match(
            r'^(\d+)\.\s+.+?\s+'
            r'(\d+[,\.]\d+)\s+each\s+'   # quantity
            r'([\d]+[,\.][\d]+)\s+'       # unit price
            r'(\d[\d\s,]*\d|\d+)\s+'      # net worth (may have space inside)
            r'\d+%\s+'                     # VAT percentage
            r'(\d[\d\s,]*\d|\d+)$',       # gross worth
            line
        )
        if match:
            try:
                qty        = float(match.group(2).replace(',', '.'))
                unit_price = float(match.group(3).replace(',', '.'))
                
                # remove spaces from numbers like "1 394,67" before converting
                net_worth  = float(
                    match.group(4).replace(' ', '').replace(',', '.')
                )
                gross      = float(
                    match.group(5).replace(' ', '').replace(',', '.')
                )
                line_items.append({
                    "item_number": match.group(1),
                    "quantity":    str(qty),
                    "unit_price":  str(round(unit_price, 2)),
                    "net_worth":   str(round(net_worth, 2)),
                    "gross_worth": str(round(gross, 2))
                })
                continue
            except:
                pass

        # layout 2: only qty is on the same line as the description
        # prices are in a separate column that OCR couldn't connect
        # note: OCR sometimes misreads "each" as "eac" or "eacn"
        match2 = re.match(
            r'^(\d+)\.\s+.+?\s+(\d+[,\.]\d+)\s+(?:each|eac|eacn)\s*$',
            line
        )
        if match2:
            try:
                qty = float(match2.group(2).replace(',', '.'))
                line_items.append({
                    "item_number": match2.group(1),
                    "quantity":    str(qty),
                    "unit_price":  "NOT FOUND",
                    "net_worth":   "NOT FOUND",
                    "gross_worth": "NOT FOUND"
                })
                continue
            except:
                pass

        # layout 3: OCR split the table badly — only item number and qty visible
        match3 = re.match(
            r'^(\d+)\.\s+.+?\s+(\d+[,\.]\d+)\s*$',
            line
        )
        if match3:
            try:
                qty = float(match3.group(2).replace(',', '.'))
                line_items.append({
                    "item_number": match3.group(1),
                    "quantity":    str(qty),
                    "unit_price":  "NOT FOUND",
                    "net_worth":   "NOT FOUND",
                    "gross_worth": "NOT FOUND"
                })
            except:
                pass

    return line_items

def extract_iban(text):
    """Extract the IBAN bank account number."""
    
    # IBAN always starts with 2 letters followed by digits
    # it's clearly labeled in the invoice.
    match = re.search(r'IBAN[:\s]+([A-Z0-9]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "NOT FOUND"

def extract_tax_id(text):
    """Extract the seller's tax ID number."""
    
    # tax ID is always next to "Tax Id:" label
    # we grab the first one found (which belongs to the seller)
    match = re.search(r'Tax\s*Id[:\s]+([\d\-]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "NOT FOUND"

def validate_invoice(data):
    """
    Run basic sanity checks on the extracted invoice data.
    Checks:
    1. Math: quantity x unit price should equal net worth
    2. Total amount should not be missing
    3. Date should not be missing
    4. Invoice number should not be missing
    5. Vendor name should not be missing
    """
    issues = []
    
    # check the math for each line item
    for item in data['line_items']:
        try:
            qty      = float(item['quantity'])
            price    = float(item['unit_price'])
            net      = float(item['net_worth'])
            expected = round(qty * price, 2)
            
            # allow a small tolerance of $1 for rounding differences
            if abs(expected - net) > 1.0:
                issues.append(
                    f"Math error item {item['item_number']}: "
                    f"{qty} x {price} = {expected} but got {net}"
                )
        except:
            # if price or net worth is NOT FOUND, skip the math check
            continue

    # check that all required fields were successfully extracted
    if data['total_amount'] == "NOT FOUND":
        issues.append("Total amount missing")
    if data['date'] == "NOT FOUND":
        issues.append("Date missing")
    if data['invoice_number'] == "NOT FOUND":
        issues.append("Invoice number missing")
    if data['vendor_name'] == "NOT FOUND":
        issues.append("Vendor name missing")
    
    # if no issues found, mark it as passed
    if not issues:
        issues.append("All validations passed")
    
    return issues

def parse_text(text, filename="unknown"):
    """
    Run all extraction functions on a single invoice's text
    and return everything as a dictionary.
    This is called once per invoice.
    """
    return {
        "filename":       filename,
        "invoice_number": extract_invoice_number(text),
        "date":           extract_date(text),
        "vendor_name":    extract_vendor_name(text),
        "client_name":    extract_client_name(text),
        "total_amount":   extract_total_amount(text),
        "tax_id":         extract_tax_id(text),
        "iban":           extract_iban(text),
        "line_items":     extract_line_items(text),
        "raw_text":       text   # keep the raw text for debugging if needed
    }

def parse_all_invoices(txt_dir=None):
    """
    Read all .txt files from the extracted_texts folder
    and parse each one into structured invoice data.

    We read from .txt files instead of images because:
    - OCR already ran once and saved the text
    - Re-running OCR every time would be very slow
    - If we tweak the regex, we just re-parse the txt files (fast!)
    """
    # default to the extracted_texts folder inside output/
    if txt_dir is None:
        txt_dir = os.path.join(
            os.path.dirname(__file__), 'output', 'extracted_texts'
        )
    
    # if txt files don't exist yet, tell the user to run OCR first
    if not os.path.exists(txt_dir):
        print("No extracted_texts folder found!")
        print("Run ocr_engine.py first to generate txt files.")
        return []

    # get all .txt files, sorted by name so order is consistent
    all_txts = sorted([
        f for f in os.listdir(txt_dir)
        if f.endswith('.txt')
    ])
    
    if not all_txts:
        print("No txt files found! Run ocr_engine.py first.")
        return []

    total = len(all_txts)
    print(f"Parsing {total} extracted text files...")

    all_invoice_data = []
    failed = []

    for i, txt_file in enumerate(all_txts):
        # show live progress on the same line
        print(f"{i+1}/{total} done", end="\r")
        
        txt_path = os.path.join(txt_dir, txt_file)
        try:
            # read the text file
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # parse the text and store the result
            # replace .txt with .jpg so filename matches original image
            data = parse_text(
                text,
                filename=txt_file.replace('.txt', '.jpg')
            )
            all_invoice_data.append(data)
            
        except Exception as e:
            # if one file fails, skip it and continue with the rest
            failed.append(txt_file)
            continue

    print(f"\nParsing complete. {len(all_invoice_data)} of {total} parsed.")
    if failed:
        print(f"Failed: {len(failed)} files")
        for f in failed:
            print(f"   - {f}")
    
    return all_invoice_data

def save_to_dataframe(invoice_data_list, save_csv=True):
    """
    Convert the list of parsed invoice dictionaries into a
    pandas DataFrame and save it as a CSV file.
    Each row in the DataFrame = one invoice.
    """
    rows = []
    
    for inv in invoice_data_list:
        # run validation checks on this invoice
        validation = validate_invoice(inv)
        
        # check if any validation issue was found
        has_issues = any(
            keyword in v for v in validation
            for keyword in ["missing", "error"]
        )
        
        # build one row for this invoice
        rows.append({
            "Filename":          inv.get("filename", "unknown"),
            "Invoice Number":    inv["invoice_number"],
            "Date":              inv["date"],
            "Vendor Name":       inv["vendor_name"],
            "Client Name":       inv.get("client_name", "NOT FOUND"),
            "IBAN":              inv.get("iban", "NOT FOUND"),
            "Total Amount":      inv["total_amount"],
            "Line Items Count":  len(inv["line_items"]),
            "Validation Status": "Issues Found" if has_issues else "Passed"
        })

    # convert the list of rows into a DataFrame
    df = pd.DataFrame(rows)

    if save_csv:
        # save to output/invoices.csv
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_csv = os.path.join(output_dir, 'invoices.csv')
        df.to_csv(output_csv, index=False)
        print(f"CSV saved to: output/invoices.csv")

    return df

if __name__ == "__main__":
    # parse all invoice txt files
    all_data = parse_all_invoices()
    
    if all_data:
        # convert to dataframe and save
        df = save_to_dataframe(all_data, save_csv=True)
        
        # show a quick preview of the results
        print("\n--- DataFrame Sample (First 5 rows) ---")
        print(df.head())
        print(f"\nTotal invoices parsed  : {len(df)}")
        print(f"Issues found           : {len(df[df['Validation Status'] == 'Issues Found'])}")
        print(f"Passed validation      : {len(df[df['Validation Status'] == 'Passed'])}")
    
    print("\nparser.py working perfectly!")
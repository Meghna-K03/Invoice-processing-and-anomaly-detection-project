import pytesseract  # pytesseract — the python wrapper for Tesseract OCR engine
import cv2          # opencv — used for reading and processing images
from PIL import Image  # PIL — image handling library (needed by pytesseract internally)
import os           

# tell pytesseract where the Tesseract software is installed on this computer
# without this line, python won't know where to find the OCR engine
# this path will be different on mac/linux 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_pytesseract(image_path):
    """Extract text from image using Pytesseract."""
    
    # read the image directly from the file path
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # convert to grayscale before passing to OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # pass the grayscale image to tesseract and get back the text
    return pytesseract.image_to_string(gray)

def extract_text_from_processed(processed_img):
    """Extract text directly from a preprocessed image array."""
    
    # this is the main function we use in our pipeline
    # it receives an already-preprocessed image (not a file path)
    # the image has already been cleaned up by preprocessing.py
    # so we just pass it straight to tesseract
    return pytesseract.image_to_string(processed_img)

def save_extracted_text(text, output_path):
    """Save extracted text to a .txt file."""
    
    # create the folder if it doesn't exist yet
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # write the extracted text to a .txt file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

def extract_text_from_all_images(invoices_dir=None, save_individual=True, verbose=False):
    """
    Run OCR on all invoice images and save the extracted text.
    
    We save each invoice's text as a separate .txt file so that:
    - parser.py can read from txt files directly (much faster)
    - we don't have to re-run OCR every time we tweak the parser
    - we can open any txt file to see what OCR actually read
    """
    
    # import here to avoid circular imports between files
    from preprocessing import preprocess_image

    # default to the invoices/ folder(if no path is given)
    if invoices_dir is None:
        invoices_dir = os.path.join(os.path.dirname(__file__), 'invoices')

    # where the extracted .txt files will be saved
    output_dir = os.path.join(
        os.path.dirname(__file__), 'output', 'extracted_texts'
    )
    # create the output folder if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # only pick up actual image files from the folder
    valid_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    all_images = [
        f for f in os.listdir(invoices_dir)
        if f.lower().endswith(valid_extensions)
    ]

    if not all_images:
        print("No images found in invoices folder.")
        return []

    total = len(all_images)
    
    # so that the user knows OCR has started
    print(f"Processing OCR for all images...")

    results = []
    failed = []

    for i, filename in enumerate(all_images):
        image_path = os.path.join(invoices_dir, filename)

        # show live progress counter on the same line
        # end="\r" moves back to the start of the line instead of printing a new line
        print(f"{i+1}/{total} done", end="\r")

        if verbose:
            print(f"Processing {i+1}/{total}: {filename}")

        try:
            # step 1: clean up the image using preprocessing.py
            # save_result=False means we don't save the processed image to disk
            # we just need it in memory to pass to OCR
            processed = preprocess_image(
                image_path,
                save_result=False,
                verbose=verbose
            )
            
            # step 2: run OCR on the cleaned image to get raw text
            text = extract_text_from_processed(processed)

            # step 3: save the extracted text as a .txt file
            # filename: batch1-0001.jpg → batch1-0001.txt
            if save_individual:
                txt_filename = os.path.splitext(filename)[0] + '.txt'
                txt_path = os.path.join(output_dir, txt_filename)
                save_extracted_text(text, txt_path)

            # store the result as (filename, text) pair
            results.append((filename, text))

        except Exception as e:
            # if one image fails, log it and move on to the next
            # we don't want one bad image to stop the whole pipeline
            if verbose:
                print(f"Failed on {filename}: {e}")
            failed.append(filename)
            continue

    # print final summary after all images are done
    print(f"\nOCR processing complete. {len(results)} of {total} images processed.")
    
    if failed and verbose:
        print(f"Failed images: {len(failed)}")
        for f in failed:
            print(f"   - {f}")

    return results


if __name__ == "__main__":
    # this runs when you execute ocr_engine.py directly
    # it processes all images and saves their text to output/extracted_texts/
    # only need to run this once — parser.py reads from those txt files
    results = extract_text_from_all_images()
    print(f"Total invoices processed: {len(results)}")
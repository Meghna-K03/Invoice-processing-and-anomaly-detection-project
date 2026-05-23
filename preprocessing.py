import cv2        
import numpy as np 
import os          

def load_image(image_path):
    """Load an image from the given path."""
    
    # cv2.imread reads the image file and returns it as a numpy array
    img = cv2.imread(image_path)
    
    if img is None:
        # raise an error so we know exactly which file failed
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    return img

def convert_to_grayscale(img):
    """Convert image to grayscale."""
    
    # invoice images are in color (BGR format in opencv)
    # we don't need color for reading text — grayscale is enough
    # and also it makes the next steps faster and more accurate
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def reduce_noise(img):
    """Apply noise reduction."""
    
    # scanned invoices often have small dots/specks (noise)
    # fastNlMeansDenoising smooths those out without blurring the text
    # h=10 (filter strength) — tried a few values, 10 worked best
    return cv2.fastNlMeansDenoising(img, h=10)

def binarize(img):
    """Apply thresholding to make text sharp black & white."""
    
    # binarization - converting every pixel to either black or white
    # this makes text stand out clearly from the background
    # THRESH_OTSU automatically figures out the best threshold value
    # based on the image — no need to hardcode a number manually
    _, binary = cv2.threshold(
        img, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return binary

def preprocess_image(image_path, save_result=True, verbose=False):
    """Full preprocessing pipeline for a single image."""
    
    #read the invoice image from disk
    img = load_image(image_path)
    
    #remove color —  only need grayscale for OCR
    gray = convert_to_grayscale(img)
    
    # cleanig  up noise/specks from the scan
    denoised = reduce_noise(gray)
    
    #make text pure black on white background
    final = binarize(denoised)

    # if save_result is True, save the processed image so we can
    # visually check how it looks after preprocessing
    if save_result:
        # build the output folder path relative to this file
        # this way it works on any computer.
        output_dir = os.path.join(
            os.path.dirname(__file__), 'output', 'processed'
        )
        # create the folder if it doesn't already exist
        os.makedirs(output_dir, exist_ok=True)
        
        # use the original filename but save as .png
        filename = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(output_dir, f"processed_{filename}.png")
        cv2.imwrite(out_path, final)
        
        if verbose:
            print(f"Processed image saved to: {out_path}")

    return final


def preprocess_all_images(invoices_dir=None, verbose=False):
    """Process all images in the invoices folder."""
    
    # if no folder is given, default to the 'invoices' folder
    # in the same directory as this script
    if invoices_dir is None:
        invoices_dir = os.path.join(os.path.dirname(__file__), 'invoices')

    # only pick up actual image files — ignore anything else
    # like .txt or .csv files that might be in the folder
    valid_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp')
    all_images = [
        f for f in os.listdir(invoices_dir)
        if f.lower().endswith(valid_extensions)
    ]

    if not all_images:
        print("No images found in invoices folder.")
        return []

    total = len(all_images)
    
    # print so the user knows processing has started
    print(f"Processing images...")

    results = []
    
    for i, filename in enumerate(all_images):
        image_path = os.path.join(invoices_dir, filename)

        # show a live counter on the same line
        # end="\r" moves cursor back to start of line instead of new line
        # so it looks like the number is updating, not scrolling
        print(f"  {i+1}/{total} images done", end="\r")

        if verbose:
            print(f"Processing {i+1}/{total}: {filename}")
        
        try:
            # run the full pipeline on this image
            processed = preprocess_image(
                image_path,
                save_result=True,
                verbose=verbose
            )
            # store the path and processed image together
            # so we can pass them to OCR later
            results.append((image_path, processed))
            
        except Exception as e:
            # if one image fails, skip it and move on
            # we don't want one bad image to stop everything
            if verbose:
                print(f"Skipping {filename} due to error: {e}")
            continue

    # print final count after the loop finishes
    print(f"\nProcessing complete. {len(results)} of {total} images processed.")
    return results


if __name__ == "__main__":
    results = preprocess_all_images()
    print(f"Total images processed: {len(results)}")
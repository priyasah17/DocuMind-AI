
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

import shutil

tesseract_path = (
    shutil.which("tesseract")
    or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = tesseract_path
# If Tesseract is not automatically detected on Windows,
# uncomment the next line and adjust the path if necessary.
# pytesseract.pytesseract.tesseract_cmd = (
#     r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# )


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from ordinary PDFs.
    If a page has no selectable text, use OCR to read its image.
    Returns one dictionary per page.
    """

    extracted_pages = []

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    with pymupdf.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            # First try normal text extraction.
            text = page.get_text("text").strip()

            # If the page is scanned, try OCR.
            if not text:
                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(2, 2),
                    alpha=False,
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples,
                )

                text = pytesseract.image_to_string(
                    image,
                    lang="eng",
                ).strip()

            extracted_pages.append(
                {
                    "page_number": page_number,
                    "content": text,
                }
            )

    return extracted_pages

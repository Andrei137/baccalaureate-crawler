import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pdfplumber
import pytesseract
import requests
from pdf2image import convert_from_path
from pypdf import PdfWriter
from utils.regex import subjects

def extract_pdf_pdfplumber(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(use_text_flow=True)
            if page_text:
                text += page_text + "\n"
    text = text.replace("Ń", "ţ")

    return text


def extract_pdf_ocr(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300)
    all_text = []
    for page in pages:
        text = pytesseract.image_to_string(page, lang="ron", config="--oem 3 --psm 6")
        all_text.append(text)
    return "\n".join(all_text)


def bad_format(text):
    for subject in subjects:
        if not re.search(subject, text, re.IGNORECASE):
            return True
    return False


def extract_pdf_text(pdf_path):
    text = extract_pdf_pdfplumber(pdf_path)
    if not text or bad_format(text):
        return extract_pdf_ocr(pdf_path)
    return text


def write_to_json(path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_from_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def download_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def download_file(url: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    out_path.write_bytes(r.content)


def open_pdf(url: str) -> pdfplumber.PDF:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return pdfplumber.open(BytesIO(r.content))


def find_page(pdf_bytes: bytes, pattern: str) -> int | None:
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if re.search(pattern, text, re.IGNORECASE):
                return i
    return None


def save_pages(pages, path: Path):
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page.page_obj)
    with open(path, "wb") as f:
        writer.write(f)


def is_dir_empty(path: Path) -> bool:
    return not any(path.iterdir())

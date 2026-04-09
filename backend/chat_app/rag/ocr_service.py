import re

import cv2
import fitz
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

_OCR_ENGINE = None

LOW_TEXT_THRESHOLD = 80
SCAN_AVG_THRESHOLD = 120
SCAN_RATIO_THRESHOLD = 0.45
OCR_CONF_THRESHOLD = 0.55
OCR_MAX_PAGES = 40


def get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        _OCR_ENGINE = PaddleOCR(
            lang="vi",
            use_angle_cls=True,
            det_db_box_thresh=0.5,
            det_limit_side_len=2000,
            show_log=False,
        )
    return _OCR_ENGINE


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r" {2,}", " ", text)
    return text.replace("..", ".").strip()


def is_dark_background(img_bgr: np.ndarray) -> bool:
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    return float(gray.mean()) < 110.0


def preprocess_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    # Auto-invert nếu nền tối (case dark screenshot)
    if is_dark_background(img_bgr):
        img_bgr = 255 - img_bgr

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.bilateralFilter(gray, 5, 35, 35)

    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def parse_ocr_result(result, min_conf: float = OCR_CONF_THRESHOLD) -> str:
    texts = []
    if result and result[0]:
        for line in result[0]:
            txt = (line[1][0] or "").strip()
            conf = float(line[1][1]) if len(line[1]) > 1 else 0.0

            if not txt or conf < min_conf:
                continue

            low = txt.lower()
            if "luatvietnam" in low or "www." in low:
                continue

            texts.append(txt)

    return normalize_text(" ".join(texts))


def ocr_page(page: fitz.Page, zoom: float = 300 / 72) -> str:
    engine = get_ocr_engine()

    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Pass 1: OCR ảnh gốc
    raw_text = parse_ocr_result(engine.ocr(img_bgr, cls=True))

    # Pass 2: OCR ảnh đã preprocess
    pre_img = preprocess_for_ocr(img_bgr)
    clean_text = parse_ocr_result(engine.ocr(pre_img, cls=True))

    return clean_text if len(clean_text) >= len(raw_text) else raw_text


def select_pages_for_ocr(docs, avg_chars_per_page: float):
    low_text_pages = [
        i for i, d in enumerate(docs)
        if len((d.page_content or "").strip()) < LOW_TEXT_THRESHOLD
    ]
    low_ratio = (len(low_text_pages) / len(docs)) if docs else 0.0

    need_ocr = (avg_chars_per_page < SCAN_AVG_THRESHOLD) or (low_ratio >= SCAN_RATIO_THRESHOLD)
    if not need_ocr:
        return []

    return low_text_pages[:OCR_MAX_PAGES]

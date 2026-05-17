import cv2
import numpy as np
from PIL import Image
import io


def pil_to_cv(img: Image.Image) -> np.ndarray:
    img_rgb = img.convert("RGB")
    return cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)


def cv_to_pil(img: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def upscale(img: np.ndarray, target_min_dim: int = 1800) -> np.ndarray:
    h, w = img.shape[:2]
    min_dim = min(h, w)
    if min_dim < target_min_dim:
        scale = target_min_dim / min_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    return img


def remove_glare_and_shadows(img: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    kernel_size = max(img.shape[0] // 10, img.shape[1] // 10)
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel_size = max(kernel_size, 51)

    bg = cv2.GaussianBlur(l, (kernel_size, kernel_size), 0)
    diff = cv2.subtract(bg, l)
    norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    l_corrected = cv2.subtract(255, norm)

    lab_corrected = cv2.merge([l_corrected, a, b])
    result = cv2.cvtColor(lab_corrected, cv2.COLOR_LAB2BGR)
    return result


def denoise(img: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(img, None, h=8, hColor=8, templateWindowSize=7, searchWindowSize=21)


def deskew(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_inv = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray_inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 10:
        return img

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    if abs(angle) < 0.5:
        return img

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    return rotated


def enhance_contrast(img: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    lab_enhanced = cv2.merge([l_enhanced, a, b])
    return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)


def sharpen(img: np.ndarray) -> np.ndarray:
    kernel = np.array([
        [ 0, -1,  0],
        [-1,  5, -1],
        [ 0, -1,  0],
    ], dtype=np.float32)
    sharpened = cv2.filter2D(img, -1, kernel)

    blurred = cv2.GaussianBlur(img, (0, 0), 3)
    usm = cv2.addWeighted(img, 1.5, blurred, -0.5, 0)
    result = cv2.addWeighted(sharpened, 0.5, usm, 0.5, 0)
    return result


def clean_background(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    result = img.copy()
    result[mask == 0] = 255
    blended = cv2.addWeighted(img, 0.7, result, 0.3, 0)
    return blended


def enhance_for_ocr(pil_image: Image.Image, steps: dict | None = None) -> tuple[Image.Image, list[str]]:
    if steps is None:
        steps = {
            "upscale": True,
            "glare_shadow": True,
            "denoise": True,
            "deskew": True,
            "contrast": True,
            "sharpen": True,
            "background": True,
        }

    img = pil_to_cv(pil_image)
    applied = []

    if steps.get("upscale", True):
        img = upscale(img)
        applied.append("Resolution upscaling")

    if steps.get("glare_shadow", True):
        img = remove_glare_and_shadows(img)
        applied.append("Glare & shadow removal")

    if steps.get("denoise", True):
        img = denoise(img)
        applied.append("Denoising")

    if steps.get("deskew", True):
        img = deskew(img)
        applied.append("Text straightening (deskew)")

    if steps.get("contrast", True):
        img = enhance_contrast(img)
        applied.append("Contrast enhancement (CLAHE)")

    if steps.get("sharpen", True):
        img = sharpen(img)
        applied.append("Sharpening (USM + kernel)")

    if steps.get("background", True):
        img = clean_background(img)
        applied.append("Background cleaning")

    return cv_to_pil(img), applied


def image_to_bytes(pil_image: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    pil_image.save(buf, format=fmt)
    return buf.getvalue()

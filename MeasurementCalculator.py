import cv2
import numpy as np
import os
import glob
import traceback
import csv

# ---------- Default Image Path ----------
IMAGE_PATH = r"C:\Users\LEdwa\AI_Pokegrader\CardImages\OldGroudon.jpg"

# ---------- Constants (standard TCG card) ----------
CARD_WIDTH_MM = 63.5
CARD_HEIGHT_MM = 88.9

# ---------- Batch Processing Function ----------
def imgFolderToTxtFile(folder_path,
                       output_csv_path,
                       supported_exts=(".jpg", ".jpeg", ".png", ".bmp"),
                       scan_step=5,
                       color_tol=30):
    """
    Outputs CSV rows:
    filename, surface_score, corners_score, centering_h_label, centering_v_label
    (NO percentages)
    """

    folder_path = os.path.abspath(folder_path)
    output_csv_path = os.path.abspath(output_csv_path)

    # Collect image files
    files = []
    for ext in supported_exts:
        files.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
        files.extend(glob.glob(os.path.join(folder_path, f"*{ext.upper()}")))
    files = sorted(set(files))

    if not files:
        print(f"No images found in {folder_path}.")
        return 0

    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    # Append header if file does not yet exist
    write_header = not os.path.exists(output_csv_path)

    with open(output_csv_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)

        if write_header:
            writer.writerow([
                "filename",
                "surface_score",
                "corners_score",
                "centering_h_label",
                "centering_v_label"
            ])

        processed = 0

        for fpath in files:
            fname = os.path.basename(fpath)

            try:
                image = cv2.imread(fpath)
                if image is None:
                    print(f"Skipping unreadable: {fname}")
                    continue

                card_contour = detect_card_contour(image, scan_step=scan_step, color_tol=color_tol)
                if card_contour is None:
                    print(f"No contour found: {fname}")
                    continue

                warped = four_point_transform(image, card_contour)
                warped_h, warped_w = warped.shape[:2]

                ppm_w = warped_w / CARD_WIDTH_MM
                ppm_h = warped_h / CARD_HEIGHT_MM
                pixels_per_mm = (ppm_w + ppm_h) / 2.0
                if pixels_per_mm <= 0:
                    print(f"Invalid px/mm: {fname}")
                    continue

                inner = detect_inner_artwork(warped)
                if inner is None:
                    ix, iy, iw, ih = fallback_inner_box(warped_w, warped_h)
                else:
                    ix, iy, iw, ih = inner

                if iw <= 0 or ih <= 0 or iw > warped_w * 0.95 or ih > warped_h * 0.95:
                    ix, iy, iw, ih = fallback_inner_box(warped_w, warped_h)

                # --- Calculate mm ---
                left_mm = ix / pixels_per_mm
                right_mm = (warped_w - (ix + iw)) / pixels_per_mm
                top_mm = iy / pixels_per_mm
                bottom_mm = (warped_h - (iy + ih)) / pixels_per_mm

                left_mm = min(left_mm, CARD_WIDTH_MM / 2)
                right_mm = min(right_mm, CARD_WIDTH_MM / 2)
                top_mm = min(top_mm, CARD_HEIGHT_MM / 2)
                bottom_mm = min(bottom_mm, CARD_HEIGHT_MM / 2)

                horiz_ratio = min(left_mm, right_mm) / (max(left_mm, right_mm) + 1e-9)
                vert_ratio = min(top_mm, bottom_mm) / (max(top_mm, bottom_mm) + 1e-9)

                # --- ONLY labels, no percentages ---
                psa_h = ratio_to_psa_label(horiz_ratio)
                psa_v = ratio_to_psa_label(vert_ratio)

                surface_score = compute_surface_score(warped)
                corners_score = compute_corners_score(warped)

                # --- Write clean CSV row ---
                writer.writerow([
                    fname,
                    surface_score,
                    corners_score,
                    psa_h,
                    psa_v
                ])

                processed += 1
                print(f"Processed: {fname}")

            except Exception as e:
                print(f"Error processing {fname}: {e}")
                traceback.print_exc()
                continue

    print(f"Completed. {processed} images written to CSV.")
    return processed

# ---------- Helpers ----------
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # tl
    rect[2] = pts[np.argmax(s)]  # br
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # tr
    rect[3] = pts[np.argmax(diff)]  # bl
    return rect

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.hypot(br[0]-bl[0], br[1]-bl[1])
    widthB = np.hypot(tr[0]-tl[0], tr[1]-tl[1])
    maxWidth = int(max(widthA, widthB))
    heightA = np.hypot(tr[0]-br[0], tr[1]-br[1])
    heightB = np.hypot(tl[0]-bl[0], tl[1]-bl[1])
    maxHeight = int(max(heightA, heightB))
    dst = np.array([[0,0],[maxWidth-1,0],[maxWidth-1,maxHeight-1],[0,maxHeight-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

# ---------- New Contour Detection (scan inward for solid border) ----------
def detect_card_contour(image, scan_step=5, color_tol=30):
    """
    Detects card contour by scanning inward from image edges until
    solid border color is found. Returns 4 points (tl, tr, br, bl).
    """
    h, w = image.shape[:2]

    # Sample outer pixels along edges
    top_row = image[0, :, :]
    bottom_row = image[-1, :, :]
    left_col = image[:, 0, :]
    right_col = image[:, -1, :]

    # Average color along edges
    top_color = np.mean(top_row, axis=0)
    bottom_color = np.mean(bottom_row, axis=0)
    left_color = np.mean(left_col, axis=0)
    right_color = np.mean(right_col, axis=0)

    # Scan inward to find first row/col that differs from border
    def find_border_index(line, ref_color):
        for i in range(0, len(line), scan_step):
            if np.linalg.norm(line[i] - ref_color) > color_tol:
                return i
        return 0

    top_y = find_border_index(image[:, w//2, :], top_color)
    bottom_y = h - find_border_index(np.flipud(image[:, w//2, :]), bottom_color)
    left_x = find_border_index(image[h//2, :, :], left_color)
    right_x = w - find_border_index(np.flipud(image[h//2, :, :]), right_color)

    contour_pts = np.array([
        [left_x, top_y],
        [right_x, top_y],
        [right_x, bottom_y],
        [left_x, bottom_y]
    ], dtype="float32")

    print(f"DEBUG: Detected card contour points: {contour_pts}")
    return contour_pts

# ---------- Inner Artwork ----------
def detect_inner_artwork(card_img):
    gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = card_img.shape[:2]
    card_area = w * h
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 0.02 * card_area or area > 0.95 * card_area:
            continue
        x,y,ww,hh = cv2.boundingRect(c)
        if ww < 0.2*w or hh < 0.2*h:
            continue
        candidates.append((area, x,y,ww,hh))
    if not candidates:
        return None
    candidates.sort(reverse=True, key=lambda x: x[0])
    _, x,y,ww,hh = candidates[0]
    return (x,y,ww,hh)

def fallback_inner_box(w, h):
    return (int(w*0.1), int(h*0.1), int(w*0.8), int(h*0.8))

def ratio_to_psa_label(ratio):
    pct = ratio * 100.0
    if pct >= 91.0: return "55/45 (10)"
    elif pct >= 83.0: return "60/40 (9)"
    elif pct >= 75.0: return "65/35 (8)"
    elif pct >= 67.0: return "70/30 (7)"
    elif pct >= 60.0: return "80/20 (6)"
    elif pct >= 50.0: return "85/15 (4-5)"
    else: return "90/10 (3 or worse)"

# ---------- Surface and Corner Scoring ----------
def compute_surface_score(card_img):
    gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    th = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, 11, 7)
    kernel = np.ones((3,3), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)

    edges = cv2.Canny(th, 60, 180)
    damage_ratio = np.count_nonzero(edges > 0) / edges.size
    score = max(0.0, min(10.0, 10.0 * (1 - damage_ratio * 2.5)))

    print(f"Surface debug: damage_ratio={damage_ratio:.4f}, score={score:.1f}")
    return round(score, 1)

def compute_corners_score(card_img, border_px=20):
    h, w = card_img.shape[:2]
    corners_score = []
    debug_info = {}

    corners = {
        'tl': (slice(0, border_px), slice(0, border_px)),
        'tr': (slice(0, border_px), slice(w - border_px, w)),
        'bl': (slice(h - border_px, h), slice(0, border_px)),
        'br': (slice(h - border_px, h), slice(w - border_px, w))
    }

    for key, (yslice, xslice) in corners.items():
        region = card_img[yslice, xslice]
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        edges = cv2.Canny(gray, 50, 150)
        _, th_white = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        local_var = cv2.Laplacian(gray, cv2.CV_64F)
        var_mask = np.abs(local_var) > 20

        damage_mask = np.logical_or(edges > 0, th_white > 0)
        damage_mask = np.logical_or(damage_mask, var_mask)

        edge_pixels = np.count_nonzero(damage_mask)
        total_pixels = damage_mask.size
        damage_ratio = edge_pixels / total_pixels

        score = max(0.0, min(10.0, 10 * (1 - damage_ratio)))
        corners_score.append(score)

        debug_info[key] = {
            'edge_pixels': edge_pixels,
            'total_pixels': total_pixels,
            'damage': damage_ratio,
            'score': score
        }

    for key, info in debug_info.items():
        print(f"{key}: edge_pixels={info['edge_pixels']}, total_pixels={info['total_pixels']}, "
              f"damage={info['damage']:.3f}, score={info['score']:.1f}")

    return round(np.mean(corners_score), 1)

# ---------- Main ----------
def main():
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        raise ValueError(f"Could not read image at {IMAGE_PATH}")

    card_contour = detect_card_contour(image)
    if card_contour is None:
        raise ValueError("Card contour not detected.")

    warped = four_point_transform(image, card_contour)
    warped_h, warped_w = warped.shape[:2]

    ppm_w = warped_w / CARD_WIDTH_MM
    ppm_h = warped_h / CARD_HEIGHT_MM
    pixels_per_mm = (ppm_w + ppm_h) / 2.0
    if pixels_per_mm <= 0:
        raise ValueError("Invalid pixel/mm calculation.")

    inner = detect_inner_artwork(warped)
    if inner is None:
        ix, iy, iw, ih = fallback_inner_box(warped_w, warped_h)
    else:
        ix, iy, iw, ih = inner

    if iw <= 0 or ih <= 0 or iw > warped_w*0.95 or ih > warped_h*0.95:
        ix, iy, iw, ih = fallback_inner_box(warped_w, warped_h)

    left_mm = ix / pixels_per_mm
    right_mm = (warped_w - (ix + iw)) / pixels_per_mm
    top_mm = iy / pixels_per_mm
    bottom_mm = (warped_h - (iy + ih)) / pixels_per_mm

    left_mm = min(left_mm, CARD_WIDTH_MM / 2)
    right_mm = min(right_mm, CARD_WIDTH_MM / 2)
    top_mm = min(top_mm, CARD_HEIGHT_MM / 2)
    bottom_mm = min(bottom_mm, CARD_HEIGHT_MM / 2)

    horiz_ratio = min(left_mm, right_mm) / (max(left_mm, right_mm) + 1e-9)
    vert_ratio = min(top_mm, bottom_mm) / (max(top_mm, bottom_mm) + 1e-9)
    psa_h = ratio_to_psa_label(horiz_ratio)
    psa_v = ratio_to_psa_label(vert_ratio)

    surface_score = compute_surface_score(warped)
    corners_score = compute_corners_score(warped)

    print(f"warped_px: {warped_w}x{warped_h}, pixels_per_mm: {pixels_per_mm:.4f}")
    print(f"Left mm: {left_mm:.2f}  Right mm: {right_mm:.2f}  Top mm: {top_mm:.2f}  Bottom mm: {bottom_mm:.2f}")
    print(f"(surface:{surface_score}, corners:{corners_score}, "
          f"centering_h:{horiz_ratio*100:.1f}% [{psa_h}], "
          f"centering_v:{vert_ratio*100:.1f}% [{psa_v}])")

if __name__ == "__main__":
    # single-image main() still usable
    # main()

    # or process whole folder into trainingData.txt:
    # (File Name, Surface score, Centering Horizontal score, Centering Vertical score). No percentages, just ratios.
    images_folder = r"C:\Users\LEdwa\AI_Pokegrader\CardImages"
    training_file = r"C:\Users\LEdwa\AI_Pokegrader\trainingData.txt"
    imgFolderToTxtFile(images_folder, training_file)

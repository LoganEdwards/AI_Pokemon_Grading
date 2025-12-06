import cv2
import numpy as np
import os
import glob
import traceback
import csv

from paths import resource_path

# ---------- Constants (standard TCG card) ----------
CARD_WIDTH_MM = 63.5
CARD_HEIGHT_MM = 88.9


def process_single_card(IMAGE_PATH: str):
    # ---------- Process Single Image ----------
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

    # Centering differences (mm imbalance)
    horiz_diff = abs(left_mm - right_mm)
    vert_diff = abs(top_mm - bottom_mm)

    def mm_to_center_decimal(diff):
        """
        Convert mm difference to standardized centering decimal:
        0.55, 0.60, 0.65, 0.70, 0.80, 0.85, 0.90
        """
        if diff <= 1:        # ~55/45
            return 0.55
        elif diff <= 2:      # ~60/40
            return 0.60
        elif diff <= 3:      # ~65/35
            return 0.65
        elif diff <= 4:      # ~70/30
            return 0.70
        elif diff <= 6:      # ~80/20
            return 0.80
        elif diff <= 8:      # ~85/15
            return 0.85
        else:                # ~90/10 or worse
            return 0.90

    # Assign grading decimals
    psa_h = mm_to_center_decimal(horiz_diff)
    psa_v = mm_to_center_decimal(vert_diff)

    surface_score = compute_surface_score(warped)
    corners_score = compute_corners_score(warped)

    # Debug printout
    # print(f"warped_px: {warped_w}x{warped_h}, pixels_per_mm: {pixels_per_mm:.4f}")
    # print(f"Left mm: {left_mm:.2f}  Right mm: {right_mm:.2f}  Top mm: {top_mm:.2f}  Bottom mm: {bottom_mm:.2f}")
    # print(f"(surface:{surface_score}, corners:{corners_score}, "
    #       f"centering_h:{psa_h}, "
    #       f"centering_v:{psa_v}])")    

    return {
        "surface": surface_score,
        "corners": corners_score,
        "centering_h": psa_h,
        "centering_v": psa_v,
    }

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

    with open(output_csv_path, "a", newline="", encoding="utf-8") as fout:
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

                # Centering differences (mm imbalance)
                horiz_diff = abs(left_mm - right_mm)
                vert_diff = abs(top_mm - bottom_mm)

                def mm_to_center_decimal(diff):
                    """
                    Convert mm difference to standardized centering decimal:
                    0.55, 0.60, 0.65, 0.70, 0.80, 0.85, 0.90
                    """
                    if diff <= 1:        # ~55/45
                        return 0.55
                    elif diff <= 2:      # ~60/40
                        return 0.60
                    elif diff <= 3:      # ~65/35
                        return 0.65
                    elif diff <= 4:      # ~70/30
                        return 0.70
                    elif diff <= 6:      # ~80/20
                        return 0.80
                    elif diff <= 8:      # ~85/15
                        return 0.85
                    else:                # ~90/10 or worse
                        return 0.90

                # Assign grading decimals
                psa_h = mm_to_center_decimal(horiz_diff)
                psa_v = mm_to_center_decimal(vert_diff)

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

def detect_card_contour(image, scan_step=1, color_tol=20, min_border_width_ratio=0.05,
                        sample_lines=7):
    """
    Wrapper that returns 4 corner points (tl, tr, br, bl) suitable for four_point_transform().
    Internally uses detect_outer_border (averaging across several center scan lines to be robust).
    """
    h, w = image.shape[:2]

    # If your detect_outer_border is the single-line version, we can call it multiple times
    # on different sample rows/cols and average the results to reduce noise.
    lefts, rights, tops, bottoms = [], [], [], []

    # sample across center +/- offsets
    mid_y = h // 2
    mid_x = w // 2
    offsets = list(range(-(sample_lines//2), (sample_lines//2) + 1))
    # clamp offsets to image
    offsets = [o for o in offsets if abs(o) < min(h//2, w//2)]

    for o in offsets:
        # sample horizontal scan (for top/bottom) using column at mid_x + o
        col_x = np.clip(mid_x + o, 0, w-1)
        row_y = np.clip(mid_y + o, 0, h-1)

        # Build small subimages (1px wide/tall) to pass to detect_outer_border scanning functions.
        # detect_outer_border expects a full image but scans center lines internally; calling it
        # repeatedly on the same image is OK — we just want to pass different center positions.
        # To avoid rewriting detect_outer_border signature, we'll temporarily shift the image by
        # padding so its center aligns with the offset. Simpler approach: call detect_outer_border
        # once and then re-run simple line scans locally here — below is a direct local scan.

        # local helper scan that matches detect_outer_border logic for one column/row:
        def scan_col(col_x_inner):
            col = image[:, col_x_inner, :]
            top_color = np.mean(image[0, :, :], axis=0)
            bottom_color = np.mean(image[-1, :, :], axis=0)
            # find first different pixel from top
            top_idx = 0
            for i in range(0, h, scan_step):
                if np.linalg.norm(col[i] - top_color) > color_tol:
                    top_idx = i
                    break
            # find first different pixel from bottom
            bottom_idx = 0
            for i in range(0, h, scan_step):
                if np.linalg.norm(col[h-1-i] - bottom_color) > color_tol:
                    bottom_idx = h-1-i
                    break
            # convert bottom_idx to distance from bottom
            bottom_px = h - 1 - bottom_idx
            return top_idx, bottom_px

        def scan_row(row_y_inner):
            row = image[row_y_inner, :, :]
            left_color = np.mean(image[:, 0, :], axis=0)
            right_color = np.mean(image[:, -1, :], axis=0)
            left_idx = 0
            for i in range(0, w, scan_step):
                if np.linalg.norm(row[i] - left_color) > color_tol:
                    left_idx = i
                    break
            right_idx = 0
            for i in range(0, w, scan_step):
                if np.linalg.norm(row[w-1-i] - right_color) > color_tol:
                    right_idx = w-1-i
                    break
            right_px = w - 1 - right_idx
            return left_idx, right_px

        t, b = scan_col(col_x)
        l, r = scan_row(row_y)

        lefts.append(l)
        rights.append(r)
        tops.append(t)
        bottoms.append(b)

    # average the samples
    left_px = int(np.median(lefts))
    right_px = int(np.median(rights))
    top_px = int(np.median(tops))
    bottom_px = int(np.median(bottoms))

    # Sanity minimum
    min_px = int(min(h, w) * min_border_width_ratio)
    left_px = max(left_px, min_px)
    right_px = max(right_px, min_px)
    top_px = max(top_px, min_px)
    bottom_px = max(bottom_px, min_px)

    # Convert distances-from-edges to corner coordinates (x,y)
    tl = (left_px, top_px)
    tr = (w - right_px - 1, top_px)
    br = (w - right_px - 1, h - bottom_px - 1)
    bl = (left_px, h - bottom_px - 1)

    contour_pts = np.array([tl, tr, br, bl], dtype="float32")
    # Optional: debug print
    # print(f"DEBUG wrapper contour pts: {contour_pts}")
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
    """
    Convert measured centering ratio into standardized decimal (first number).
    Ratio is min/max, close to 0.5 -> 55/45, worse -> 90/10
    """
    # Convert ratio (0-1) into imbalance percentage
    imbalance = (1 - ratio) * 100  # bigger imbalance = worse centering
    if imbalance <= 10:        # ~55/45
        return 0.55
    elif imbalance <= 20:      # ~60/40
        return 0.60
    elif imbalance <= 30:      # ~65/35
        return 0.65
    elif imbalance <= 40:      # ~70/30
        return 0.70
    elif imbalance <= 55:      # ~80/20
        return 0.80
    elif imbalance <= 65:      # ~85/15
        return 0.85
    else:                      # ~90/10 or worse
        return 0.90

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

    # print(f"Surface debug: damage_ratio={damage_ratio:.4f}, score={score:.1f}")
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

    # for key, info in debug_info.items():
    #     print(f"{key}: edge_pixels={info['edge_pixels']}, total_pixels={info['total_pixels']}, "
    #           f"damage={info['damage']:.3f}, score={info['score']:.1f}")

    return round(np.mean(corners_score), 1)

if __name__ == "__main__":
    # single-image using user submitted path:
    testImagePath = resource_path(os.path.join("referenceImages", "DarkBackgroundReferenceImage.jpg"))
    process_single_card(testImagePath)

    # or process whole folder into trainingData.txt:
    # (File Name, Surface score, Centering Horizontal score, Centering Vertical score). No percentages, just ratios.
    # images_folder = resource_path(os.path.join("PSA Cards"))
    # training_file = resource_path(os.path.join("trainingData.txt"))
    # imgFolderToTxtFile(images_folder, training_file)
    
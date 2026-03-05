import os
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from Ctrls import PathCtrl

_MAX_IMAGE_COUNT = 30
_MIN_IMAGE_COUNT = 10
_IMAGE_EXT = set(['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'])


class WatermarkStats:
    def __init__(self, aspect_ratio: int):
        self.img_list: list[np.ndarray] = []
        self.img_aspect_ratio = aspect_ratio
        self.size_counts: dict[tuple[int, int], int] = defaultdict(int)

    def add_img(self, img: np.ndarray, w: int, h: int):
        if len(self.img_list) >= _MAX_IMAGE_COUNT:
            return
        self.img_list.append(img)
        self.size_counts[(w, h)] += 1

    def has_enough_images(self) -> bool:
        return len(self.img_list) >= _MIN_IMAGE_COUNT

    def most_common_size(self) -> tuple[int, int]:
        return max(self.size_counts.items(), key=lambda x: x[1])[0]

    def img_count(self) -> int:
        return len(self.img_list)


def _thumbnail_filter(path: Path) -> bool:
    return len(path.stem) == 64 and path.suffix.lower() in _IMAGE_EXT


def _group_images_by_size(image_folder: str) -> dict[int, WatermarkStats]:
    image_files = [f for f in Path(image_folder).iterdir()
                   if _thumbnail_filter(f)]

    watermark_stats: dict[int, WatermarkStats] = {}

    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        h, w = img.shape[:2]
        img_aspect_ratio = int(round((w / h) * 100))
        if img_aspect_ratio not in watermark_stats:
            watermark_stats[img_aspect_ratio] = WatermarkStats(
                img_aspect_ratio)
        watermark_stats[img_aspect_ratio].add_img(img, w, h)

    return {k: v for k, v in watermark_stats.items() if v.has_enough_images()}


def _differ_gray(stats: WatermarkStats) -> np.ndarray:
    tw, th = stats.most_common_size()
    # 1. calculate pixel standard deviation
    img_array: list[np.ndarray] = []
    for img in stats.img_list:
        h, w = img.shape[:2]
        if w != tw or h != th:
            img = cv2.resize(img, (tw, th), interpolation=cv2.INTER_LINEAR)
        img_array.append(img)

    roi_array = np.array(img_array)
    pixel_std = np.std(roi_array, axis=0, dtype=np.float32)
    std_gray = np.mean(pixel_std, axis=2).astype(np.uint8)

    # 2. normalize, range [std_min, std_max] scales to [0, 255]
    std_min = std_gray.min()
    std_max = std_gray.max()
    if std_max > std_min:
        scale = 255 / (std_max - std_min)
        std_normalized = ((std_gray - std_min) * scale).astype(np.uint8)
    else:
        std_normalized = std_gray

    return std_normalized


def extract_watermark(thumbnail_folder: str) -> list[str]:
    watermark_stats_groups = _group_images_by_size(thumbnail_folder)

    file_urls = []
    for aspect_ratio, watermark_stats in watermark_stats_groups.items():
        std_normalized = _differ_gray(watermark_stats)
        file_name = f"_{aspect_ratio}_{watermark_stats.img_count()}.png"
        file_path = os.path.join(thumbnail_folder, file_name)
        cv2.imwrite(file_path, std_normalized)
        file_urls.append(PathCtrl.formatTmpFileSrc(file_name))
    return file_urls

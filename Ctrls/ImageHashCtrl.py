import itertools
from pathlib import Path
from PIL import Image
import imagehash


def list_images(root_dir):
    return [p for p in Path(root_dir).rglob('*') if p.is_file()]


def load_hash(path, hash_func):
    with Image.open(path) as img:
        return hash_func(img)

def phash(path):
    return load_hash(path, imagehash.phash)

def build_hash_table(image_paths, hash_algo='phash'):
    hash_func = getattr(imagehash, hash_algo)
    hash_table = []
    for path in image_paths:
        try:
            hash_value = load_hash(path, hash_func)
            hash_table.append((path, hash_value))
        except Exception as exc:
            print(f'skip {path}: {exc}')
    return hash_table


def pairwise_compare(hash_table, threshold=5):
    results = []
    for (path_a, hash_a), (path_b, hash_b) in itertools.combinations(hash_table, 2):
        distance = hash_a - hash_b  # 汉明距离
        if distance <= threshold:
            results.append((str(path_a), str(path_b), distance))
    return results


def run_pipeline(root_dir, hash_algo='phash', threshold=5):
    images = list_images(root_dir)
    hash_table = build_hash_table(images, hash_algo)
    return pairwise_compare(hash_table, threshold)


def same_hash_images():
    folder_path = "D:\\OnlyFans\\_icon"
    img_list = [p for p in Path(folder_path).rglob('*') if p.is_file()]
    hash_dict = {}
    for img in img_list:
        hash_value = load_hash(img, imagehash.phash)
        if hash_value in hash_dict:
            hash_dict[hash_value].append(img)
        else:
            hash_dict[hash_value] = [img]
    for hash_value, img_list in hash_dict.items():
        if len(img_list) > 1:
            names = " ".join([Path(img).name for img in img_list])
            print(f"{hash_value}: {names}")

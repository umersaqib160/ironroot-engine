"""
IronRoot Store — Image Downloader
Run this once to pull all product images into this folder.
Usage: python download_images.py
"""

import urllib.request
import os

IMAGES = {
    "01_pan_hero_white_bg.png":   "https://www.ironrootstore.com/cdn/shop/files/Remove_background_project.png?v=1756806420&width=1000",
    "02_pan_lifestyle_cooking.jpg": "https://www.ironrootstore.com/cdn/shop/files/Hfe0454c762464004b1feb619704621bbs.jpg?v=1756806420&width=800",
    "03_pan_on_stove.jpg":         "https://www.ironrootstore.com/cdn/shop/files/H93edf466c4d24323ac0385038e6d6ab8v.jpg?v=1756806420&width=1000",
    "04_pan_with_food.jpg":        "https://www.ironrootstore.com/cdn/shop/files/H139cfe9712a64fd194516f7f9598fdb07_69a35f76-2fa2-4275-8093-dc073beb681c.jpg?v=1756806420&width=800",
    "05_pan_product_shot.jpg":     "https://www.ironrootstore.com/cdn/shop/files/71dgVr6136L._AC_SL1500.jpg?v=1756806420&width=1500",
    "06_pan_side_angle.jpg":       "https://www.ironrootstore.com/cdn/shop/files/H202af9c50d84448ba3044b07278410624.jpg?v=1756806420&width=750",
    "07_pan_top_down.jpg":         "https://www.ironrootstore.com/cdn/shop/files/H59a2a61b117f46c48188800404b64d59c.jpg?v=1756806420&width=750",
    "08_lifestyle_cooking_scene.jpg": "https://www.ironrootstore.com/cdn/shop/files/51qZ9jyYmcL._AC.jpg?v=1755010794&width=800",
    "09_sizzle_steak.jpg":         "https://www.ironrootstore.com/cdn/shop/files/710CkJnnVHL._AC_SL1500.jpg?v=1756898346&width=1500",
    "10_pan_with_herbs.webp":      "https://www.ironrootstore.com/cdn/shop/files/Setde2sartenesdeaceroinoxidableAllroundKuhnRikon_3.webp?v=1756898428&width=1200",
    "11_pan_finished_dish.jpg":    "https://www.ironrootstore.com/cdn/shop/files/Allroundstainlessfryngpan_1.jpg?v=1756898485&width=467",
    "12_features_hero.jpg":        "https://www.ironrootstore.com/cdn/shop/files/71FELflz7yL._AC_SL1000_627577aa-06a1-43f4-9cdc-5eee6c7e521d.jpg?v=1755016450&width=1000",
    "13_pan_quality_shot.jpg":     "https://www.ironrootstore.com/cdn/shop/files/91ql3nHTu9S._AC_SL1500_1a6c5540-044b-4ec5-9224-29a8dd8c5e68.jpg?v=1755016293",
    "14_pan_hero_large.jpg":       "https://www.ironrootstore.com/cdn/shop/files/71Gr-_Gs6PL._AC_SL1500_52c322ae-0b4d-4a24-891f-e702183e53fc.jpg?v=1755016193&width=1500",
    "15_pan_sustainable.jpg":      "https://www.ironrootstore.com/cdn/shop/files/81isYDQSJqL_49d837e6-7321-466f-ac26-9388aa62bb5f.jpg?v=1755016264&width=1601",
}

headers = {"User-Agent": "Mozilla/5.0"}
script_dir = os.path.dirname(os.path.abspath(__file__))

for filename, url in IMAGES.items():
    dest = os.path.join(script_dir, filename)
    if os.path.exists(dest):
        print(f"  skip  {filename} (already exists)")
        continue
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
            f.write(r.read())
        print(f"  ✓     {filename}")
    except Exception as e:
        print(f"  ✗     {filename} — {e}")

print("\nDone. Images saved to:", script_dir)

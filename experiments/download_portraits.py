"""Download and resize new portraits from Wikimedia Commons."""
import os
import sys
import time
from urllib.parse import unquote
import urllib.request
from io import BytesIO
from PIL import Image

USER_AGENT = "USSSR-Faces-Bot/1.0 (https://github.com/VisageDvachevsky/USSSR; konard@example.org) Python/urllib"

PORTRAITS = [
    (13, "sakharov",     "https://upload.wikimedia.org/wikipedia/commons/8/84/RIAN_archive_25981_Academician_Sakharov.jpg"),
    (14, "kurchatov",    "https://upload.wikimedia.org/wikipedia/commons/3/3d/Igor_Kurchatov_1929.jpg"),
    (15, "shostakovich", "https://upload.wikimedia.org/wikipedia/commons/a/ab/Dmitri_Shostakovich_credit_Deutsche_Fotothek_adjusted.jpg"),
    (16, "eisenstein",   "https://upload.wikimedia.org/wikipedia/commons/9/92/Sergei_Eisenstein_portrait_1928.tif"),
    (17, "sholokhov",    "https://upload.wikimedia.org/wikipedia/commons/c/c7/Mikhail_Sholokhov_1960.jpg"),
    (18, "vysotsky",     "https://upload.wikimedia.org/wikipedia/commons/3/3d/%D0%92%D0%BB%D0%B0%D0%B4%D0%B8%D0%BC%D0%B8%D1%80_%D0%92%D1%8B%D1%81%D0%BE%D1%86%D0%BA%D0%B8%D0%B9_-_%D0%BF%D0%BE%D1%80%D1%82%D1%80%D0%B5%D1%82.jpg"),
    (19, "yashin",       "https://upload.wikimedia.org/wikipedia/commons/9/98/Lev_Yashin_1960.jpg"),
    (20, "plisetskaya",  "https://upload.wikimedia.org/wikipedia/commons/4/46/Maya_Plisetskaya_1950s_01.jpg"),
    (21, "kalashnikov",  "https://upload.wikimedia.org/wikipedia/commons/d/d4/Mikhail_Kalashnikov_-_A.jpg"),
    (22, "solzhenitsyn", "https://upload.wikimedia.org/wikipedia/commons/8/8d/Aleksandr_Solzhenitsyn_1974crop.jpg"),
    (23, "leonov",       "https://upload.wikimedia.org/wikipedia/commons/f/f8/Alexei_Leonov.jpg"),
    (24, "rokossovsky",  "https://upload.wikimedia.org/wikipedia/commons/8/8e/Marshal_of_Poland_Konstanty_Rokossowski_portrait.jpg"),
    (25, "tupolev",      "https://upload.wikimedia.org/wikipedia/commons/7/7a/%D0%90.%D0%9D._%D0%A2%D1%83%D0%BF%D0%BE%D0%BB%D0%B5%D0%B2_1944.jpg"),
    (26, "kapitsa",      "https://upload.wikimedia.org/wikipedia/commons/4/44/Pyotr_Kapitsa_1930s.jpg"),
    (27, "landau",       "https://upload.wikimedia.org/wikipedia/commons/0/0b/Landau.jpg"),
    (28, "ulanova",      "https://upload.wikimedia.org/wikipedia/commons/5/5c/Galina_Ulanova_1968.jpg"),
    (29, "okudzhava",    "https://upload.wikimedia.org/wikipedia/commons/3/3f/Bundesarchiv_Bild_183-R1202-0019%2C_Berlin%2C_Palast_der_Republik%2C_Bulat_Okudshawa_cropped.jpg"),
    (30, "kalinin",      "https://upload.wikimedia.org/wikipedia/commons/b/bb/%D0%9C%D0%B8%D1%85%D0%B0%D0%B8%D0%BB_%D0%9A%D0%B0%D0%BB%D0%B8%D0%BD%D0%B8%D0%BD_%281940%29.jpg"),
    (31, "molotov",      "https://upload.wikimedia.org/wikipedia/commons/3/3f/V.M._Molotov_TASS_Portrait_Trim_Edit_Crop_%28cropped%29.jpg"),
    (32, "budyonny",     "https://upload.wikimedia.org/wikipedia/commons/5/51/%D0%9C%D0%B0%D1%80%D1%88%D0%B0%D0%BB_%D0%A1%D0%BE%D0%B2%D0%B5%D1%82%D1%81%D0%BA%D0%BE%D0%B3%D0%BE_%D0%A1%D0%BE%D1%8E%D0%B7%D0%B0_%D0%A1%D0%B5%D0%BC%D1%91%D0%BD_%D0%9C%D0%B8%D1%85%D0%B0%D0%B9%D0%BB%D0%BE%D0%B2%D0%B8%D1%87_%D0%91%D1%83%D0%B4%D1%91%D0%BD%D0%BD%D1%8B%D0%B9.jpg"),
    (33, "chkalov",      "https://upload.wikimedia.org/wikipedia/commons/9/9a/%D0%92%D0%B0%D0%BB%D0%B5%D1%80%D0%B8%D0%B9_%D0%9F%D0%B0%D0%B2%D0%BB%D0%BE%D0%B2%D0%B8%D1%87_%D0%A7%D0%BA%D0%B0%D0%BB%D0%BE%D0%B2.jpg"),
    (34, "papanin",      "https://upload.wikimedia.org/wikipedia/commons/a/a0/%D0%9F%D0%B0%D0%BF%D0%B0%D0%BD%D0%B8%D0%BD_%D0%98%D0%B2%D0%B0%D0%BD_%D0%94%D0%BC%D0%B8%D1%82%D1%80%D0%B8%D0%B5%D0%B2%D0%B8%D1%87_1.jpg"),
    (35, "lysenko",      "https://upload.wikimedia.org/wikipedia/commons/e/ee/Trofim_Lysenko_portrait.jpg"),
    (36, "akhmatova",    "https://upload.wikimedia.org/wikipedia/commons/3/37/%D0%90%D0%BD%D0%BD%D0%B0_%D0%90%D1%85%D0%BC%D0%B0%D1%82%D0%BE%D0%B2%D0%B0.png"),
]

TARGET_DIR = os.path.abspath("frontend/static/portraits")
TARGET_WIDTH = 600

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()

def main() -> int:
    os.makedirs(TARGET_DIR, exist_ok=True)
    # CLI filter: pass numeric IDs to download only a subset (e.g. "25 26 27").
    wanted_ids = {int(arg) for arg in sys.argv[1:] if arg.isdigit()}
    failures = []
    for num, slug, url in PORTRAITS:
        if wanted_ids and num not in wanted_ids:
            continue
        dest = os.path.join(TARGET_DIR, f"{num:02d}_{slug}.jpg")
        print(f"-> {num:02d} {slug}: {url}")
        try:
            data = fetch(url)
        except Exception as exc:
            failures.append((num, slug, f"fetch failed: {exc}"))
            print(f"   ! fetch failed: {exc}")
            time.sleep(2.0)
            continue
        try:
            img = Image.open(BytesIO(data))
            img.load()
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            if img.width > TARGET_WIDTH:
                ratio = TARGET_WIDTH / float(img.width)
                new_h = int(img.height * ratio)
                img = img.resize((TARGET_WIDTH, new_h), Image.LANCZOS)
            img.save(dest, "JPEG", quality=85, optimize=True, progressive=True)
            size_kb = os.path.getsize(dest) / 1024
            print(f"   ok -> {dest} ({img.width}x{img.height}, {size_kb:.1f} KB)")
        except Exception as exc:
            failures.append((num, slug, f"process failed: {exc}"))
            print(f"   ! process failed: {exc}")
        time.sleep(2.0)
    if failures:
        print("\nFAILURES:")
        for num, slug, msg in failures:
            print(f"  {num:02d} {slug}: {msg}")
        return 1
    print("\nAll portraits downloaded successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

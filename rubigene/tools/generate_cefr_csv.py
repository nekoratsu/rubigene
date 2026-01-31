import sys
import os
import csv

TSV_URL = "https://raw.githubusercontent.com/cefr-j/vocabulary-profile/master/cefrj-vocabulary-profile.tsv"
OUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "cefr.csv"))

# requests install (if needed)
def ensure_requests():
    try:
        import requests
    except ImportError:
        import subprocess
        print("requests not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    return requests

def download_tsv(url):
    try:
        import requests
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"Download error: {e}", file=sys.stderr)
        return None

def parse_and_save_tsv(tsv_text, out_path):
    try:
        reader = csv.DictReader(tsv_text.splitlines(), delimiter='\t')
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "CEFR_level", "pos"])
            for row in reader:
                word = row.get("word", "").strip().lower()
                level = row.get("CEFR_level", "").strip().upper()
                pos = row.get("pos", "").strip()
                if not word or not level or not pos:
                    continue
                writer.writerow([word, level, pos])
        print(f"Saved: {out_path}")
        return True
    except Exception as e:
        print(f"TSV parse/save error: {e}", file=sys.stderr)
        return False

def main():
    ensure_requests()
    import requests  # after install
    print("Downloading CEFR-J Vocabulary Profile TSV...")
    tsv_text = download_tsv(TSV_URL)
    if not tsv_text:
        print("Failed to download TSV.", file=sys.stderr)
        return 1
    print("Parsing and saving as rubigene/data/cefr.csv ...")
    ok = parse_and_save_tsv(tsv_text, OUT_PATH)
    if not ok:
        print("Failed to parse or save TSV.", file=sys.stderr)
        return 2
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

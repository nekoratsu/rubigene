import sys
import subprocess
import json
import os

# 1. wordfreq install (if needed)
def ensure_wordfreq():
    try:
        import wordfreq
    except ImportError:
        print("wordfreq not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "wordfreq"])
        import wordfreq
    return wordfreq

def main():
    wordfreq = ensure_wordfreq()
    from wordfreq import top_n_list, zipf_frequency

    print("Generating English top 50,000 word frequencies...")
    words = top_n_list("en", 50000)
    freq_dict = {}
    errors = 0
    for word in words:
        try:
            freq = zipf_frequency(word, "en")
            freq_dict[word] = freq
        except Exception as e:
            errors += 1
            print(f"Error for word '{word}': {e}", file=sys.stderr)
            continue

    print(f"Total words: {len(freq_dict)} (errors: {errors})")

    # 5. Save as rubigene/data/frequency.json
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "frequency.json")
    out_path = os.path.abspath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(freq_dict, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()

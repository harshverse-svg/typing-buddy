"""build_wordlist.py - Build frequency word list in word<TAB>number format.

Sources:
1. Frequency source: Hermit Dave's FrequencyWords (OpenSubtitles corpus, MIT License).
2. Dictionary validation: Infochimps / SCOWL / dwyl english-words (Public Domain / MIT License),
   ensuring only genuine English words are included and user typos (e.g. 'recieve') are excluded.

Filters:
- Length: 2 to 25 characters
- Lowercase alphabetic characters, hyphens, and apostrophes: ^[a-z]+(?:['\\-][a-z]+)*$
- Excludes common English misspellings (where the target correct word is distinct).
- Valid English words verified against standard English dictionary.
- Scales raw frequencies to 1..250 on a logarithmic scale.
"""
import argparse
import math
import re
import urllib.request

WORD_PATTERN = re.compile(r"^[a-z]+(?:['\-][a-z]+)*$")
DEFAULT_FREQ_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/en/en_full.txt"
DEFAULT_DICT_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"

# Common spelling errors to exclude from the dictionary so they can be corrected
COMMON_MISSPELLINGS = {
    "accomodate", "acheive", "arguement", "begining", "beleive", "calender",
    "concious", "definately", "embarass", "enviroment", "foriegn", "goverment",
    "guarentee", "maintainance", "millenium", "neccesary", "neccessary", "noticable",
    "occured", "priviledge", "recieve", "recieved", "rythm", "seperate",
    "suprise", "thier", "tommorow", "truely", "untill", "wich", "wierd", "writting"
}


def load_valid_dictionary(dict_source):
    """Load set of verified valid English words."""
    print(f"Loading dictionary validation words from: {dict_source}")
    valid = set()
    if dict_source.startswith("http://") or dict_source.startswith("https://"):
        req = urllib.request.Request(dict_source, headers={"User-Agent": "TypingPredictorBuilder/1.0"})
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                w = line.decode("utf-8", errors="ignore").strip().lower()
                if w and w not in COMMON_MISSPELLINGS:
                    valid.add(w)
    else:
        with open(dict_source, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                w = line.strip().lower()
                if w and w not in COMMON_MISSPELLINGS:
                    valid.add(w)
    print(f"Loaded {len(valid)} dictionary words for validation.")
    return valid


def parse_and_filter(stream, valid_words=None, min_len=2, max_len=25, limit=150000):
    """Parse lines of (word, count) and filter words."""
    word_counts = {}
    count_items = 0
    for line in stream:
        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="ignore")
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        word = parts[0].lower().strip()
        try:
            count = int(parts[1])
        except ValueError:
            continue

        if not (min_len <= len(word) <= max_len):
            continue
        if word in COMMON_MISSPELLINGS:
            continue
        if not WORD_PATTERN.fullmatch(word):
            continue

        # If dictionary is provided, ensure word or hyphen/apostrophe-stripped word is in dictionary
        if valid_words is not None:
            clean_w = word.replace("'", "").replace("-", "")
            if word not in valid_words and clean_w not in valid_words:
                continue

        if word not in word_counts:
            word_counts[word] = count
            count_items += 1
            if limit and count_items >= limit:
                break
    return word_counts


def scale_frequencies(word_counts, min_scale=1, max_scale=250):
    """Scale raw frequency counts to min_scale..max_scale logarithmically."""
    if not word_counts:
        return {}
    min_count = min(word_counts.values())
    max_count = max(word_counts.values())

    log_min = math.log(max(1, min_count))
    log_max = math.log(max(1, max_count))
    span = log_max - log_min if log_max > log_min else 1.0

    scaled = {}
    for word, count in word_counts.items():
        log_val = math.log(max(1, count))
        score = min_scale + int(round((max_scale - min_scale) * (log_val - log_min) / span))
        score = max(min_scale, min(max_scale, score))
        scaled[word] = score
    return scaled


def build_wordlist(freq_source, dict_source, output_path, limit=150000):
    """Build wordlist file from frequency and dictionary sources."""
    valid_words = load_valid_dictionary(dict_source) if dict_source else None

    print(f"Reading frequency data from: {freq_source}")
    if freq_source.startswith("http://") or freq_source.startswith("https://"):
        req = urllib.request.Request(freq_source, headers={"User-Agent": "TypingPredictorBuilder/1.0"})
        with urllib.request.urlopen(req) as resp:
            counts = parse_and_filter(resp, valid_words=valid_words, limit=limit)
    else:
        with open(freq_source, "r", encoding="utf-8", errors="ignore") as f:
            counts = parse_and_filter(f, valid_words=valid_words, limit=limit)

    print(f"Filtered {len(counts)} genuine English words.")
    scaled = scale_frequencies(counts)

    sorted_words = sorted(scaled.items(), key=lambda item: (-item[1], item[0]))

    print(f"Writing {len(sorted_words)} words to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("# words_main.txt - Frequency word list built from FrequencyWords & SCOWL dictionary\n")
        out.write("# Format: word<TAB>frequency (1-250)\n")
        for word, freq in sorted_words:
            out.write(f"{word}\t{freq}\n")
    print("Done!")


def main():
    parser = argparse.ArgumentParser(description="Build words_main.txt from a frequency list.")
    parser.add_argument("--freq-source", default=DEFAULT_FREQ_URL, help="URL or path to word frequency list")
    parser.add_argument("--dict-source", default=DEFAULT_DICT_URL, help="URL or path to valid dictionary list")
    parser.add_argument("--out", default="words_main.txt", help="Output path (default: words_main.txt)")
    parser.add_argument("--limit", type=int, default=150000, help="Maximum number of words (default: 150000)")
    args = parser.parse_args()

    build_wordlist(args.freq_source, args.dict_source, args.out, limit=args.limit)


if __name__ == "__main__":
    main()

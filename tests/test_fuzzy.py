"""test_fuzzy.py - Benchmark and unit tests for fuzzy spelling correction."""
import os
import time

import pytest

from typing_buddy.fuzzy import FuzzyEngine

BENCHMARK_PAIRS = [
    ("recieve", "receive"),
    ("definately", "definitely"),
    ("occured", "occurred"),
    ("seperate", "separate"),
    ("accomodate", "accommodate"),
    ("neccessary", "necessary"),
    ("wich", "which"),
    ("thier", "their"),
    ("beleive", "believe"),
    ("untill", "until"),
    ("tommorow", "tomorrow"),
    ("begining", "beginning"),
    ("goverment", "government"),
    ("enviroment", "environment"),
    ("embarass", "embarrass"),
    ("maintainance", "maintenance"),
    ("millenium", "millennium"),
    ("rythm", "rhythm"),
    ("calender", "calendar"),
    ("concious", "conscious"),
    ("priviledge", "privilege"),
    ("truely", "truly"),
    ("noticable", "noticeable"),
    ("foriegn", "foreign"),
    ("acheive", "achieve"),
    ("suprise", "surprise"),
    ("wierd", "weird"),
    ("writting", "writing"),
    ("arguement", "argument"),
    ("guarentee", "guarantee"),
]


@pytest.fixture(scope="module")
def fuzzy_engine():
    """Load wordpack and initialize FuzzyEngine."""
    words = {}
    base_dir = os.path.dirname(__file__)
    candidates = [
        os.path.join(base_dir, "..", "wordpacks", "en-large", "words.txt"),
        os.path.join(base_dir, "..", "wordpacks", "en-basic", "words.txt"),
        os.path.join(base_dir, "..", "words_main.txt"),
    ]
    for wordlist_path in candidates:
        if os.path.exists(wordlist_path):
            with open(wordlist_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#"):
                        continue
                    parts = line.split()
                    if parts:
                        word = parts[0].lower()
                        freq = int(parts[1]) if len(parts) > 1 else 1
                        if word not in words or freq > words[word]:
                            words[word] = freq
            if len(words) >= 5000:
                break
    engine = FuzzyEngine()
    engine.build_index_async(words)
    # Wait for background index
    deadline = time.time() + 10
    while not engine.is_ready and time.time() < deadline:
        time.sleep(0.05)
    assert engine.is_ready, "FuzzyEngine index failed to build within deadline"
    return engine


def test_misspelling_benchmark_accuracy(fuzzy_engine):
    """Verify >= 90% accuracy in top 3 for benchmark words."""
    top3_count = 0
    top1_count = 0
    total = len(BENCHMARK_PAIRS)

    # Warm up call to ensure JIT/frame initialization
    fuzzy_engine.correct_word("warmup")

    for typo, target in BENCHMARK_PAIRS:
        t0 = time.perf_counter()
        results = fuzzy_engine.correct_word(typo, n=3)
        dt_ms = (time.perf_counter() - t0) * 1000

        # Query time must be under 20 ms even on busy systems
        assert dt_ms < 20.0, f"Query for '{typo}' took {dt_ms:.2f}ms (> 20ms)"

        if results and results[0] == target:
            top1_count += 1
        if target in results[:3]:
            top3_count += 1

    accuracy = (top3_count / total) * 100
    print(f"\nBenchmark Results: Top-3 Accuracy: {top3_count}/{total} ({accuracy:.1f}%), Top-1: {top1_count}/{total}")
    assert accuracy >= 90.0, f"Benchmark accuracy {accuracy:.1f}% below 90% threshold"


def test_correctly_spelled_words_never_corrected(fuzzy_engine):
    """Correctly spelled words must return empty list."""
    correct_words = ["receive", "definitely", "occurred", "separate", "necessary",
                     "which", "their", "believe", "until", "tomorrow", "government",
                     "environment", "embarrass", "calendar", "conscious", "hello", "world"]
    for word in correct_words:
        assert fuzzy_engine.correct_word(word) == [], f"Correctly spelled '{word}' was corrected!"


def test_no_correction_rules(fuzzy_engine):
    """Test words with digits, ALL CAPS, learned words, ignore list, and short words."""
    # Digits
    assert fuzzy_engine.correct_word("word123") == []
    assert fuzzy_engine.correct_word("h3llo") == []

    # ALL CAPS
    assert fuzzy_engine.correct_word("RECIEVE") == []
    assert fuzzy_engine.correct_word("DEFINATELY") == []

    # Very short words (< 4 letters)
    assert fuzzy_engine.correct_word("teh") == []
    assert fuzzy_engine.correct_word("cat") == []

    # Learned words
    learned = {"mycustomword"}
    assert fuzzy_engine.correct_word("mycustomword", learned_words=learned) == []

    # Ignore list
    fuzzy_engine.add_to_ignore("ignoredtypo")
    assert fuzzy_engine.correct_word("ignoredtypo") == []


def test_prefix_fuzzy_matching(fuzzy_engine):
    """In-word prefix fuzzy suggestions for 'recie' and 'neccesa'."""
    res_recie = fuzzy_engine.fuzzy_prefix("recie", n=5)
    assert any("receive" in s.lower() for s in res_recie), f"Expected 'receive' in {res_recie}"
    assert all(s.startswith("~") for s in res_recie)

    res_neccesa = fuzzy_engine.fuzzy_prefix("neccesa", n=5)
    assert any("necessary" in s.lower() for s in res_neccesa), f"Expected 'necessary' in {res_neccesa}"
    assert all(s.startswith("~") for s in res_neccesa)


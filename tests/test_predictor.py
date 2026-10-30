"""test_predictor.py - Unit tests for Predictor ranking, learning, and caching."""
import os
import tempfile

from typing_buddy.predictor import Predictor, load_wordlist


def test_load_wordlist_plain():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("# comment\napple\t100\nbanana\t200\ncherry\n")
        path = f.name
    try:
        freq, _ = load_wordlist(path)
        assert freq["apple"] == 100
        assert freq["banana"] == 200
        assert freq["cherry"] == 1
    finally:
        os.remove(path)


def test_multiple_lists_higher_wins():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f1, \
         tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f2:
        f1.write("testword\t50\n")
        f2.write("testword\t150\n")
        p1, p2 = f1.name, f2.name
    try:
        pred = Predictor([p1, p2], user_path=p1 + ".user")
        assert pred.freq["testword"] == 150
    finally:
        for p in (p1, p2, p1 + ".user"):
            if os.path.exists(p):
                os.remove(p)


def test_new_word_min_count_rule():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("hello\t200\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    try:
        pred = Predictor([wordfile], user_path=userfile)
        pred.NEW_WORD_MIN_COUNT = 3

        # Type 'unknown' 1 time
        pred.learn("unknown")
        assert "unknown" not in pred.freq
        assert pred.pending.get("unknown") == 1

        # Type 2nd time
        pred.learn("unknown")
        assert "unknown" not in pred.freq
        assert pred.pending.get("unknown") == 2

        # Type 3rd time -> should be added to freq and appended to file
        pred.learn("unknown")
        assert "unknown" in pred.freq
        assert "unknown" not in pred.pending

        # Verify appended to file
        with open(wordfile, "r", encoding="utf-8") as wf:
            content = wf.read()
        assert "unknown\t120" in content
    finally:
        for p in (wordfile, userfile):
            if os.path.exists(p):
                os.remove(p)


def test_append_file_without_trailing_newline():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("firstword\t100")  # no newline!
        wordfile = f.name
    userfile = wordfile + ".user"
    try:
        pred = Predictor([wordfile], user_path=userfile)
        pred.NEW_WORD_MIN_COUNT = 1
        pred.learn("secondword")

        with open(wordfile, "r", encoding="utf-8") as wf:
            lines = wf.readlines()
        assert len(lines) == 2
        assert lines[0].strip() == "firstword\t100"
        assert lines[1].strip() == "secondword\t120"
    finally:
        for p in (wordfile, userfile):
            if os.path.exists(p):
                os.remove(p)


def test_cache_invalidation_on_new_word():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("plan\t100\nplanet\t150\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    try:
        pred = Predictor([wordfile], user_path=userfile)
        pred.NEW_WORD_MIN_COUNT = 1
        pred.prewarm()

        # Query suggestions for 'pla'
        s1 = pred.suggest("pla")
        assert "plan" in s1 or "planet" in s1

        # Learn 'platinum'
        pred.learn("platinum")
        s2 = pred.suggest("pla")
        assert "platinum" in s2
    finally:
        for p in (wordfile, userfile):
            if os.path.exists(p):
                os.remove(p)


def test_remove_word():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("removethis\t120\nkeepthis\t150\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    ignorefile = wordfile + ".ignore"
    try:
        pred = Predictor([wordfile], user_path=userfile, ignore_path=ignorefile)
        pred.prewarm()
        assert "removethis" in pred.freq

        pred.remove_word("removethis")
        assert "removethis" not in pred.freq
        assert "removethis" not in pred.keys
        assert "removethis" in pred.ignore_words

        # Check suggestions
        sugg = pred.suggest("remove")
        assert "removethis" not in sugg
    finally:
        for p in (wordfile, userfile, ignorefile):
            if os.path.exists(p):
                os.remove(p)


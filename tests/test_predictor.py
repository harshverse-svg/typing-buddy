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


def test_new_word_min_count_rule_auto_mode():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("hello\t200\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    addedfile = wordfile + ".added"
    try:
        pred = Predictor([wordfile], user_path=userfile, added_path=addedfile, new_word_mode="auto")
        pred.NEW_WORD_MIN_COUNT = 3

        # Type 'unknown' 1 time
        pred.learn("unknown")
        assert "unknown" not in pred.freq
        assert pred.pending.get("unknown") == 1

        # Type 2nd time
        pred.learn("unknown")
        assert "unknown" not in pred.freq
        assert pred.pending.get("unknown") == 2

        # Type 3rd time -> should be added to freq and appended to file in auto mode
        pred.learn("unknown")
        assert "unknown" in pred.freq
        assert "unknown" not in pred.pending

        # Verify appended to file
        with open(wordfile, "r", encoding="utf-8") as wf:
            content = wf.read()
        assert "unknown\t120" in content
    finally:
        for p in (wordfile, userfile, addedfile):
            if os.path.exists(p):
                os.remove(p)


def test_new_word_mode_review_default():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("knownword\t200\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    addedfile = wordfile + ".added"
    try:
        pred = Predictor([wordfile], user_path=userfile, added_path=addedfile, new_word_mode="review")
        pred.NEW_WORD_MIN_COUNT = 2

        pred.learn("reviewword")
        assert "reviewword" not in pred.freq
        assert not os.path.exists(addedfile)

        # 2nd time -> should be placed in review queue (addedfile), NOT in wordfile or pred.freq
        pred.learn("reviewword")
        assert "reviewword" not in pred.freq
        assert os.path.exists(addedfile)
        with open(wordfile, "r", encoding="utf-8") as wf:
            assert "reviewword" not in wf.read()

        # Approve word via keep_word
        pred.keep_word("reviewword")
        assert "reviewword" in pred.freq
        with open(wordfile, "r", encoding="utf-8") as wf:
            assert "reviewword\t120" in wf.read()
    finally:
        for p in (wordfile, userfile, addedfile):
            if os.path.exists(p):
                os.remove(p)


def test_new_word_mode_off():
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("knownword\t200\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    addedfile = wordfile + ".added"
    try:
        pred = Predictor([wordfile], user_path=userfile, added_path=addedfile, new_word_mode="off")
        pred.NEW_WORD_MIN_COUNT = 1
        for _ in range(5):
            pred.learn("secretword")
        assert "secretword" not in pred.freq
        assert "secretword" not in pred.pending
        assert not os.path.exists(addedfile)
    finally:
        for p in (wordfile, userfile, addedfile):
            if os.path.exists(p):
                os.remove(p)


def test_pending_counters_not_written_to_disk():
    import json
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("knownword\t200\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    try:
        pred = Predictor([wordfile], user_path=userfile, new_word_mode="review")
        pred.learn("transientsecret")
        assert pred.pending.get("transientsecret") == 1

        pred.save()
        assert os.path.exists(userfile)
        with open(userfile, "r", encoding="utf-8") as uf:
            data = json.load(uf)
        assert "pending" not in data, "pending counters must NEVER be written to user_data.json"
    finally:
        for p in (wordfile, userfile):
            if os.path.exists(p):
                os.remove(p)


def test_word_pairs_only_known_words():
    import json
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("alpha\t200\nbeta\t180\n")
        wordfile = f.name
    userfile = wordfile + ".user"
    try:
        pred = Predictor([wordfile], user_path=userfile)

        # Pair 1: Both known words -> should be stored in bi
        pred.learn("beta", prev="alpha")
        assert pred.bi.get("alpha", {}).get("beta") == 1

        # Pair 2: Unknown prev, known word -> must NOT be stored
        pred.learn("alpha", prev="unknownprev")
        assert "unknownprev" not in pred.bi

        # Pair 3: Known prev, unknown word -> must NOT be stored
        pred.learn("unknownnext", prev="alpha")
        assert "unknownnext" not in pred.bi.get("alpha", {})

        # Pair 4: Both unknown words -> must NOT be stored
        pred.learn("secretwordtwo", prev="secretwordone")
        assert "secretwordone" not in pred.bi

        pred.save()
        with open(userfile, "r", encoding="utf-8") as uf:
            data = json.load(uf)
        assert "alpha" in data["bi"]
        assert "unknownprev" not in data["bi"]
        assert "secretwordone" not in data["bi"]
        assert data["bi"]["alpha"] == {"beta": 1}
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
        pred = Predictor([wordfile], user_path=userfile, new_word_mode="auto")
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
        pred = Predictor([wordfile], user_path=userfile, new_word_mode="auto")
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


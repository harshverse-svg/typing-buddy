"""test_privacy_files.py - Verify every file written by the app is documented in PRIVACY.md."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from typing_buddy.data_dir import init_user_data_files
from typing_buddy.predictor import Predictor
from typing_buddy.settings import Settings
from typing_buddy.snippets import SnippetsManager
from typing_buddy.stats import StatsTracker


def test_all_created_files_documented_in_privacy_policy(tmp_path):
    data_dir = tmp_path / "typing_buddy_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize data directory structures
    init_user_data_files(data_dir, interactive_migrate=False)

    # 2. Run Settings
    settings_file = data_dir / "settings.json"
    settings = Settings(str(settings_file))
    settings.set_value("popup_font_size", 14)

    # 3. Run Snippets
    snippets_file = data_dir / "snippets.json"
    snippets = SnippetsManager(str(snippets_file))
    snippets.load()

    # 4. Run StatsTracker
    stats_file = data_dir / "stats.json"
    stats = StatsTracker(str(stats_file))
    stats.record_pick(2, 4, is_correction=False)
    stats.save()

    # 5. Run Predictor with personal word file, user data, added words, ignore words
    personal_words = data_dir / "personal_words.txt"
    personal_words.write_text("initial\t100\n", encoding="utf-8")
    user_file = data_dir / "user_data.json"
    added_file = data_dir / "added_words.json"
    ignore_file = data_dir / "ignore_words.txt"

    pred = Predictor(
        [str(personal_words)],
        learn_file=str(personal_words),
        user_path=str(user_file),
        added_path=str(added_file),
        ignore_path=str(ignore_file),
        new_word_mode="review",
    )
    pred.NEW_WORD_MIN_COUNT = 1
    # Queue a word in review
    pred.learn("newqueuedword")
    # Add a word
    pred.keep_word("approvedword")
    # Remove a word to create ignore list
    pred.remove_word("approvedword")
    pred.save()

    # 6. Setup and write to logger
    log_file = data_dir / "predictor.log"
    logger = logging.getLogger("test_privacy_logger")
    handler = RotatingFileHandler(str(log_file), maxBytes=10000, backupCount=1, encoding="utf-8")
    logger.addHandler(handler)
    logger.info("Test diagnostic log entry")
    handler.close()

    # 7. Collect all created files
    created_files = set()
    for p in data_dir.iterdir():
        if p.is_file() and not p.name.endswith(".tmp"):
            created_files.add(p.name)

    assert len(created_files) > 0, "No files were created during testing"

    # 8. Check against PRIVACY.md
    privacy_md_path = Path(__file__).resolve().parent.parent / "PRIVACY.md"
    assert privacy_md_path.exists(), "PRIVACY.md must exist in the repository root"
    privacy_text = privacy_md_path.read_text(encoding="utf-8")

    undocumented = []
    for filename in sorted(created_files):
        if filename not in privacy_text:
            undocumented.append(filename)

    assert not undocumented, (
        f"The following files created by the application are NOT documented in PRIVACY.md: {undocumented}"
    )

"""test_grammar.py - Unit tests for grammar checker, near-end filtering, and Harper integration."""
import pytest

from typing_buddy.grammar import (
    HarperChecker,
    Issue,
    NullChecker,
    compute_replacement_action,
    filter_issues_near_end,
)
from typing_buddy.packs import get_non_english_pack_words


def test_null_checker():
    checker = NullChecker()
    assert checker.is_available() is False
    assert checker.check("I has a cat.") == []


def test_filter_issues_near_end():
    text = "Yesterday I has a question"
    # Word positions:
    # "Yesterday" (0..9)
    # "I" (10..11)
    # "has" (12..15)
    # "a" (16..17)
    # "question" (18..26)
    issue1 = Issue(start=12, end=15, kind="Agreement", rule="Agreement", message="did you mean have", replacements=["have"])
    # Issue in first word ("Yesterday")
    issue_far = Issue(start=0, end=9, kind="WordChoice", rule="WordChoice", message="msg", replacements=["Today"])

    # max_words_back = 3 (covers "has", "a", "question")
    kept = filter_issues_near_end([issue_far, issue1], text, max_words_back=3)
    assert issue1 in kept
    assert issue_far not in kept


def test_filter_issues_skips_single_word():
    # Sentences with fewer than 2 words must return empty (avoids partial false alarms)
    issue = Issue(start=0, end=4, kind="WordChoice", rule="rule", message="msg", replacements=["that"])
    assert filter_issues_near_end([issue], "word", max_words_back=3) == []


def test_compute_replacement_action():
    text = "I has a cat"
    issue = Issue(start=2, end=5, kind="Agreement", rule="Agreement", message="", replacements=["have"])
    action = compute_replacement_action(issue, text, max_tail_len=40)
    assert action is not None
    num_bs, retype = action
    # tail is "has a cat" (length 9)
    assert num_bs == 9
    assert retype == "have a cat"


def test_compute_replacement_action_refuses_long_tail():
    text = "I has " + ("a" * 45)
    issue = Issue(start=2, end=5, kind="Agreement", rule="Agreement", message="", replacements=["have"])
    assert compute_replacement_action(issue, text, max_tail_len=40) is None


CORRECT_SENTENCES = [
    "I have a dog.",
    "She has a lovely cat.",
    "This is a good test.",
    "We went to the store today.",
    "Everything looks completely fine.",
    "How are you doing today?",
    "I will see you tomorrow.",
    "Can you please send me that file?",
    "The weather is very nice outside.",
    "Let us meet at five in the evening.",
    "John and Mary went to the market.",
    "Alice said she would come over later.",
    "Bob is working on his new computer.",
    "Thanks for your help with this project.",
    "Sounds good to me, see you soon.",
    "No problem at all, take your time.",
    "Are you ready for the meeting?",
    "I will be there in ten minutes.",
    "That was a very interesting book.",
    "Python is a great programming language.",
    "The project is on track for release.",
    "Please review the attached document.",
    "I think we should proceed with the plan.",
    "The team did an amazing job.",
    "I agree with your suggestion.",
    "Bhai kya haal hai?",
    "Haan sab theek hai yahan.",
    "Kal milte hain office mein.",
    "Aaj ka kaam khatam ho gaya.",
    "Chai peene chalte hain abhi.",
]

KNOWN_ERROR_SENTENCES = [
    ("I has a dog.", "have"),
    ("She have a cat.", "has"),
    ("This is an dog.", "a"),
    ("The the car is fast.", "The"),
    ("He go to school.", "goes"),
    ("I could of done it.", "could have"),
    ("You should of called.", "should have"),
    ("They was very happy.", "were"),
    ("He don't know that.", "doesn't"),
    ("Suppose to be easy.", "Supposed to"),
]


@pytest.fixture(scope="module")
def harper_checker():
    hinglish_words = get_non_english_pack_words(["hinglish"])
    checker = HarperChecker(custom_words=hinglish_words)
    if not checker.is_available():
        pytest.skip("harper-py is not available in this environment")
    return checker


def test_harper_zero_false_positives_on_correct_sentences(harper_checker):
    """Verify 30 correct chat, standard, and Hinglish sentences produce zero suggestions."""
    for sentence in CORRECT_SENTENCES:
        issues = harper_checker.check(sentence)
        assert issues == [], f"Unexpected grammar issue on correct sentence: '{sentence}' -> {issues}"


def test_harper_catches_verified_errors(harper_checker):
    """Verify Harper flags 10 known grammatical errors with expected corrections."""
    caught = 0
    for text, expected in KNOWN_ERROR_SENTENCES:
        issues = harper_checker.check(text)
        all_repls = [r.lower() for i in issues for r in i.replacements]
        assert any(expected.lower() in r for r in all_repls), f"Expected '{expected}' for '{text}', got {issues}"
        caught += 1
    assert caught == len(KNOWN_ERROR_SENTENCES)

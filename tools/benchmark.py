"""benchmark.py - Resource and latency benchmark for Typing Buddy."""
import os
import sys
import time

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing_buddy.fuzzy import FuzzyEngine
from typing_buddy.grammar import HarperChecker
from typing_buddy.packs import get_enabled_pack_wordlists, get_non_english_pack_words
from typing_buddy.predictor import Predictor


def get_process_memory_mb():
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        return proc.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def benchmark_grammar_latency(checker, iterations=100):
    test_sentences = [
        "I has a question about this.",
        "She have two dogs and three cats.",
        "This is an test of the grammar system.",
        "The the quick brown fox jumps over the lazy dog.",
        "We could of gone to the store earlier today.",
        "Suppose to be ready by five o'clock.",
        "He don't know the exact answer to that.",
        "Everything was completely fine until yesterday.",
        "Can you please review the attached document?",
        "Alice and Bob went to the market to buy apples."
    ]
    latencies = []
    for _ in range(iterations // len(test_sentences) + 1):
        for s in test_sentences:
            t0 = time.perf_counter()
            _ = checker.check(s)
            latencies.append((time.perf_counter() - t0) * 1000)
            if len(latencies) >= iterations:
                break
        if len(latencies) >= iterations:
            break

    avg_ms = sum(latencies) / len(latencies)
    sorted_lats = sorted(latencies)
    p95_ms = sorted_lats[int(len(sorted_lats) * 0.95)]
    return avg_ms, p95_ms


def benchmark_cpu_usage(duration_seconds=5):
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        # Warmup
        proc.cpu_percent(interval=None)
        time.sleep(duration_seconds)
        return proc.cpu_percent(interval=None)
    except Exception:
        return 0.0


def main():
    print("=" * 65)
    print("TYPING-BUDDY PERFORMANCE & RESOURCE BENCHMARK")
    print("=" * 65)

    # 1. Startup & Memory with en-basic only (+ grammar)
    t0 = time.perf_counter()
    en_basic_paths = get_enabled_pack_wordlists(["en-basic"])
    pred_basic = Predictor([str(p) for p in en_basic_paths], user_path="bench_u1.json")
    pred_basic.prewarm()
    fuzzy_basic = FuzzyEngine()
    fuzzy_basic.build_index_async(pred_basic.freq)
    while not fuzzy_basic.is_ready:
        time.sleep(0.01)

    hinglish_words = get_non_english_pack_words(["hinglish"])
    grammar = HarperChecker(custom_words=hinglish_words)
    startup_time = (time.perf_counter() - t0) * 1000

    mem_basic_grammar = get_process_memory_mb()
    print(f"[1] Startup Time (en-basic + grammar):  {startup_time:7.2f} ms")
    print(f"[2] Memory (en-basic + grammar):        {mem_basic_grammar:7.2f} MB  (Target: < 120 MB)")

    # 2. Grammar check latency
    avg_gram, p95_gram = benchmark_grammar_latency(grammar, iterations=100)
    print(f"[3] Grammar Check Latency:              {avg_gram:7.4f} ms  (p95: {p95_gram:.4f} ms, Target: < 20 ms)")

    # 3. Memory with en-large (+ grammar)
    en_large_paths = get_enabled_pack_wordlists(["en-large"])
    t0 = time.perf_counter()
    pred_large = Predictor([str(p) for p in en_large_paths], user_path="bench_u2.json")
    pred_large.prewarm()
    fuzzy_large = FuzzyEngine()
    fuzzy_large.build_index_async(pred_large.freq)
    while not fuzzy_large.is_ready:
        time.sleep(0.01)
    large_load_time = (time.perf_counter() - t0) * 1000

    mem_large_grammar = get_process_memory_mb()
    print(f"[4] en-large Load & Index Time:         {large_load_time:7.2f} ms ({len(pred_large.keys):,} words)")
    print(f"[5] Memory (en-large + grammar):        {mem_large_grammar:7.2f} MB  (Target: < 300 MB)")

    # 4. Suggestion and Fuzzy Latency (en-large)
    prefixes = ["th", "wh", "re", "pro", "com", "int", "con", "de", "un", "ex"]
    sugg_lats = []
    for _ in range(100):
        for p in prefixes:
            t0 = time.perf_counter()
            _ = pred_large.suggest(p, n=3)
            sugg_lats.append((time.perf_counter() - t0) * 1000)
    avg_sugg = sum(sugg_lats) / len(sugg_lats)
    p95_sugg = sorted(sugg_lats)[int(len(sugg_lats) * 0.95)]
    print(f"[6] en-large Avg Suggestion Latency:    {avg_sugg:7.4f} ms  (p95: {p95_sugg:.4f} ms)")

    # 5. Idle CPU measurement
    print("[7] Measuring Idle CPU over 5 seconds...")
    idle_cpu = benchmark_cpu_usage(duration_seconds=5)
    print(f"    Idle CPU:                            {idle_cpu:7.2f} %   (Target: < 1.0%)")

    # 6. Simulated Typing CPU (10,000 keystrokes)
    print("[8] Measuring CPU during simulated typing (10,000 chars)...")
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        proc.cpu_percent(interval=None)
        t_start = time.perf_counter()
        sim_text = "The quick brown fox jumps over the lazy dog and asks a few questions about grammar. " * 150
        for ch in sim_text:
            if ch == " ":
                _ = pred_large.suggest("th", n=3)
                _ = grammar.check("The quick brown fox jumps over the lazy dog.")
            else:
                _ = pred_large.suggest("qu", n=3)
        sim_duration = time.perf_counter() - t_start
        sim_cpu = proc.cpu_percent(interval=None)
        print(f"    Simulated Typing CPU:                {sim_cpu:7.2f} %   (Processed in {sim_duration:.2f}s)")
    except Exception as e:
        print(f"    Simulated Typing CPU: error {e}")

    print("=" * 65)

    # Cleanup temp benchmark user files
    for f in ["bench_u1.json", "bench_u2.json"]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass


if __name__ == "__main__":
    main()

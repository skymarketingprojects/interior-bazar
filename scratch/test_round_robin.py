"""
Quick integration test for the DB-backed round-robin phone counter.
Run from the project root:
    python3 scratch/test_round_robin.py

It simulates:
  1. First-ever call  → should return number[0]
  2. Second call      → should return number[1]
  3. Third call       → should return number[0] (wraps around)
  4. Simulates a "long time later" by manually deleting the counter row
     to mimic a fresh state — should still start from number[0] (not break)
  5. Multiple rapid calls → confirms strict alternation
"""
import os
import sys
import django

# ── Bootstrap Django ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interior_bazzar.settings')
django.setup()

# ── Import after setup ────────────────────────────────────────────────────────
from app_ib.models import RoundRobinCounter
from app_ib.views import _get_next_phone, _phone_numbers, _PHONE_COUNTER_KEY

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"

def assert_eq(label, got, expected):
    if got == expected:
        print(f"  {PASS}  {label}: got '{got}'")
    else:
        print(f"  {FAIL}  {label}: expected '{expected}', got '{got}'")

def clean():
    RoundRobinCounter.objects.filter(key=_PHONE_COUNTER_KEY).delete()
    print("  [reset] Counter row deleted (fresh state)")

print("\n" + "="*60)
print("  Round-Robin Phone Counter — DB-backed integration test")
print("="*60)

# ─── Test 1: Basic round-robin sequence ───────────────────────────────────────
print("\n[Test 1] Basic sequence from fresh state")
clean()
r1 = _get_next_phone()
r2 = _get_next_phone()
r3 = _get_next_phone()
r4 = _get_next_phone()
assert_eq("Call 1", r1, _phone_numbers[0])
assert_eq("Call 2", r2, _phone_numbers[1])
assert_eq("Call 3 (wrap)", r3, _phone_numbers[0])
assert_eq("Call 4", r4, _phone_numbers[1])

# ─── Test 2: Simulate "long gap" — counter row deleted (Redis-like reset) ─────
print("\n[Test 2] Simulate cache/row loss (long time later)")
clean()
r_after_gap = _get_next_phone()
assert_eq("After gap, Call 1", r_after_gap, _phone_numbers[0])
r_after_gap2 = _get_next_phone()
assert_eq("After gap, Call 2", r_after_gap2, _phone_numbers[1])

# ─── Test 3: Counter persists — does NOT reset between calls ──────────────────
print("\n[Test 3] Counter persists (no reset between calls)")
clean()
calls = [_get_next_phone() for _ in range(6)]
expected = [_phone_numbers[i % len(_phone_numbers)] for i in range(6)]
for i, (got, exp) in enumerate(zip(calls, expected), 1):
    assert_eq(f"Call {i}", got, exp)

# ─── Test 4: Verify DB row count is correct ───────────────────────────────────
print("\n[Test 4] DB row sanity check")
clean()
for _ in range(5):
    _get_next_phone()
row = RoundRobinCounter.objects.get(key=_PHONE_COUNTER_KEY)
assert_eq("DB count after 5 calls", row.count, 5)
assert_eq("Only 1 row exists", RoundRobinCounter.objects.filter(key=_PHONE_COUNTER_KEY).count(), 1)

print("\n" + "="*60)
print("  All tests complete!")
print("="*60 + "\n")

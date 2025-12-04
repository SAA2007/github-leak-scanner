# 🧪 Test Progress Indicators

"""Quick test to verify progress bars work."""

from tqdm import tqdm
import time

print("Testing tqdm progress bars...\n")

# Test 1: Basic progress bar
print("[1/3] Basic progress bar:")
for i in tqdm(range(10), desc="Processing", unit="item"):
    time.sleep(0.1)

print("✅ Basic progress bar works\n")

# Test 2: Progress bar with postfix
print("[2/3] Progress bar with status:")
with tqdm(total=5, desc="Scanning", unit="file") as pbar:
    for i in range(5):
        pbar.set_postfix_str(f"Current: file_{i}.txt")
        time.sleep(0.2)
        pbar.update(1)

print("✅ Progress bar with status works\n")

# Test 3: Nested progress bars
print("[3/3] Nested progress bars:")
for epoch in tqdm(range(2), desc="Epochs", position=0):
    for batch in tqdm(range(3), desc="Batches", position=1, leave=False):
        time.sleep(0.1)

print("✅ Nested progress bars work\n")

print("🎉 All progress indicator tests passed!")

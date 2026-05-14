"""Check for truncated thoughts."""
lines = open("brain/thoughts.md", encoding="utf-8").readlines()
cutoffs = 0
total_thoughts = 0
for i, line in enumerate(lines):
    if line.startswith("### "):
        total_thoughts += 1
    s = line.rstrip()
    if not s or len(s) < 20:
        continue
    # Check if a content line is followed by a new thought header (### )
    if i + 1 < len(lines) and lines[i + 1].startswith("### "):
        # Does it end cleanly?
        if s[-1] not in ".!?:*`)>-]\"'":
            if not s.startswith(">>>") and not s.startswith("###"):
                cutoffs += 1
                if cutoffs <= 5:
                    print(f"  CUTOFF L{i}: ...{s[-80:]}")

print(f"\nTotal thoughts: {total_thoughts}")
print(f"Potential mid-sentence cutoffs: {cutoffs}")
print(f"Cutoff rate: {cutoffs/max(total_thoughts,1)*100:.1f}%")

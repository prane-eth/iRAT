# irat/preprocess/gsm8k_prep.py

import json
from pathlib import Path
from datasets import load_dataset
from irat.preprocess.text_normalize import normalize_text_pipeline


# data looks like this
# {
#   "question": "Brad has 3 times as many apples as Sarah…",
#   "answer": "15",
#   "idx": 0
# }

def preprocess_gsm8k_train():
    """
    1. Load GSM8K (Hugging Face).
    2. Normalize each question.
    3. Assign ID = "gsm8k_train_{idx}" using enumerate for the index.
    4. Save out { id, question, answer } per line to processed/gsm8k_train_proc.jsonl.
    """
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "processed"
    out_dir.mkdir(exist_ok=True)

    output_file = out_dir / "gsm8k_train_proc.jsonl"

    # 1. Load GSM8K train split
    ds = load_dataset("gsm8k", "main", split="train")
    print(f"Loaded GSM8K train: {len(ds)} examples")

    processed = []
    for idx, row in enumerate(ds):
        # Use enumerate index to build a unique ID:
        raw_q = row["question"]
        ans = row["answer"]

        # 2. Normalize the question text
        clean_q = normalize_text_pipeline(raw_q)

        # 3. Build the record
        rec = {
            "id": f"gsm8k_train_{idx}",
            "question": clean_q,
            "answer": ans
        }
        processed.append(rec)

    # Sanity check: ensure every record has a non-empty question
    assert all(r["question"] for r in processed)

    # 4. Write out as JSONL
    with open(output_file, "w") as f_out:
        for rec in processed:
            f_out.write(json.dumps(rec) + "\n")

    print(f"Saved {len(processed)} records to {output_file}")


if __name__ == "__main__":
    preprocess_gsm8k_train()

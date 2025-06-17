# irat/preprocess/mbpp_prep.py

import json
from pathlib import Path
from datasets import load_dataset
from irat.preprocess.text_normalize import normalize_text_pipeline
from irat.utils.logger import log_debug

def preprocess_mbpp():
    """
    1. Load MBPP (Hugging Face).
    2. For each row, choose the first non-empty field among 'prompt' or 'text' for the problem statement.
    3. Normalize that text if non-empty; otherwise leave it blank.
    4. Join 'test_list' into a "\n"-separated string.
    5. Use 'task_id' as the unique identifier.
    6. Skip any rows where no valid text field is found.
    7. Save to processed/mbpp_proc.jsonl with fields { id, prompt, code, tests }.
    """
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "processed"
    out_dir.mkdir(exist_ok=True)

    # 1. Load MBPP train split
    ds = load_dataset("mbpp", split="train")
    log_debug(f"Loaded MBPP: {len(ds)} problems")

    # 2. Inspect column names
    cols = list(ds.features.keys())
    log_debug("Available columns in MBPP:", cols)

    output_file = out_dir / "mbpp_proc.jsonl"
    processed = []
    skipped = 0

    for row in ds:
        task_id = row.get("task_id")  # unique ID
        # 2a. Try 'prompt' first
        raw_prompt = row.get("prompt", "")
        # 2b. If 'prompt' is empty, try 'text'
        if not raw_prompt.strip():
            raw_prompt = row.get("text", "")
        # 2c. If still empty, skip
        if not raw_prompt.strip():
            skipped += 1
            continue

        # 3. Normalize the prompt
        norm_prompt = normalize_text_pipeline(raw_prompt)

        # 4. Join test_list
        raw_tests = row.get("test_list", [])
        tests_joined = "\n".join(t.strip() for t in raw_tests)

        # 5. Code snippet (if any)
        raw_code = row.get("code", "").rstrip()

        rec = {
            "id": f"mbpp_{task_id}",
            "prompt": norm_prompt,
            "code": raw_code,
            "tests": tests_joined
        }
        processed.append(rec)

    log_debug(f"Skipped {skipped} rows with no prompt/text.")

    # 6. Sanity: ensure no rec has an empty 'id'
    assert all(r["id"] != "mbpp_None" for r in processed)

    # 7. Write out as JSONL
    with open(output_file, "w", encoding="utf-8") as f_out:
        for rec in processed:
            f_out.write(json.dumps(rec) + "\n")

    log_debug(f"Saved {len(processed)} MBPP records to {output_file}")


if __name__ == "__main__":
    preprocess_mbpp()

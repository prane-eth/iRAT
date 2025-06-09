# irat/preprocess/human_eval_prep.py

import json
from pathlib import Path
from irat.preprocess.text_normalize import normalize_text_pipeline

def preprocess_human_eval():
    """
    1. Read raw HumanEval JSONL from data/human_eval.jsonl.
    2. Each line is a JSON object with keys including:
         - "task_id"             (e.g. "HumanEval/0")
         - "prompt"              (the function signature + docstring)
         - "canonical_solution"  (the reference code body, indented)
         - "test"                (string containing all test assertions)
       Other fields (e.g. "entry_point", "METADATA") are ignored.
    3. Normalize the "prompt" text (remove control chars, Unicode‐NFKC, strip, ensure trailing '?').
    4. Strip leading/trailing whitespace from the "test" block.
    5. Strip leading/trailing whitespace from the "canonical_solution" block.
    6. Write out processed records to processed/human_eval_proc.jsonl with fields:
         {
           "id":      <task_id>,
           "prompt":  <normalized_prompt>,
           "code":    <canonical_solution>,
           "tests":   <raw_test_string>
         }
    """
    repo_root = Path(__file__).resolve().parents[1]
    raw_path = repo_root / "data" / "human_eval.jsonl"
    if not raw_path.exists():
        raise FileNotFoundError(f"{raw_path} not found. Place human_eval.jsonl under data/.")

    out_dir = repo_root / "processed"
    out_dir.mkdir(exist_ok=True)
    output_file = out_dir / "human_eval_proc.jsonl"

    processed = []
    with open(raw_path, "r", encoding="utf-8") as f_in:
        for line in f_in:
            entry = json.loads(line)

            # 1. Extract unique ID
            task_id = entry.get("task_id") or entry.get("id")
            if not task_id:
                raise ValueError("Entry missing 'task_id' or 'id' field")

            # 2. Normalize prompt text
            raw_prompt = entry.get("prompt", "")
            if raw_prompt.strip():
                norm_prompt = normalize_text_pipeline(raw_prompt)
            else:
                norm_prompt = ""

            # 3. Extract canonical solution
            raw_code = entry.get("canonical_solution", "")
            code_clean = raw_code.rstrip()

            # 4. Extract test block
            raw_tests = entry.get("test", "")
            tests_clean = raw_tests.strip()

            processed.append({
                "id":     task_id,
                "prompt": norm_prompt,
                "code":   code_clean,
                "tests":  tests_clean
            })

    # Sanity check
    missing = [r for r in processed if not r["id"]]
    if missing:
        raise ValueError(f"{len(missing)} entries have empty 'id'")

    # Write out JSONL
    with open(output_file, "w", encoding="utf-8") as f_out:
        for rec in processed:
            f_out.write(json.dumps(rec) + "\n")

    print(f"Saved {len(processed)} HumanEval records to {output_file}")


if __name__ == "__main__":
    preprocess_human_eval()

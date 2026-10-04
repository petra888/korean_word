"""Read-only content QA against the current fixed source tree; write results here only."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import re

parser = argparse.ArgumentParser()
parser.add_argument("snapshot", type=Path)
args = parser.parse_args()
root = args.snapshot.resolve()
out = Path(__file__).resolve().parent
checks = []

def read_json(path):
    return json.loads((root / path).read_text())

def read_csv(path):
    with (root / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))

def check(name, condition, details=None):
    checks.append({"name": name, "status": "pass" if condition else "fail", "details": details})

raw = read_json("analysis/vocabulary-raw.json")
source = read_json("analysis/vocabulary.json")
order = read_json("curriculum/textbook-order.json")
bank = read_json("curriculum/pilot-10.json")
words, items = bank["words"], bank["items"]
by_id = {word["id"]: word for word in words}
check("450 raw rows and original fields retained", len(raw) == len(source) == 450 and all(
    all(row[key] == enriched[key] for key in row) for row, enriched in zip(raw, source)))
check("450 textbook positions preserved", len(order["words"]) == 450 and all(
    row["id"] == source_row["content_id"] and row["source_order"] == source_row["source_order"]
    and row["word_original"] == source_row["headword_original"]
    and row["definition_original"] == source_row["definition_original"]
    and row["example_original"] == source_row["example_original"]
    and row["issue_ids"] == source_row["issue_ids"]
    for row, source_row in zip(order["words"], source)))
check("45 consecutive batches of 10 rows", len(order["batches"]) == 45
      and all(len(batch["word_ids"]) == 10 for batch in order["batches"])
      and [wid for batch in order["batches"] for wid in batch["word_ids"]]
      == [row["content_id"] for row in source])
order_csv = read_csv("curriculum/textbook-order.csv")
check("450-row textbook order CSV matches JSON", len(order_csv) == 450 and all(
    row["원문ID"] == word["id"] and row["교재표제어"] == word["word_original"]
    and row["수록순서"] == str(word["source_order"])
    and row["원문사전뜻"] == word["definition_original"]
    and row["원문예문"] == word["example_original"]
    and row["교정이슈"] == ";".join(word["issue_ids"])
    and row["10단어묶음"] == f"T{(word['source_order']-1)//10+1:02d}"
    for row, word in zip(order_csv, order["words"])))
expected_first = ["까탈", "깜냥", "달포", "말미", "선잠", "강단있는", "격의", "융통성", "굴지", "기탄없이"]
check("first 10 words follow source order", [word["word"] for word in words] == expected_first
      and [word["id"] for word in words] == [row["content_id"] for row in source[:10]])
previous = bank.get("previous_items", [])
current_items = {item["id"]: item for item in items}
check("legacy 150 item snapshots retained with distinct bank version", len(previous) == 150
      and len({item["id"] for item in previous}) == 150
      and bank.get("previous_version") != bank["version"])
check("existing answer IDs and correct expressions preserved", all(
    old["id"] in current_items and all(old[key] == current_items[old["id"]][key]
        for key in ("word_id", "meaning_id", "phase", "correct_option_id"))
    and next(option["text"] for option in old["options"] if option["id"] == old["correct_option_id"])
    == next(option["text"] for option in current_items[old["id"]]["options"]
        if option["id"] == old["correct_option_id"]) for old in previous))
check("one new practice context per source word", len(items) - len(previous) == 10 and all(
    sum(item["word_id"] == word["id"] and item["phase"] == "practice"
        and item["id"] not in {old["id"] for old in previous} for item in items) == 1 for word in words))
html = (root / "prototype/pilot-flow.html").read_text()
embedded = json.loads(re.search(r'<script type="application/json" id="curriculum-data">([\s\S]+?)</script>', html).group(1))
check("HTML embedded bank exactly equals canonical JSON", embedded == bank)
item_csv = read_csv("curriculum/pilot-10-items.csv")
item_map = {row["문항ID"]: row for row in item_csv}
check("160 objective CSV rows and unique IDs", len(item_csv) == len(item_map) == len(items) == 160)
item_comparisons = []
for item in items:
    row = item_map[item["id"]]
    options = {option["id"]: option["text"] for option in item["options"]}
    expected = {
        "원문ID": item["word_id"], "의미ID": item["meaning_id"], "단어": by_id[item["word_id"]]["word"],
        "용도": item["phase"], "주간차수": str(item.get("period_sequence", "")),
        "유형": item["type"], "지문": item["prompt"], "정답ID": item["correct_option_id"],
        "정답내용": options[item["correct_option_id"]], "힌트": item["hint"],
        "해설": item["explanation"], "단서": " / ".join(item["context_cues"]), "검수상태": item["review_status"],
        **{"보기" + key: value for key, value in options.items()},
    }
    item_comparisons.append(all(row[key] == value for key, value in expected.items()))
check("all 160 objective CSV fields match canonical JSON", all(item_comparisons))
word_csv = read_csv("curriculum/pilot-10-words.csv")
check("10 word CSV rows preserve source and draft definition", len(word_csv) == 10 and all(
    row["원문ID"] == word["id"] and row["의미ID"] == word["meaning_id"] and row["단어"] == word["word"]
    and row["원문뜻"] == word["source"]["definition_original"]
    and row["원문예문"] == word["source"]["example_original"]
    and row["진단뜻초안"] == word["definition_diagnostic"]["definition_for_check"]
    and row["진단뜻사전검증"] == "False" and row["승인상태"] == "draft"
    for row, word in zip(word_csv, words)))
writing_csv = read_csv("curriculum/pilot-10-writing.csv")
writing_comparisons = []
for row in writing_csv:
    word = by_id[row["원문ID"]]
    writing = word["writing"]
    prompt = writing if row["작문구분"] == "기본" else writing["alternative"]
    writing_comparisons.append(row["의미ID"] == word["meaning_id"] and row["원문단어"] == word["word"]
        and row["학습표시"] == word["display_word"] and row["질문"] == prompt["prompt"]
        and row["문장틀"] == prompt["sentence_frame"] and row["교사용예시"] == prompt["teacher_sample"]
        and json.loads(row["작문판정JSON"]) == writing["judgment_labels"]
        and json.loads(row["교사관찰안내JSON"]) == writing["teacher_guidance"] and row["승인상태"] == "draft")
check("20 writing CSV rows exactly match JSON metadata", len(writing_csv) == 20 and all(writing_comparisons))
check("all items have one blank, 4 unique choices and valid key", all(
    item["prompt"].count("(____)") == 1 and len(item["options"]) == 4
    and len({option["text"] for option in item["options"]}) == 4
    and {option["id"] for option in item["options"]} == {"a", "b", "c", "d"}
    and item["correct_option_id"] in {option["id"] for option in item["options"]} for item in items))
check("correct answer form is listed in accepted_forms", all(
    next(option["text"] for option in item["options"] if option["id"] == item["correct_option_id"])
    in by_id[item["word_id"]]["accepted_forms"] for item in items))
literal_leaks = []
for item in items:
    answer = next(option["text"] for option in item["options"] if option["id"] == item["correct_option_id"])
    for field in ("prompt", "hint"):
        normalized = re.sub(r"\s+", "", item[field])
        if re.sub(r"\s+", "", answer) in normalized or re.sub(r"\s+", "", by_id[item["word_id"]]["display_word"]) in normalized:
            literal_leaks.append({"item_id": item["id"], "field": field})
check("no literal correct answer in prompt/hint", not literal_leaks, literal_leaks)
check("all words/items explicitly pending approval and dictionary unverified", bank["status"] == "teacher_review_required"
      and all(word["approval_status"] == "draft" and word["definition_diagnostic"]["dictionary_verified"] is False
              for word in words) and all(item["review_status"] == "draft" for item in items))
check("removed numeric writing criteria absent; 3 judgment buttons metadata", all(
    "criteria" not in word["writing"] and [label["id"] for label in word["writing"]["judgment_labels"]]
    == ["correct", "incorrect", "uncertain"] for word in words))
content_doc = (root / "documents/10-word-curriculum.md").read_text()
check("teacher content document includes every objective ID/prompt/hint/explanation", all(
    item["id"] in content_doc and all(item[field] in content_doc for field in ("prompt", "hint", "explanation"))
    for item in items))
check("teacher content document includes all 20 writing prompts/frames/examples", all(
    all(prompt[key] in content_doc for key in ("prompt", "sentence_frame", "teacher_sample"))
    for word in words for prompt in (word["writing"], word["writing"]["alternative"])))

pattern_stats = []
for word in words:
    own_items = [item for item in items if item["word_id"] == word["id"]]
    pattern_stats.append({"word_id": word["id"], "word": word["word"], "item_count": len(own_items),
        "unique_option_sets": len({tuple(sorted(option["text"] for option in item["options"])) for item in own_items}),
        "unique_hints": len({item["hint"] for item in own_items}),
        "unique_explanations": len({item["explanation"] for item in own_items}),
        "answer_position_counts": dict(collections.Counter(item["correct_option_id"] for item in own_items))})
report = {"base_commit": "0d7598638dac12c59e2cf7d0151b43a73f51c42a", "verified_scope": "fixed working tree, not a committed revision", "snapshot": str(root),
    "status": "pass" if all(check["status"] == "pass" for check in checks) else "fail",
    "check_count": len(checks), "checks": checks, "pattern_stats": pattern_stats,
    "source_issue_ids_first_10": {word["id"]: word["source"]["issue_ids"] for word in words if word["source"]["issue_ids"]},
    "content_counts": {"source_rows": len(source), "unique_raw_headwords": len({row["headword_original"] for row in source}),
        "source_batches": len(order["batches"]), "pilot_words": len(words), "objective_items": len(items), "writing_prompts": len(writing_csv),
        "phase_counts": dict(collections.Counter(item["phase"] for item in items))},
    "checksums": {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in (
        "analysis/vocabulary.json", "curriculum/textbook-order.json", "curriculum/pilot-10.json", "prototype/pilot-flow.html")},
    "limits": ["Dataset/source-field comparison does not independently reread all 60 PDF pages.",
        "No external dictionary verification, Korean teacher approval, age norms or real-student efficacy test.",
        "Literal answer leakage check does not imply absence of inferential cues or easy distractors.",
        "Structural pass is not a publish/education approval."]}
(out / "content-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({"status": report["status"], "checks": len(checks), "counts": report["content_counts"],
    "failed": [check["name"] for check in checks if check["status"] == "fail"]}, ensure_ascii=False))
raise SystemExit(report["status"] != "pass")

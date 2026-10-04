#!/usr/bin/env python3
"""Read-only snapshot of the canonical content for an independent text review.

The accompanying Markdown report records which text was read and its limits.
Structure counts do not constitute dictionary or qualified-teacher approval.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    source = args.project / "curriculum" / "pilot-10.json"
    raw = source.read_bytes()
    data = json.loads(raw)
    reviewed_authored_sha256 = "83cb6653362f671d7080a1515ceb112c315d224365744b0f09549a703131dc4c"
    authored_payload = {key: value for key, value in data.items() if key not in {"previous_items", "previous_version"}}
    authored_sha256 = hashlib.sha256((json.dumps(authored_payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")).hexdigest()
    if authored_sha256 != reviewed_authored_sha256:
        raise SystemExit("The authored current content changed after the recorded independent reading; re-review it before regenerating this snapshot.")
    out = Path(__file__).resolve().parent
    words = {word["id"]: word for word in data["words"]}
    review_focus = {
        "W0001": "불필요한 요구가 일을 지연·방해하는 상황인지 읽음; 정당한 안전 요구와 구별하는 뜻 범위 유지",
        "W0002": "혼자 할 수 있는 일과 어려운 일을 비교해 자신의 능력 범위를 가리키는지 읽음",
        "W0003": "한 달보다 조금 긴 전체 기간인지 읽음; 정확한 날짜 수로 뜻을 고정하지 않는 해설 확인",
        "W0004": "다른 일을 할 시간 여유를 얻거나 받은 상황인지 읽음; 글 끝부분의 다른 뜻과 구별",
        "W0005": "잠의 깊이를 시간대·기상 시각과 구별해 읽음; 사전/사후/지연 보기 집합 구별 확인",
        "W0006": "검토 뒤 굳게 결단·실행하는 태도인지 읽음; 경솔함·무조건 고집과 구별",
        "W0007": "마음을 터놓기 전후 관계의 거리인지 읽음; C13의 분노·후회 감정 보기 중첩 제거 확인",
        "W0008": "상황 변화에 맞춰 방법을 조정하는지 읽음; 목표·안전 기준 유지와 발휘하다 결합 단서 감소 확인",
        "W0009": "여러 대상 중 손꼽힐 뛰어남인지 읽음; 기간·유명함을 필수 조건으로 반복하지 않는지 확인",
        "W0010": "꺼리거나 어려워하지 않고 말하는 태도인지 읽음; 부정 범위와 없이 중복 여부 확인",
    }
    item_rows = []
    for item in data["items"]:
        word = words[item["word_id"]]
        options = {option["id"]: option["text"] for option in item["options"]}
        item_rows.append({
            "item_id": item["id"], "word_id": word["id"],
            "word": word["word"], "phase": item["phase"],
            "prompt": item["prompt"],
            **{f"option_{key}": options[key] for key in "abcd"},
            "correct_option_id": item["correct_option_id"],
            "correct_text": options[item["correct_option_id"]],
            "hint": item["hint"], "explanation": item["explanation"],
            "context_cues": " | ".join(item["context_cues"]),
            "review_focus": review_focus[word["id"]],
            "text_review_result": "추가 명백한 정답키·문장 성립 결함 미발견",
            "approval_limit": "교육 초안; 사전 대조·국어 교사 승인 미실행",
        })
    writing_rows = []
    for word in data["words"]:
        for variant, writing in (
            ("basic", word["writing"]),
            ("alternate", word["writing"]["alternative"]),
        ):
            writing_rows.append({
                "word_id": word["id"], "word": word["word"],
                "variant": variant, "prompt": writing["prompt"],
                "sentence_frame": writing["sentence_frame"],
                "teacher_sample": writing["teacher_sample"],
                "text_review_result": "추가 명백한 문장 성립 결함 미발견",
                "approval_limit": "교육 초안; 실제 학생 난도·교사 판정 일치도 미검증",
            })
    for name, rows in (("item-review.csv", item_rows), ("writing-review.csv", writing_rows)):
        with (out / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    stats = []
    for word in data["words"]:
        items = [item for item in data["items"] if item["word_id"] == word["id"]]
        evaluation = [item for item in items if item["phase"] != "practice"]
        stats.append({
            "word_id": word["id"], "items": len(items),
            "practice_items": sum(item["phase"] == "practice" for item in items),
            "evaluation_items": len(evaluation),
            "evaluation_option_sets": len({tuple(sorted(option["text"] for option in item["options"])) for item in evaluation}),
            "evaluation_hints": len({item["hint"] for item in evaluation}),
            "evaluation_explanations": len({item["explanation"] for item in evaluation}),
            "pre_post_delayed_option_sets": len({tuple(sorted(option["text"] for option in item["options"])) for item in items if item["phase"] in {"pretest", "posttest", "delayed"}}),
        })
    summary = {
        "source": str(source), "source_sha256": hashlib.sha256(raw).hexdigest(),
        "reviewed_authoring_snapshot_sha256": reviewed_authored_sha256,
        "authored_payload_without_legacy_sha256": authored_sha256,
        "legacy_history_only_change_from_read_snapshot": authored_sha256 == reviewed_authored_sha256,
        "reviewed_current_items": len(item_rows),
        "reviewed_current_words_and_items_sha256": hashlib.sha256(json.dumps({"words": data["words"], "items": data["items"]}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "previous_items_count_excluded_from_reviewed_current_count": len(data.get("previous_items", [])),
        "item_count": len(item_rows), "writing_count": len(writing_rows),
        "phases": dict(collections.Counter(item["phase"] for item in data["items"])),
        "source_order": [word["word"] for word in data["words"]],
        "approval_statuses": sorted({word["approval_status"] for word in data["words"]}),
        "review_statuses": sorted({item["review_status"] for item in data["items"]}),
        "all_dictionary_unverified": all(word["definition_diagnostic"]["dictionary_verified"] is False for word in data["words"]),
        "pattern_stats": stats,
    }
    (out / "review-snapshot.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "source_sha256", "reviewed_current_items", "writing_count",
        "previous_items_count_excluded_from_reviewed_current_count",
        "legacy_history_only_change_from_read_snapshot",
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

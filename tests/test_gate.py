"""H3 regression gate — gate.main の単体テスト（LLM 不要・課金ゼロ）。

eval_runs.jsonl を一時ファイルで組み立て、exit code を検証する。
"""
import json

from genai_prod_kit.evals import gate


def _write_runs(path, runs):
    with open(path, "w", encoding="utf-8") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")


def _run(acc):
    # gate が参照する最低限のフィールドだけ持つ run dict
    return {"accuracy": acc, "git_sha": "deadbeefcafe"}


def test_skips_when_fewer_than_two_runs(tmp_path):
    p = tmp_path / "eval_runs.jsonl"
    _write_runs(p, [_run(0.90)])
    assert gate.main(str(p)) == 0  # 比較不能 → skip(0)


def test_pass_when_accuracy_improves(tmp_path):
    p = tmp_path / "eval_runs.jsonl"
    _write_runs(p, [_run(0.90), _run(0.95)])
    assert gate.main(str(p)) == 0


def test_pass_when_drop_within_threshold(tmp_path):
    # 既定 threshold 0.02。1pt 低下は許容
    p = tmp_path / "eval_runs.jsonl"
    _write_runs(p, [_run(0.90), _run(0.89)])
    assert gate.main(str(p)) == 0


def test_fail_when_drop_exceeds_threshold(tmp_path):
    # 5pt 低下 → ブロック(1)
    p = tmp_path / "eval_runs.jsonl"
    _write_runs(p, [_run(0.90), _run(0.85)])
    assert gate.main(str(p)) == 1

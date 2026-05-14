"""JSON配列をフィルタリングしてCSVに出力するスクリプト。

使用例:
    python json_to_csv.py users.json out.csv --filter status=active
    python json_to_csv.py users.json out.csv \
        --filter status=active --filter role=admin --match any
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import webbrowser
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FEEDBACK_URL = "https://github.com/osamu19840914/my-first-claude-project/issues/new"


def send_feedback() -> int:
    print(f"フィードバックをお待ちしています！\n以下のURLからIssueを作成してください:\n{FEEDBACK_URL}")
    webbrowser.open(FEEDBACK_URL)
    return 0


def parse_filter(expr: str) -> tuple[str, str]:
    if "=" not in expr:
        raise argparse.ArgumentTypeError(
            f"--filter は key=value の形式で指定してください: {expr!r}"
        )
    key, value = expr.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"key が空です: {expr!r}")
    return key, value


def matches(record: dict, filters: list[tuple[str, str]], mode: str) -> bool:
    if not filters:
        return True
    results = (str(record.get(k, "")) == v for k, v in filters)
    return all(results) if mode == "all" else any(results)


def collect_columns(records: list[dict]) -> list[str]:
    columns: dict[str, None] = {}
    for record in records:
        for key in record:
            columns.setdefault(key, None)
    return list(columns)


def load_json(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"エラー: 入力ファイルが見つかりません: {path}")
    except PermissionError:
        raise SystemExit(f"エラー: 入力ファイルを読み取る権限がありません: {path}")
    except UnicodeDecodeError as e:
        raise SystemExit(f"エラー: 入力ファイルのUTF-8デコードに失敗しました: {e}")
    except OSError as e:
        raise SystemExit(f"エラー: 入力ファイルの読み込みに失敗しました: {e}")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"エラー: JSONの解析に失敗しました ({path} 行{e.lineno} 列{e.colno}): {e.msg}"
        )

    if not isinstance(data, list):
        raise SystemExit(
            f"エラー: 入力JSONはオブジェクトの配列である必要があります（実際: {type(data).__name__}）"
        )
    return data


def write_csv(path: Path, records: list[dict], columns: list[str]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
    except PermissionError:
        raise SystemExit(f"エラー: 出力ファイルを書き込む権限がありません: {path}")
    except OSError as e:
        raise SystemExit(f"エラー: 出力ファイルの書き込みに失敗しました: {e}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, nargs="?", help="入力JSONファイル（オブジェクトの配列）")
    parser.add_argument("output", type=Path, nargs="?", help="出力CSVファイル")
    parser.add_argument(
        "--filter",
        action="append",
        type=parse_filter,
        default=[],
        metavar="KEY=VALUE",
        help="フィルタ条件。複数指定可能",
    )
    parser.add_argument(
        "--match",
        choices=("all", "any"),
        default="all",
        help="複数フィルタの結合方法（all=AND, any=OR）。デフォルト: all",
    )
    parser.add_argument(
        "--feedback",
        action="store_true",
        help="フィードバックを送るためのURLを表示してブラウザを開きます",
    )
    args = parser.parse_args(argv)

    if args.feedback:
        return send_feedback()

    if args.input is None or args.output is None:
        parser.error("input と output は必須です（--feedback なしの場合）")

    data = load_json(args.input)
    filtered = [r for r in data if isinstance(r, dict) and matches(r, args.filter, args.match)]
    columns = collect_columns(filtered)
    write_csv(args.output, filtered, columns)

    print(f"{len(filtered)} 件を {args.output} に書き出しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())

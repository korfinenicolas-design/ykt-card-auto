#!/usr/bin/env python3
"""
YKT Card Auto — 雨课堂卡片模式作业自动完成工具

从已知答案提交，或自动探测正确答案。

用法:
  # 从已知答案提交
  python ykt_card_auto.py \\
    --sessionid xxx --csrftoken xxx \\
    --classroom_id 30112085 --cards_id 6995005 \\
    --answers '{"1": "A", "2": "BC", "3": "D"}'

  # 自动探测答案（每题先答A获取正确答案，再修正提交）
  python ykt_card_auto.py \\
    --sessionid xxx --csrftoken xxx \\
    --classroom_id 30112085 --cards_id 6995005 \\
    --auto-answer

  # 仅列出题目ID，不提交
  python ykt_card_auto.py \\
    --sessionid xxx --csrftoken xxx \\
    --classroom_id 30112085 --cards_id 6995005 \\
    --list-only
"""

import argparse
import json
import sys
import requests


BASE_URL = "https://www.yuketang.cn/v2/api/web/cards"


def create_session(sessionid: str, csrftoken: str) -> requests.Session:
    """创建带 Cookie 的 requests Session"""
    s = requests.Session()
    s.cookies.set("sessionid", sessionid, domain="www.yuketang.cn")
    s.cookies.set("csrftoken", csrftoken, domain="www.yuketang.cn")
    s.headers.update({
        "xtbz": "ykt",
        "X-CSRFToken": csrftoken,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    return s


def get_problem_ids(session: requests.Session, cards_id: str, classroom_id: str) -> list:
    """获取作业中所有题目ID列表"""
    r = session.get(
        f"{BASE_URL}/detlist/{cards_id}?classroom_id={classroom_id}"
    )
    data = r.json()
    if data.get("errcode") != 0:
        raise RuntimeError(f"获取题目列表失败: {data.get('errmsg', 'Unknown error')}")
    return [p["id"] for p in data["data"]["problem_results"]]


def submit_answer(
    session: requests.Session,
    cards_problem_id: int,
    result: str,
    classroom_id: str,
) -> dict:
    """提交单个答案"""
    r = session.post(
        f"{BASE_URL}/problem_result",
        json={
            "cards_problem_id": cards_problem_id,
            "result": result,
            "classroom_id": classroom_id,
        },
    )
    return r.json()


def auto_answer_problem(
    session: requests.Session,
    pid: int,
    classroom_id: str,
    index: int,
    total: int,
    options: list[str] = None,
) -> str | None:
    """
    自动探测一道题的正确答案。

    策略: 先提交"A"作为试探。如果 API 返回了正确答案（data.answer），
    就用正确答案修正提交。如果恰好"A"就是对的，直接通过。

    适用于单选题 (option_list=['A','B','C','D'])。
    多选题也可用此方法，但稳妥起见建议已知答案后手动填写。
    """
    if options is None:
        options = ["A", "B", "C", "D"]

    # 第一步：提交"A"作为试探
    res = submit_answer(session, pid, "A", classroom_id)

    if res.get("errcode") != 0:
        print(f"  [{index:2d}/{total}] ❌ id={pid}: 提交失败: {res.get('errmsg')}")
        return None

    answer = res.get("data", {}).get("answer")

    if res.get("data", {}).get("correct") is True:
        print(f"  [{index:2d}/{total}] ✅ id={pid} 答案=A (一击命中)")
        return "A"

    if answer:
        clean = str(answer).strip()
        if clean.upper() != "A":
            # 用正确答案修正提交
            res2 = submit_answer(session, pid, clean, classroom_id)
            if res2.get("data", {}).get("correct") is True:
                print(f"  [{index:2d}/{total}] ✅ id={pid} 答案={clean}")
            else:
                print(f"  [{index:2d}/{total}] ⚠️ id={pid} 获取到答案={clean} 但修正后仍不正确")
        return clean

    # 如果不返回answer字段，回退到暴力枚举
    print(f"  [{index:2d}/{total}] 🔄 id={pid} 未直接返回答案，开始枚举...")
    for opt in options:
        res = submit_answer(session, pid, opt, classroom_id)
        if res.get("data", {}).get("correct") is True:
            print(f"  [{index:2d}/{total}] ✅ id={pid} 答案={opt} (枚举找到)")
            return opt

    print(f"  [{index:2d}/{total}] ❌ id={pid}: 无法获取正确答案")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="雨课堂卡片模式作业自动完成工具"
    )
    parser.add_argument("--sessionid", required=True, help="sessionid Cookie")
    parser.add_argument("--csrftoken", required=True, help="csrftoken Cookie")
    parser.add_argument("--classroom_id", required=True, help="雨课堂教室ID")
    parser.add_argument("--cards_id", required=True, help="卡片ID (leaf_type_id)")
    parser.add_argument("--answers", help="答案映射 JSON, 如 '{\"1\":\"A\",\"2\":\"BC\"}'")
    parser.add_argument(
        "--auto-answer",
        action="store_true",
        help="自动探测答案（提交A获取正确答案再修正）",
    )
    parser.add_argument("--list-only", action="store_true", help="仅列出题目ID")
    args = parser.parse_args()

    if not args.auto_answer and not args.answers and not args.list_only:
        parser.error("请提供 --answers 或 --auto-answer 或 --list-only")

    session = create_session(args.sessionid, args.csrftoken)

    # 获取题目ID列表
    try:
        problem_ids = get_problem_ids(session, args.cards_id, args.classroom_id)
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"📚 共 {len(problem_ids)} 道题\n")

    if args.list_only:
        for i, pid in enumerate(problem_ids, 1):
            print(f"  [{i:2d}] id={pid}")
        return

    # ---- 从已知答案提交 ----
    if args.answers:
        answers = json.loads(args.answers)
        print("📋 使用预设答案提交:\n")
        for idx_str, ans in sorted(answers.items()):
            idx = int(idx_str) - 1  # 1-indexed -> 0-indexed
            if idx < 0 or idx >= len(problem_ids):
                print(f"  [{idx_str:>2}] ⚠️ 索引越界，跳过")
                continue
            pid = problem_ids[idx]
            res = submit_answer(session, pid, ans, args.classroom_id)
            correct = res.get("data", {}).get("correct", False)
            mark = "✅" if correct else "❌"
            print(f"  [{idx_str:>2}] {mark} id={pid} ans={ans}")
    
    # ---- 自动探测答案 ----
    if args.auto_answer:
        print("🤖 自动探测答案模式:\n")
        results = []
        for i, pid in enumerate(problem_ids):
            answer = auto_answer_problem(
                session, pid, args.classroom_id, i + 1, len(problem_ids)
            )
            results.append({"index": i + 1, "pid": pid, "answer": answer})

        print("\n===== 结果汇总 =====")
        for r in results:
            ans_str = r["answer"] if r["answer"] else "❓"
            print(f"  [{r['index']:2d}] id={r['pid']} 答案={ans_str}")
        print(f"\n✅ 完成! {len(results)} 题")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
辅助工具：通过 leaf_id 获取 cards_id，或列出课程中未完成的卡片作业。

用法:
  # 获取某个 leaf_id 对应的 cards_id
  python ykt_find_cards.py --sessionid xxx --csrftoken xxx \
    --classroom_id 30112085 --leaf_id 83664915

  # 获取课程所有未完成的卡片作业
  python ykt_find_cards.py --sessionid xxx --csrftoken xxx \
    --classroom_id 30112085 --course_id 1976756 \
    --scan-incomplete
"""

import argparse
import sys
import requests

BASE = "https://www.yuketang.cn"
MOOCAPI = f"{BASE}/mooc-api/v1/lms/learn"


def create_session(sessionid, csrftoken):
    s = requests.Session()
    s.cookies.set("sessionid", sessionid, domain="yuketang.cn")
    s.cookies.set("csrftoken", csrftoken, domain="yuketang.cn")
    s.headers.update({"xtbz": "ykt", "X-CSRFToken": csrftoken})
    return s


def get_leaf_info(session, classroom_id, leaf_id):
    """获取 leaf_type_id (= cards_id)"""
    r = session.get(
        f"{MOOCAPI}/leaf_info/{classroom_id}/{leaf_id}/?classroom_id={classroom_id}"
    )
    data = r.json()
    if not data.get("success"):
        print(f"❌ 获取 leaf_info 失败: {data.get('msg')}")
        return None
    return data["data"]


def get_course_chapters(session, classroom_id):
    """获取课程章节列表，查找未完成的卡片作业"""
    # 需要 sign (university_id)，这里用 common 值或从 classroom_info 获取
    r = session.get(
        f"{MOOCAPI}/classroom_info/?classroom_id={classroom_id}&uv_id=0"
    )
    if not r.json().get("success"):
        print("❌ 获取教室信息失败")
        return None

    # 获取课程章节（sign 是学校ID，这里从 URL 推断或接收参数）
    # 简单起见，让用户提供 sign
    return None


def main():
    parser = argparse.ArgumentParser(description="查找雨课堂卡片作业信息")
    parser.add_argument("--sessionid", required=True)
    parser.add_argument("--csrftoken", required=True)
    parser.add_argument("--classroom_id", required=True)
    parser.add_argument("--leaf_id", help="leaf_id, 获取对应的 cards_id")
    args = parser.parse_args()

    session = create_session(args.sessionid, args.csrftoken)

    if args.leaf_id:
        info = get_leaf_info(session, args.classroom_id, args.leaf_id)
        if not info:
            sys.exit(1)
        print(f"名称: {info.get('name')}")
        print(f"类型: leaf_type={info.get('leaf_type')} (7=卡片模式)")
        print(f"cards_id: {info.get('content_info', {}).get('leaf_type_id')}")
        print(f"截止时间戳: {info.get('score_deadline')}")
        print(f"已批改: {info.get('is_assessed')}")


if __name__ == "__main__":
    main()

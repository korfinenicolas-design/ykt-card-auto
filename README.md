<div align="center">

# 🐾 YKT Card Auto

**雨课堂卡片模式作业自动完成工具**

> 逆向分析 leaf_type=7 卡片作业 API，自动探测正确答案，一键满分

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![Node.js 18+](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![雨课堂](https://img.shields.io/badge/雨课堂-逆向-red.svg)](https://www.yuketang.cn)

</div>

---

## 🔥 这是什么？

雨课堂的 PPT **卡片模式作业**（`leaf_type=7`）是一种把题目嵌在课件 PPT 里的特殊作业类型。

这个工具通过逆向分析其 API，实现了**自动获取正确答案并提交**—— 无需手动做题、无需人工看题。

**核心理念：** 提交任意答案 → API 直接返回正确答案 → 修正提交 → 满分 ✅

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 🤖 **自动探测答案** | 每题提交"A"试探，API 响应自带正确答案，自动修正提交 |
| 📋 **已知答案提交** | 已有答案列表？直接批量提交 |
| 🔍 **仅列出题目** | 只看题不答，方便排查 |
| 🐍 **Python 版** | 完整命令行工具，`pip install requests` 即可 |
| 🟢 **Node.js 版** | 零依赖，原生 `fetch`，即开即用 |

## 🚀 快速上手

### 1️⃣ 获取 Cookie

打开 [雨课堂](https://www.yuketang.cn) 并登录，从浏览器 DevTools → Application → Cookies 获取：

| Cookie | 说明 |
|--------|------|
| `sessionid` | 登录会话 ID |
| `csrftoken` | CSRF 令牌 |

### 2️⃣ 获取卡片 ID

```bash
# 找到作业 URL 中的 classroom_id 和 leaf_id
# 示例: https://www.yuketang.cn/h5/homework/2597/30112085/83664915

# 通过 leaf_info API 获取 cards_id（= leaf_type_id）
# 或直接使用辅助工具
```

### 3️⃣ 一键答题

```bash
# Python
pip install requests
python ykt_card_auto.py \
  --sessionid "你的sessionid" \
  --csrftoken "你的csrftoken" \
  --classroom_id "30112085" \
  --cards_id "6995005" \
  --auto-answer
```

```bash
# Node.js（无需安装依赖）
node ykt_card_auto.mjs \
  --sessionid "你的sessionid" \
  --csrftoken "你的csrftoken" \
  --classroom_id "30112085" \
  --cards_id "6995005" \
  --auto-answer
```

输出示例：
```
📚 共 22 道题

[ 1/22] ✅ id=21565002 答案=D
[ 2/22] ✅ id=21565003 答案=C
[ 3/22] ✅ id=21565004 答案=D
...
===== 结果汇总 =====
[ 1] id=21565002 答案=D
[22] id=21565023 答案=C

✅ 完成! 22 题 满分!
```

### 已知答案提交

```bash
python ykt_card_auto.py \
  --sessionid "xxx" --csrftoken "xxx" \
  --classroom_id "30112085" --cards_id "6995005" \
  --answers '{"1":"D","2":"C","3":"D"}'
```

## 🧠 技术揭秘

### 真正的提交 API

```http
POST /v2/api/web/cards/problem_result
Content-Type: application/json

{
  "cards_problem_id": 21565002,
  "result": "A",
  "classroom_id": "30112085"
}
```

```json
{
  "errcode": 0,
  "data": {
    "correct": false,
    "score": 0,
    "answer": "D"    // ← 直接返回正确答案！
  }
}
```

### 伪 API（全是摆设 ❌）

这些 `POST` 路由**全部返回** `{"errcode": 0, "data": {"2597": <user_id>}}`，不处理任何逻辑：

- `submit_answer`
- `problem_submit`
- `record_answer`
- `view_problem/{id}`
- `batch_update_answer`
- `view_depth`

> 当时排查这些占位路由花了不少时间……详情见 [逆向工程笔记](docs/reverse-engineering.md)。

### 关键发现

- 🔓 **服务端不校验答题次数** — 前端限制只是摆设
- 📨 **API 直接泄露正确答案** — 提交任意答案都会返回 `data.answer`
- 🃏 **cards_id = leaf_type_id** — 卡片作业的唯一标识

## 📁 项目结构

```
ykt-card-auto/
├── README.md                     # 你正在看的
├── LICENSE                       # MIT
├── ykt_card_auto.py              # Python 主脚本
├── ykt_card_auto.mjs             # Node.js 版（零依赖）
├── ykt_find_cards.py             # 辅助：查询 cards_id
└── docs/
    └── reverse-engineering.md    # 完整逆向过程
```

## ⚠️ 注意事项

- 🔑 Cookie 有效期有限，过期需要重新获取
- ⏰ 截止日期后的作业可能无法提交
- 📖 **本工具仅供学习研究使用**

## 📄 License

MIT

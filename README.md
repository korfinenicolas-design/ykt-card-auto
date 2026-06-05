# YKT Card Auto — 雨课堂卡片模式作业自动完成工具

> 逆向分析雨课堂卡片模式（leaf_type=7）作业的提交 API，实现自动获取答案并提交。

## 📝 背景

雨课堂的 PPT 卡片模式作业是一种特殊作业类型，题目嵌入在 PPT 幻灯片中。本文档和脚本源于对雨课堂卡片模式作业的完整逆向工程。

## 🔍 核心发现

### 提交 API

真正的提交接口是：

```
POST /v2/api/web/cards/problem_result
Body: {"cards_problem_id": <问题ID>, "result": "<答案>", "classroom_id": "<教室ID>"}
```

**关键特性**：
- 不验证答题次数（尽管页面可能显示有次数限制）
- 提交任意答案后，响应中 `data.answer` 字段会**直接返回正确答案**
- 可以通过先提交错误答案获取正确答案，再修正提交来拿到满分

### 伪 API（占位路由）

以下路由**全部是占位路由**，永远返回 `{"2597": <user_id>}`，不处理任何业务逻辑：

- `POST /v2/api/web/cards/submit_answer`
- `POST /v2/api/web/cards/problem_submit`
- `POST /v2/api/web/cards/record_answer`
- `POST /v2/api/web/cards/view_problem/{CARDS}`
- `POST /v2/api/web/cards/batch_update_answer`
- `POST /v2/api/web/cards/view_depth`

## 🚀 快速使用

### 前置条件

1. 从浏览器获取雨课堂 Cookie:
   - `sessionid` — 登录后的会话 ID
   - `csrftoken` — CSRF 令牌

2. 获取卡片 ID:
   - 打开作业页面，URL 格式: `https://www.yuketang.cn/h5/homework/{sign}/{classroom_id}/{leaf_id}`
   - 通过 `leaf_info` API 获取 `leaf_type_id`，这就是 `cards_id`
   ```
   GET /mooc-api/v1/lms/learn/leaf_info/{classroom_id}/{leaf_id}/?classroom_id={classroom_id}
   ```

### 使用方法

```bash
# 安装
git clone https://github.com/yourname/ykt-card-auto
cd ykt-card-auto
pip install requests

# 编辑 config.py 填写 Cookie 和教室信息
# 或直接命令行传参
python ykt_card_auto.py \
  --sessionid "your_sessionid" \
  --csrftoken "your_csrftoken" \
  --classroom_id "30112085" \
  --cards_id "6995005"
```

### 自动获取答案

```bash
python ykt_card_auto.py \
  --sessionid "xxx" --csrftoken "xxx" \
  --classroom_id "30112085" --cards_id "6995005" \
  --auto-answer
```

`--auto-answer` 模式会：
1. 每道题提交 "A" 获取 API 返回的正确答案
2. 如首答错误，用返回的正确答案修正提交
3. 全部完成满分

## 📦 项目结构

```
ykt-card-auto/
├── README.md            # 本文件
├── LICENSE              # MIT License
├── ykt_card_auto.py     # 主脚本：自动提交答案
├── ykt_get_answers.py   # 辅助脚本：提取题目/答案
└── docs/
    └── reverse-engineering.md  # 逆向工程详细记录
```

## ⚠️ 注意事项

1. **Cookie 会过期**，需要定期更新
2. 作业有截止日期，过期的作业可能无法提交
3. 部分课程需要先选课/购买才能访问
4. 本工具仅供学习研究使用

## 📄 License

MIT

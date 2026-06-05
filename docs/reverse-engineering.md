# 逆向工程笔记

> 记录雨课堂卡片模式（leaf_type=7）作业提交 API 的完整逆向过程。

## TL;DR

真正的提交 API 只有一个：`POST /v2/api/web/cards/problem_result`。  
其他 `/v2/api/web/cards/*` 全是占位路由。

## 完整过程

### 阶段一：瞎猜接口（失败）

通过阅读前端 Vue 源码（SFC 编译后的 `$options.methods`），发现提交逻辑里引用了这些 POST 端点：

```
POST /v2/api/web/cards/submit_answer
POST /v2/api/web/cards/problem_submit
POST /v2/api/web/cards/record_answer
POST /v2/api/web/cards/view_problem/{CARDS}
POST /v2/api/web/cards/batch_update_answer
POST /v2/api/web/cards/view_depth
POST /v2/api/web/cards/problem_result   ← 这个才是真的
```

前 6 个全部返回占位数据：`{"errcode": 0, "data": {"2597": 80774976}}`。  
只有 `problem_result` 会真正处理答案并返回 `correct/score/answer` 字段。

### 阶段二：CDP 浏览器自动化

通过 Chrome DevTools Protocol (CDP) 操作已登录的浏览器：

1. 打开 `https://www.yuketang.cn/v2/web/studentCards/{classroom_id}/{cards_id}/{course_id}`
2. 设置移动端视口 (390x844)，因为卡片页面只有移动端布局
3. 通过 `document.querySelector("#app").__vue__` 找到 Vue 根实例
4. 深度遍历组件树 (`$children`)，找到包含 `submitObjectProblem` 方法的组件
5. 通过 `component.$options.methods` 获取源码

关键源码片段：

```javascript
// Vue 组件 submitObjectProblem 方法简化版
submitObjectProblem: function() {
    var success = this.controlParam.problemCount > this.controlParam.curIndex;
    if (!success) { return; }
    
    var r = API.pc.studentCards.POST_PROBLEM_RESULT;
    // r = "/v2/api/web/cards/problem_result"
    
    var a = {
        cards_problem_id: this.postParam.problem.id,
        result: this.postParam.result,
        classroom_id: this.classroom_id,
        duration: this.duration
    };
    
    request.post(r, a).then(function(res) {
        if (res.errcode === 0) {
            this.showResult(res.data);
        }
    });
}
```

通过 CDP `Runtime.evaluate` 执行 `window.API.pc.studentCards` 获取所有可用端点：

```json
{
  "POST_PROBLEM_RESULT": "/v2/api/web/cards/problem_result",
  "STUDENT_CARDS": "/v2/api/web/cards/studentCards/{id}",
  "VIEW_DEPTH": "/v2/api/web/cards/view_depth",
  "VIEW_PROBLEM": "/v2/api/web/cards/view_problem/{id}",
  "GET_PROBLEM_RESULT": "/v2/api/web/cards/get_problem_result"
}
```

### 阶段三：确认真实 API

直接通过 curl 测试：

```bash
# 假的 - 永远返回占位数据
curl -X POST "https://www.yuketang.cn/v2/api/web/cards/submit_answer" \
  -H "xtbz: ykt" -H "Content-Type: application/json" \
  -d '{"cards_problem_id": 123, "result": "A"}'
# → {"errcode": 0, "data": {"2597": 80774976}}

# 真的 - 返回答题结果
curl -X POST "https://www.yuketang.cn/v2/api/web/cards/problem_result" \
  -H "xtbz: ykt" -H "Content-Type: application/json" \
  -d '{"cards_problem_id": 123, "result": "A", "classroom_id": "30112085"}'
# → {"errcode": 0, "data": {"correct": false, "score": 0, "answer": "D", ...}}
```

### 关键发现

1. **submit_answer 等都是摆设** — `view_depth` 和 `view_problem` 是真实存在的 GET API（查看题目），但 POST 版全是占位。

2. **API 直接返回正确答案** — 无论提交什么答案，响应里的 `data.answer` 就是正确答案。

3. **不校验答题次数** — 尽管页面可能用 `prob.user.count` 限制提交次数，但后端对 `problem_result` 不做次数校验，可以反复提交。

4. **card_id 即 leaf_type_id** — 通过 `leaf_info` API 获取的 `leaf_type_id` 就是 `cards_id`。

## 技术环境

| 组件 | 版本/路径 |
|------|-----------|
| Chrome Headless | Google Chrome for Testing 147 |
| CDP 库 | chrome-remote-interface (npm) |
| Playwright | 1.59.1 |
| Python | 3.12+ |
| 雨课堂后端 | Vue 3 + Element UI + Axios |

## 相关 API

### 获取卡片详情

```
GET /v2/api/web/cards/detlist/{cards_id}?classroom_id={classroom_id}
```

响应包含:
- `problem_results[]` — 题目列表（每题有 id, type, option, problem 等）
- `Slides[]` — PPT 幻灯片内容
- `studentProblemStatus` — 当前得分/状态

### 获取作业信息

```
GET /mooc-api/v1/lms/learn/leaf_info/{classroom_id}/{leaf_id}/?classroom_id={classroom_id}
```

响应包含:
- `leaf_type_id` — 即 cards_id（卡片模式专用）
- `score_deadline` — 截止时间戳
- `is_assessed` — 是否已批改

### 获取课程章节

```
GET /mooc-api/v1/lms/learn/course/chapter?cid={classroom_id}&sign={university_id}&classroom_id={classroom_id}
```

用于发现当前账号下所有章节和未完成作业的 leaf_id。

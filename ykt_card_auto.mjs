#!/usr/bin/env node
/**
 * YKT Card Auto — Rain Classroom PPT Card Homework Auto-Answer Tool
 *
 * Usage:
 *   node ykt_card_auto.mjs \
 *     --sessionid "xxx" --csrftoken "xxx" \
 *     --classroom_id "30112085" --cards_id "6995005" \
 *     --auto-answer
 *
 *   node ykt_card_auto.mjs \
 *     --sessionid "xxx" --csrftoken "xxx" \
 *     --classroom_id "30112085" --cards_id "6995005" \
 *     --answers '{"1":"A","2":"BC","3":"D"}'
 *
 *   node ykt_card_auto.mjs \
 *     --sessionid "xxx" --csrftoken "xxx" \
 *     --classroom_id "30112085" --cards_id "6995005" \
 *     --list-only
 */

const BASE = 'https://www.yuketang.cn/v2/api/web/cards';

function parseArgs() {
  const args = {};
  for (let i = 2; i < process.argv.length; i++) {
    if (process.argv[i].startsWith('--')) {
      const key = process.argv[i].replace(/^--/, '');
      const next = process.argv[i + 1];
      if (next && !next.startsWith('--')) {
        args[key] = next;
        i++;
      } else {
        args[key] = true;
      }
    }
  }
  return args;
}

function makeHeaders(sessionid, csrftoken) {
  return {
    'Cookie': `sessionid=${sessionid}; csrftoken=${csrftoken}`,
    'xtbz': 'ykt',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  };
}

async function getProblemIds(sessionid, csrftoken, cardsId, classroomId) {
  const r = await fetch(
    `${BASE}/detlist/${cardsId}?classroom_id=${classroomId}`,
    { headers: makeHeaders(sessionid, csrftoken) }
  );
  const data = await r.json();
  if (data.errcode !== 0) {
    throw new Error(`获取题目列表失败: ${data.errmsg || '未知错误'}`);
  }
  return data.data.problem_results.map(p => p.id);
}

async function submitAnswer(sessionid, csrftoken, pid, result, classroomId) {
  const r = await fetch(`${BASE}/problem_result`, {
    method: 'POST',
    headers: makeHeaders(sessionid, csrftoken),
    body: JSON.stringify({
      cards_problem_id: pid,
      result,
      classroom_id: classroomId,
    }),
  });
  return await r.json();
}

async function autoAnswer(sessionid, csrftoken, pid, classroomId, index, total) {
  const res = await submitAnswer(sessionid, csrftoken, pid, 'A', classroomId);

  if (res.errcode !== 0) {
    console.log(`  [${String(index).padStart(2)}/${total}] ❌ id=${pid}: ${res.errmsg}`);
    return null;
  }

  if (res.data?.correct === true) {
    console.log(`  [${String(index).padStart(2)}/${total}] ✅ id=${pid} 答案=A (一击命中)`);
    return 'A';
  }

  const answer = res.data?.answer;
  if (answer) {
    const clean = String(answer).trim();
    if (clean.toUpperCase() !== 'A') {
      const res2 = await submitAnswer(sessionid, csrftoken, pid, clean, classroomId);
      if (res2.data?.correct === true) {
        console.log(`  [${String(index).padStart(2)}/${total}] ✅ id=${pid} 答案=${clean}`);
      } else {
        console.log(`  [${String(index).padStart(2)}/${total}] ⚠️ id=${pid} 答案=${clean} 但修正后仍不正确`);
      }
    }
    return clean;
  }

  console.log(`  [${String(index).padStart(2)}/${total}] ❌ id=${pid}: 未获取到正确答案`);
  return null;
}

async function main() {
  const args = parseArgs();

  if (!args.sessionid || !args.csrftoken || !args.classroom_id || !args.cards_id) {
    console.error('用法: node ykt_card_auto.mjs \\');
    console.error('  --sessionid "xxx" --csrftoken "xxx" \\');
    console.error('  --classroom_id "30112085" --cards_id "6995005" \\');
    console.error('  --auto-answer 或 --answers \'{"1":"A"}\' 或 --list-only');
    process.exit(1);
  }

  if (!args['auto-answer'] && !args.answers && !args['list-only']) {
    console.error('请提供 --auto-answer 或 --answers 或 --list-only');
    process.exit(1);
  }

  const { sessionid, csrftoken, classroom_id, cards_id } = args;

  try {
    const problemIds = await getProblemIds(sessionid, csrftoken, cards_id, classroom_id);
    console.log(`📚 共 ${problemIds.length} 道题\n`);

    if (args['list-only']) {
      problemIds.forEach((id, i) => console.log(`  [${String(i + 1).padStart(2)}] id=${id}`));
      return;
    }

    if (args.answers) {
      const answers = JSON.parse(args.answers);
      console.log('📋 使用预设答案提交:\n');
      for (const [idxStr, ans] of Object.entries(answers).sort((a, b) => +a[0] - +b[0])) {
        const idx = parseInt(idxStr) - 1;
        if (idx < 0 || idx >= problemIds.length) {
          console.log(`  [${idxStr.padStart(2)}] ⚠️ 索引越界`);
          continue;
        }
        const res = await submitAnswer(sessionid, csrftoken, problemIds[idx], ans, classroom_id);
        const correct = res.data?.correct;
        console.log(`  [${idxStr.padStart(2)}] ${correct ? '✅' : '❌'} id=${problemIds[idx]} ans=${ans}`);
      }
    }

    if (args['auto-answer']) {
      console.log('🤖 自动探测答案模式:\n');
      const results = [];
      for (let i = 0; i < problemIds.length; i++) {
        const answer = await autoAnswer(sessionid, csrftoken, problemIds[i], classroom_id, i + 1, problemIds.length);
        results.push({ index: i + 1, pid: problemIds[i], answer });
      }

      console.log('\n===== 结果汇总 =====');
      results.forEach(r => {
        console.log(`  [${String(r.index).padStart(2)}] id=${r.pid} 答案=${r.answer || '❓'}`);
      });
      console.log(`\n✅ 完成! ${results.length} 题`);
    }
  } catch (e) {
    console.error(`❌ ${e.message}`);
    process.exit(1);
  }
}

main();

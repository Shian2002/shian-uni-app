# WorkBuddy 执行交接：Codex 卡顿维护

## 任务目标

用户感觉 Codex 变卡。已经用 `$keep-codex-fast` 做过只读体检，主要问题是 Codex Desktop 的线程列表元数据膨胀，尤其是 `threads.title` 和 `threads.first_user_message` 存了超长内容，导致线程列表、切换、恢复变慢。

请按本文执行维护。重点是：**先确认 Codex 已退出，再执行 apply；如果仍检测到 Codex running，不能说维护成功。**

## 当前已知报告

最近一次只读报告结果：

```text
thread_active_rows 26
thread_title_chars 106783
thread_first_user_message_chars 108552
thread_max_title_chars 64914
thread_max_first_user_message_chars 64914
thread_titles_over_limit 2
thread_first_user_message_over_limit 7
thread_first_user_message_over_10k 2
thread_metadata_repair_candidates 7
logs_mb 584.6
size_sessions_gb 0.427
size_archived_sessions_gb 0.603
old_session_candidates 0
config_prune_candidates 0
worktree_candidates 0
extended_paths 0
```

主要要修：

- `thread_title_chars`
- `thread_first_user_message_chars`
- `thread_max_title_chars`
- `thread_max_first_user_message_chars`
- `thread_metadata_repair_candidates`

## 上一次为什么失败

用户已经运行过：

```bash
/tmp/keep-codex-fast-after-exit.sh
```

但日志显示：

```text
apply_skipped_codex_running
blocking_process codex_process_001
blocking_process codex_process_002
blocking_process codex_process_003
blocking_process codex_process_004
blocking_process codex_process_005
blocking_process codex_process_006
```

所以那一次只是报告模式，没有真正维护成功。

## 执行前要求

1. 让用户退出 Codex Desktop。
2. 确认没有 Codex 进程还在写本地数据库。
3. 不要删除聊天、日志、worktree、memory、skill、plugin。
4. 必须先备份，维护脚本会自动备份。
5. 维护成功前不要让用户以为已经处理好了。

## 推荐执行方式

如果 `/tmp/keep-codex-fast-after-exit.sh` 还在，可以直接使用它。它已经被改成：如果检测到 Codex 仍在运行，会等待 15 秒继续重试。

```bash
/tmp/keep-codex-fast-after-exit.sh
```

如果脚本不存在，重建脚本：

```bash
cat > /tmp/keep-codex-fast-after-exit.sh <<'SH'
#!/bin/zsh
set -eu

LOG="/tmp/keep-codex-fast-after-exit-$(date +%Y%m%d%H%M%S).log"
MARKER="/tmp/keep-codex-fast-after-exit.latest"
echo "$LOG" > "$MARKER"

{
  echo "started_at=$(date)"
  echo "mode=retry_apply_until_codex_not_running"

  ATTEMPT=0
  while true; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "apply_attempt=$ATTEMPT at=$(date)"
    TMP_OUT="/tmp/keep-codex-fast-apply-attempt-$$.log"
    python3 /Users/junj/.codex/skills/keep-codex-fast/scripts/keep_codex_fast.py \
      --apply \
      --repair-thread-metadata-bloat \
      --archive-older-than-days 10 \
      --worktree-older-than-days 7 \
      --rotate-logs-above-mb 512 \
      > "$TMP_OUT" 2>&1 || true
    cat "$TMP_OUT"
    if ! grep -q "apply_skipped_codex_running" "$TMP_OUT"; then
      rm -f "$TMP_OUT"
      break
    fi
    rm -f "$TMP_OUT"
    echo "codex_still_running_waiting_at=$(date)"
    sleep 15
  done

  echo "verify_after_apply_at=$(date)"
  python3 /Users/junj/.codex/skills/keep-codex-fast/scripts/keep_codex_fast.py
  echo "finished_at=$(date)"
} >> "$LOG" 2>&1
SH

chmod +x /tmp/keep-codex-fast-after-exit.sh
/tmp/keep-codex-fast-after-exit.sh
```

## 如果一直显示 Codex 仍在运行

先查看进程：

```bash
pgrep -fl "Codex|codex"
```

如果用户确认 Codex Desktop 已退出，但仍有残留进程，可以结束 Codex 相关进程：

```bash
pkill -f "/Applications/Codex.app"
```

然后重新运行：

```bash
/tmp/keep-codex-fast-after-exit.sh
```

## 验证维护结果

查看最新日志路径：

```bash
cat /tmp/keep-codex-fast-after-exit.latest
```

查看日志：

```bash
cat "$(cat /tmp/keep-codex-fast-after-exit.latest)"
```

成功标准：

1. 日志中不应再出现：

```text
apply_skipped_codex_running
```

2. 日志中应有 apply 相关输出和备份路径。
3. `verify_after_apply_at` 后面的只读报告中，以下数值应明显下降：

```text
thread_title_chars
thread_first_user_message_chars
thread_max_title_chars
thread_max_first_user_message_chars
thread_metadata_repair_candidates
```

理想情况：

- `thread_metadata_repair_candidates` 接近 0。
- 最大标题长度从约 64914 降到 120 左右。
- 最大预览长度从约 64914 降到 240 左右。

## 补充：Git 已升级

本机旧 Git 是：

```text
/usr/local/bin/git
git version 2.15.0
```

已经用 Homebrew 安装新版，当前应为：

```bash
git --version
which git
git branch --show-current
```

期望：

```text
git version 2.54.0
/opt/homebrew/bin/git
```

## 不要做的事

- 不要永久删除 Codex 聊天记录。
- 不要手动改 SQLite，优先用脚本。
- 不要在 Codex 仍运行时强行写库。
- 不要把备份目录上传或公开，因为里面可能有本地私有元数据。
- 不要把 “report mode” 误认为维护成功。


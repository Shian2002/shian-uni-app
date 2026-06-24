#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

timestamp="${IP_EVIDENCE_TIMESTAMP:-$(date +%Y%m%d-%H%M%S)}"
out_dir="artifacts/ip-evidence/${timestamp}"
mkdir -p "$out_dir"

meta_file="${out_dir}/evidence-metadata.txt"
file_list="${out_dir}/tracked-files.txt"
archive_file_list="${out_dir}/archived-files.txt"
archive_file_list_nul="${out_dir}/archived-files.nul"
archive_file="${out_dir}/xuan-cet-tai-source-${timestamp}.tar.gz"

{
  echo "项目：时安解忧屋 / xuan-cet-tai"
  echo "导出时间：$(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "工作目录：$ROOT_DIR"
  echo
  echo "当前提交："
  git rev-parse HEAD
  echo
  echo "当前分支："
  git branch --show-current || true
  echo
  echo "最近 20 条提交："
  git log --oneline --decorate -20
  echo
  echo "作者统计："
  git shortlog -sne --all
  echo
  echo "工作区状态："
  git status --short
} > "$meta_file"

git ls-files > "$file_list"
git ls-files -z --cached --others --exclude-standard -- \
  README.md AGENTS.md AUTHORS.md COPYRIGHT.md NOTICE.md \
  package.json package-lock.json vite.config.js index.html \
  deploy-h5-to-server.sh deploy-to-server.sh deploy-to-staging.sh rollback-h5-on-server.sh \
  start-dev.sh start-h5-preview.sh start-macos-dev.sh start-macos.sh \
  src backend database docs scripts configs desktop android-shell \
  > "$archive_file_list_nul"
tr '\0' '\n' < "$archive_file_list_nul" > "$archive_file_list"

tar --null -czf "$archive_file" -T "$archive_file_list_nul"

shasum -a 256 "$archive_file" "$meta_file" "$file_list" "$archive_file_list" > "${out_dir}/SHA256SUMS.txt"

echo "已生成知识产权证据包：${out_dir}"
echo "源码压缩包：${archive_file}"
echo "元数据：${meta_file}"
echo "归档清单：${archive_file_list}"
echo "校验文件：${out_dir}/SHA256SUMS.txt"

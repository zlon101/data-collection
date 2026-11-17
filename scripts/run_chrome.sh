#!/usr/bin/env bash
# 启动带 CDP 远程调试的 Chrome，供 BrowserManager(mode=connect) / scrape_agent 使用。
# 从仓库根目录执行: ./scripts/run_chrome.sh
#
# 端口读取顺序: 环境变量 PORT > .env 的 CDP_URL > .env.example 的 CDP_URL > 9222
# 其它可选环境变量: CHROME_PATH、PROFILE_DIR

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_DIR="${PROFILE_DIR:-$PROJECT_ROOT/local_data/chrome-cdp-profile}"

port_from_env_file() {
  local file="$1"
  [[ -f "$file" ]] || return 1
  local env_url
  env_url="$(grep -E '^[[:space:]]*CDP_URL=' "$file" | tail -1 | cut -d= -f2- | tr -d '[:space:]' | tr -d '\"' | tr -d "'")"
  [[ -n "$env_url" ]] || return 1
  if [[ "$env_url" =~ :([0-9]+)(/|$) ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

if [[ -z "${PORT:-}" ]]; then
  PORT="$(port_from_env_file "$PROJECT_ROOT/.env" || port_from_env_file "$PROJECT_ROOT/.env.example" || true)"
fi
PORT="${PORT:-9222}"

if [[ -n "${CHROME_PATH:-}" ]]; then
  :
elif [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]; then
  CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif [[ -x "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev" ]]; then
  CHROME_PATH="/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev"
else
  echo "未找到 Chrome，请设置 CHROME_PATH。"
  exit 1
fi

mkdir -p "$PROFILE_DIR"

echo "启动 Chrome: $CHROME_PATH"
echo "CDP: http://localhost:$PORT"
echo "Profile: $PROFILE_DIR"

exec "$CHROME_PATH" \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins="*" \
  --user-data-dir="$PROFILE_DIR" \
  --no-first-run \
  --no-default-browser-check

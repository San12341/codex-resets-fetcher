#!/usr/bin/env python3
"""
Codex Resets 数据获取脚本
========================
通过纯网络请求（无浏览器自动化 / 无 Selenium / 无 Playwright）直接调用
codex-resets.com 的 JSON API 获取 Codex 重置信息。

数据来源：https://codex-resets.com/api/resets （公开 GET 接口，无需认证）

用法：
    python3 codex_resets_fetcher.py                  # 概览：最新重置 + 统计 + 当前预测
    python3 codex_resets_fetcher.py --latest 5       # 最近 5 条重置记录
    python3 codex_resets_fetcher.py --all            # 全部重置记录
    python3 codex_resets_fetcher.py --type regular   # 仅 regular 类型
    python3 codex_resets_fetcher.py --type banked    # 仅 banked 类型
    python3 codex_resets_fetcher.py --watch          # 仅当前重置预测/观察
    python3 codex_resets_fetcher.py --stats          # 仅统计数据
    python3 codex_resets_fetcher.py --json           # 输出原始 JSON
    python3 codex_resets_fetcher.py --json --out data.json   # 保存到文件
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

API_URL = "https://codex-resets.com/api/resets"
DEFAULT_TIMEOUT = 15  # 秒
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# 网络层：纯 urllib，零第三方依赖
# ---------------------------------------------------------------------------
def fetch_resets(timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """请求 /api/resets 并返回解析后的 JSON 字典。"""
    req = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Referer": "https://codex-resets.com/",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise SystemExit(f"[错误] HTTP {e.code}: {e.reason} — {API_URL}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"[错误] 网络请求失败: {e.reason} — {API_URL}") from e
    except TimeoutError:
        raise SystemExit(f"[错误] 请求超时（{timeout}s）— {API_URL}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(f"[错误] 返回内容不是合法 JSON: {e}") from e

    if not isinstance(data, dict) or "events" not in data:
        raise SystemExit("[错误] API 返回结构异常，缺少 'events' 字段")

    return data


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def parse_iso(ts: str | None) -> datetime | None:
    """解析 ISO 8601 时间字符串为带时区的 datetime。"""
    if not ts:
        return None
    try:
        # 兼容 Z 后缀
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_dt(ts: str | None, tz: timezone = timezone.utc) -> str:
    """格式化时间为可读字符串。"""
    dt = parse_iso(ts)
    if dt is None:
        return "未知"
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M %Z")


def fmt_relative(ts: str | None) -> str:
    """返回相对时间描述，如 '2 天前'。"""
    dt = parse_iso(ts)
    if dt is None:
        return "未知"
    now = datetime.now(timezone.utc)
    delta = now - dt
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes = rem // 60
    if days > 0:
        return f"{days} 天前"
    if hours > 0:
        return f"{hours} 小时前"
    if minutes > 0:
        return f"{minutes} 分钟前"
    return "刚刚"


def truncate(text: str, max_len: int = 80) -> str:
    """截断长文本，去除换行。"""
    one_line = " ".join(text.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"


# ---------------------------------------------------------------------------
# 渲染函数
# ---------------------------------------------------------------------------
def render_stats(stats: dict[str, Any]) -> str:
    lines = [
        "=== 统计信息 ===",
        f"  总重置次数     : {stats.get('total', 'N/A')}",
        f"  最近一次重置   : {fmt_dt(stats.get('last_reset_at'))} ({fmt_relative(stats.get('last_reset_at'))})",
        f"  距今天数       : {stats.get('days_since_last', 'N/A')} 天",
        f"  平均间隔       : {stats.get('avg_interval_days', 'N/A')} 天",
    ]
    return "\n".join(lines)


def render_watch(watch: dict[str, Any] | None) -> str:
    if not watch:
        return "=== 当前重置预测 ===\n  暂无活跃观察"
    lines = [
        "=== 当前重置预测（Reset Watch） ===",
        f"  级别           : {watch.get('level', 'N/A')}",
        f"  重置概率       : {watch.get('reset_chance', 'N/A')}%",
        f"  预测窗口       : {watch.get('forecast_window', 'N/A')}",
        f"  过期时间       : {fmt_dt(watch.get('expires_at'))}",
        f"  观察推文       : {watch.get('tweet_url', 'N/A')}",
        f"  推文内容       : {truncate(watch.get('text', ''), 120)}",
    ]
    hints = watch.get("episode_hints") or []
    if hints:
        lines.append(f"  相关线索 ({len(hints)} 条):")
        for i, h in enumerate(hints, 1):
            lines.append(
                f"    [{i}] {fmt_dt(h.get('observed_at'))} — "
                f"{truncate(h.get('text', ''), 100)}"
            )
    return "\n".join(lines)


def render_events(events: list[dict[str, Any]], title: str = "重置记录") -> str:
    if not events:
        return f"=== {title} ===\n  无记录"
    lines = [f"=== {title}（共 {len(events)} 条）==="]
    for i, ev in enumerate(events, 1):
        rtype = ev.get("reset_type", "?")
        source = ev.get("source", "?")
        lines.append(
            f"\n  [{i}] {fmt_dt(ev.get('announced_at'))}  "
            f"[{rtype}/{source}]  ({fmt_relative(ev.get('announced_at'))})"
        )
        lines.append(f"      推文: {ev.get('tweet_url', 'N/A')}")
        lines.append(f"      内容: {truncate(ev.get('text', ''), 120)}")
    return "\n".join(lines)


def render_overview(data: dict[str, Any]) -> str:
    """默认概览：统计 + 最新重置 + 当前预测。"""
    parts: list[str] = []

    # 统计
    stats = data.get("stats", {})
    if stats:
        parts.append(render_stats(stats))

    # 最新一条
    events = data.get("events", [])
    if events:
        parts.append(render_events(events[:1], "最新一次重置"))

    # 当前预测
    watch = data.get("watch")
    if watch:
        parts.append(render_watch(watch))

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="通过纯网络请求获取 codex-resets.com 的 Codex 重置信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--all", action="store_true", help="显示全部重置记录")
    parser.add_argument("--latest", type=int, metavar="N", help="显示最近 N 条重置记录")
    parser.add_argument(
        "--type",
        choices=["regular", "banked"],
        dest="reset_type",
        help="按重置类型筛选",
    )
    parser.add_argument("--watch", action="store_true", help="仅显示当前重置预测")
    parser.add_argument("--stats", action="store_true", help="仅显示统计数据")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")
    parser.add_argument("--out", metavar="FILE", help="将 JSON 输出保存到文件（配合 --json）")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"请求超时秒数（默认 {DEFAULT_TIMEOUT}）")
    args = parser.parse_args()

    # 1. 拉取数据
    data = fetch_resets(timeout=args.timeout)
    events = data.get("events", [])

    # 2. 按类型筛选
    if args.reset_type:
        events = [e for e in events if e.get("reset_type") == args.reset_type]

    # 3. 输出
    if args.json:
        payload = data
        # 如果指定了筛选，只输出筛选后的 events
        if args.reset_type or args.latest:
            filtered = events[: args.latest] if args.latest else events
            payload = {**data, "events": filtered}
        json_str = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"[OK] 已保存 {len(payload.get('events', []))} 条记录到 {args.out}")
        else:
            print(json_str)
        return

    if args.watch:
        print(render_watch(data.get("watch")))
        return

    if args.stats:
        print(render_stats(data.get("stats", {})))
        return

    if args.all:
        print(render_events(events, "全部重置记录"))
        return

    if args.latest:
        print(render_events(events[: args.latest], f"最近 {args.latest} 条重置记录"))
        return

    # 默认：概览
    print(render_overview(data))


if __name__ == "__main__":
    main()

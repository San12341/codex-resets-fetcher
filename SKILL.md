---
name: codex-resets-fetcher
description: "通过纯网络请求（无浏览器自动化）直接获取 codex-resets.com 的 Codex 重置信息，包括历史重置记录、当前重置预测和统计数据。当用户询问 Codex 重置、重置记录、重置历史、最近一次重置、重置预测、重置概率、codex-resets、reset tracker、OpenAI/ChatGPT Codex 额度重置时间等相关问题时使用。"
---

# Codex Resets Fetcher

通过公开 JSON API 直接获取 Codex 重置数据，零第三方依赖、零自动化手段。

## 数据来源

- **API**：`GET https://codex-resets.com/api/resets`（公开接口，无需认证）
- **网站渲染方式**：SSR + 客户端 JSON API 混合；动态数据全部由该 API 提供

## 快速使用

运行内置脚本获取数据：

```bash
python3 scripts/fetch_codex_resets.py [选项]
```

常用选项：

| 命令 | 用途 |
|---|---|
| `（无参数）` | 概览：统计 + 最新重置 + 当前预测 |
| `--latest N` | 最近 N 条重置记录 |
| `--all` | 全部重置记录 |
| `--type regular` / `--type banked` | 按重置类型筛选 |
| `--watch` | 仅当前重置预测 |
| `--stats` | 仅统计数据 |
| `--json` | 输出原始 JSON（供程序处理） |
| `--json --out FILE` | 保存 JSON 到文件 |

## API 返回结构

脚本返回的 JSON 包含三个顶层字段：

### `events` — 重置历史列表（按时间倒序）

每条事件字段：

| 字段 | 说明 |
|---|---|
| `tweet_id` | 来源推文 ID |
| `tweet_url` | 推文链接（x.com/thsottiaux） |
| `text` | 推文原文 |
| `announced_at` | ISO 8601 时间戳（UTC） |
| `reset_type` | `regular`（普通重置）或 `banked`（存入银行的重置额度） |
| `source` | `webhook` / `observed` / `backfill` |

### `watch` — 当前重置预测（可能为 null）

| 字段 | 说明 |
|---|---|
| `level` | 观察级别（如 `elevated`） |
| `reset_chance` | 重置概率百分比 |
| `forecast_window` | 预测窗口描述 |
| `expires_at` | 预测过期时间 |
| `episode_hints` | 相关推文线索列表 |

### `stats` — 统计数据

| 字段 | 说明 |
|---|---|
| `total` | 历史总重置次数 |
| `last_reset_at` | 最近一次重置时间 |
| `days_since_last` | 距今天数 |
| `avg_interval_days` | 平均重置间隔（天） |

## 回答指引

- 用户问"最近一次重置"→ 用 `--latest 1` 或直接读 `stats.last_reset_at` + `events[0]`
- 用户问"什么时候会再重置"→ 用 `--watch` 输出预测概率和窗口；若无活跃 watch，说明当前无预测
- 用户问"历史统计/频率"→ 用 `--stats`，必要时结合 `--all` 计算月度分布
- 需要程序化处理或导出 → 用 `--json --out` 保存后再分析
- 时间默认 UTC，回答时按需换算为用户本地时区（UTC+8）

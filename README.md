# Codex Resets Fetcher

通过纯网络请求（无浏览器自动化、零第三方依赖）直接获取 [codex-resets.com](https://codex-resets.com) 的 Codex 重置信息，包括历史重置记录、当前重置预测和统计数据。

## 特性

- **零依赖**：仅使用 Python 标准库 `urllib`，无需 `pip install`
- **纯 API 直连**：直接调用公开 JSON 接口，不使用 Selenium / Playwright 等自动化手段
- **数据完整**：覆盖全部历史重置记录、实时重置预测、统计指标
- **多输出格式**：支持人类可读概览、按条件筛选、原始 JSON 导出

## 数据来源

公开 API 端点：`GET https://codex-resets.com/api/resets`

无需认证，返回三个字段：

| 字段 | 说明 |
|---|---|
| `events` | 全部重置事件（按时间倒序），含推文 ID、链接、原文、时间、类型、来源 |
| `watch` | 当前重置预测（概率、预测窗口、相关推文线索），无活跃预测时为 `null` |
| `stats` | 统计数据（总次数、最近重置时间、距今天数、平均间隔） |

重置类型：`regular`（普通重置）/ `banked`（存入银行的重置额度）

## 快速开始

```bash
# 概览：统计 + 最新重置 + 当前预测
python3 scripts/fetch_codex_resets.py

# 最近 5 条重置记录
python3 scripts/fetch_codex_resets.py --latest 5

# 全部重置记录
python3 scripts/fetch_codex_resets.py --all

# 仅 banked 类型
python3 scripts/fetch_codex_resets.py --type banked

# 仅当前重置预测
python3 scripts/fetch_codex_resets.py --watch

# 仅统计数据
python3 scripts/fetch_codex_resets.py --stats

# 导出原始 JSON
python3 scripts/fetch_codex_resets.py --json

# 保存 JSON 到文件
python3 scripts/fetch_codex_resets.py --json --out resets.json
```

## 命令选项

| 选项 | 说明 |
|---|---|
| `--latest N` | 显示最近 N 条重置记录 |
| `--all` | 显示全部重置记录 |
| `--type {regular,banked}` | 按重置类型筛选 |
| `--watch` | 仅显示当前重置预测 |
| `--stats` | 仅显示统计数据 |
| `--json` | 输出原始 JSON |
| `--out FILE` | 将 JSON 保存到文件（配合 `--json`） |
| `--timeout SEC` | 请求超时秒数（默认 15） |

## 项目结构

```
codex-resets-fetcher/
├── README.md
├── SKILL.md                          # Agent Skill 描述（可选，用于 AI 助手自动调用）
└── scripts/
    └── fetch_codex_resets.py         # 主脚本
```

## 技术实现

网站采用 SSR + 客户端 JSON API 混合架构：重置历史日历数据内嵌于 HTML `data-*` 属性，动态数据（最新重置、统计、预测）由 `/api/resets` 提供。本脚本直接调用该 API，跳过页面渲染层。

## 免责声明

数据来源于 codex-resets.com 对 @thsottiaux 推文的公开追踪。本工具仅做数据获取与展示，重置的最终解释权归 OpenAI 所有。

## License

MIT

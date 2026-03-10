<p align="center">
  <h1 align="center">🇨🇳 SWCC</h1>
  <p align="center"><b>Socialism With Chinese Characteristics — SW Claude Code</b></p>
  <p align="center">民主集中制多智能体编排 Claude Code 插件</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/agents-9_specialized-red" alt="Agents">
  <img src="https://img.shields.io/badge/skills-5_workflows-yellow" alt="Skills">
  <img src="https://img.shields.io/badge/python-not_needed-green" alt="No Python">
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen" alt="Zero deps">
  <img src="https://img.shields.io/badge/Claude_Code-plugin-blue" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="MIT">
</p>

---

> **美国人用三权分立编排 AI，中国古人用三省六部编排 AI，我们用什么？**
>
> 1949 年之后的答案：**民主集中制**。
>
> 先让左派和右派吵，吵完党委拍板，国务院拆活儿，部委干活儿，纪委验收。
>
> 一个编码任务，走完一整套中国特色社会主义政治流程。

## 为什么是民主集中制？

大多数 Multi-Agent 框架的思路是：让 Agent 自由协作，出了问题再修。

这就像没有制度的团队——要么一团和气（所有 Agent 都同意，没人提反对意见），要么各说各的（Agent 之间矛盾无人裁决）。

民主集中制的解法：**先强制对立，再集中拍板**。左派和右派必须提出不同方案，暴露盲区；党委综合裁决，一锤定音；部委坚决执行，纪委铁面验收。

| | SWCC 🇨🇳 | directive 🇺🇸 | edict 🏯 |
|---|:---:|:---:|:---:|
| **灵感来源** | 中国特色社会主义 | 美国宪政 | 三省六部 |
| **运行方式** | ✅ Claude Code 插件，装上即用 | 独立应用，需 Docker | 独立应用，需 Docker + OpenClaw |
| **决策机制** | 民主集中制 | 三权制衡 | 层级审批 |
| **强制对立** | ✅ 左右必须提出不同方案 | ❌ | ❌ |
| **动态流程** | ✅ 按规模自动调节协商深度 | ❌ 固定流程 | ❌ 固定流程 |
| **冲突裁决** | 党委综合裁决 | 最高法院仲裁 | 门下省封驳 |
| **代码执行** | ✅ 部委执行 | ✅ DoD 执行 | ✅ 兵部执行 |
| **按需调研** | ✅ 智库四重身份（社科院/发改委/工程院/审计署） | ❌ | ❌ |
| **代码验收** | ✅ 纪委 Review + 测试 | ✅ Senate + DoJ 审查 | ⚠️ 门下省审计划 |
| **紧急通道** | ✅ 举国体制 | ❌ | ❌ |

## 30 秒体验

```bash
# 安装
claude plugins marketplace add ylxmf2005/swcc
claude plugins install swcc

# 在任意项目中
/zhili 给这个项目加 JWT 认证
```

坐好，看戏。中办会先分拣任务，然后左右派开始辩论，党委拍板，部委干活，纪委验收。

## 🏛️ 架构：谁是谁

```
                          ┌─────────┐
                    ┌─────│  用户    │─────┐
                    │     └─────────┘     │
                    ▼                     │
              ┌──────────┐                │
              │ 📋 中办   │ 收文分拣        │ 交付
              │ zhongban │ 判定：小/中/大   │
              └────┬─────┘                │
         ┌─────────┼─────────┐  政协协商  │       ┌ ─ ─ ─ ─ ─ ─ ─ ─ ┐
         ▼         ▼         ▼            │         📚 智库  zhiku
    ┌─────────┐┌─────────┐┌─────────┐     │       │    按需调研        │
    │ 🔴 左派  ││ 🔵 右派  ││ 🟡 中间  │     │
    │ zuopai  ││ youpai  ││zhongjian│     │       │ 🔬社科院  📊发改委  │
    │ 大破大立 ││ 稳中求进 ││ 实事求是 │     │         🔧工程院  🔍审计署
    └────┬────┘└────┬────┘└────┬────┘     │       │                   │
         └──────────┼──────────┘          │        任意 agent 可随时调用
                    ▼                     │       └ ─ ─ ─ ─ ─ ─ ─ ─ ┘
              ┌──────────┐                │
              │ ⭐ 党委   │ 集中决策        │
              │ dangwei  │ 最终裁决        │
              └────┬─────┘                │
                   ▼                      │
              ┌──────────┐                │
              │ 🏢 国务院 │ 拆分子任务      │
              │guowuyuan │ 分析依赖        │
              └────┬─────┘                │
          ┌────────┼────────┐             │
          ▼        ▼        ▼             │
       ┌──────┐┌──────┐┌──────┐           │
       │ 部委1 ││ 部委2 ││ 部委3 │ 并行执行  │
       │buwei ││buwei ││buwei │           │
       └──┬───┘└──┬───┘└──┬───┘           │
          └────────┼────────┘             │
                   ▼                      │
              ┌──────────┐                │
              │ 🔍 纪委   │ 代码审查        │
              │  jiwei   │ + 跑测试        │
              └────┬─────┘                │
                   │ 通过? ─── 否 → 驳回重做
                   │
                   ▼────────────────────→─┘
```

## 🎭 九大员：每个 Agent 都有灵魂

| Agent | 角色 | 信条 | 模型 |
|-------|------|------|------|
| 📋 zhongban (中办) | 收文分拣 | "宁大勿小，多协商总比少协商好" | opus |
| 🔴 zuopai (政协左派) | 激进革新 | "推倒重来！旧代码就该删掉重写！" | opus |
| 🔵 youpai (政协右派) | 保守稳健 | "能修补绝不重写，能复用绝不新建" | opus |
| 🟡 zhongjian (政协中间) | 折中调和 | "实践是检验真理的唯一标准" | opus |
| ⭐ dangwei (党委) | 最终裁决 | "批评左倾冒险主义，纠正右倾保守主义" | opus |
| 🏢 guowuyuan (国务院) | 拆分调度 | "党委决策不可更改，我只负责拆分" | opus |
| 🔧 buwei (部委) | 代码执行 | "令行禁止——不多做，不少做" | opus |
| 🔍 jiwei (纪委) | 监察验收 | "铁面无私，信任但验证" | opus |
| 📚 zhiku (智库) | 按需调研 | "没有调查就没有发言权" | opus |

> 💡 **智库**不在主流程中，而是被其他 agent 按需调用。它有四重身份：**社科院**（战略调研）、**发改委**（可行性分析）、**工程院**（实操参考）、**审计署**（合规标准），根据调用方的需求自动切换。

## 📊 动态协商深度

中办会根据任务复杂度自动决定协商深度。你也可以用 `--scale` 覆盖：

```
/zhili --scale 小 fix typo in README        → 跳过协商，直接执行
/zhili add input validation                  → 中办自动判定
/zhili --scale 大 redesign the auth system   → 强制三方协商
```

| 规模 | 协商深度 | 判定标准 |
|------|---------|---------|
| 小 | 跳过协商 | <3 文件，简单改动 |
| 中 | 🔴左派 vs 🔵右派 | 3-8 文件，中等复杂度 |
| 大 | 🔴左派 vs 🔵右派 → 🟡中间路线折中 | >8 文件或架构级变更 |

## ⚡ 举国体制 (`/juguo`)

当任务紧急到没时间开会：

```
/juguo 紧急修复认证漏洞
```

> 跳过中办。跳过政协。跳过党委。国务院直接拆活，全部委同时开干，纪委只跑自动化。
>
> 集中力量办大事。

## 🛠️ 五大技能

| 技能 | 说明 | 用法 |
|------|------|------|
| `/zhili` | **全流程一条龙** — 从协商到交付 | `/zhili [--scale 小\|中\|大] 任务描述` |
| `/xieshang` | **只看方案** — 产出计划不动代码 | `/xieshang 任务描述` |
| `/zhixing` | **直接执行** — 跳过讨论 | `/zhixing [方案]` |
| `/jicha` | **纪委审查** — review 当前变更 | `/jicha [关注点]` |
| `/juguo` | **举国体制** — 全力冲刺 | `/juguo 任务描述` |

## 📦 安装

```bash
# 方式一：从 GitHub 安装
claude plugins marketplace add ylxmf2005/swcc
claude plugins install swcc

# 方式二：本地安装
git clone https://github.com/ylxmf2005/swcc.git
claude plugins install --path ./swcc
```

零依赖。不需要 Python，不需要 Docker，不需要 OpenClaw。装上就用。

## 📁 产物

每次运行按日期+任务关键词创建独立目录，完整可追溯：

```
.tmp/swcc/
└── 2026-03-10-add-user-auth/     # 日期-任务slug
    ├── zhongban-report.md        # 📋 中办分拣报告
    ├── zuopai-proposal.md        # 🔴 左派方案（含 diff 草案）
    ├── youpai-proposal.md        # 🔵 右派方案（含 diff 草案）
    ├── zhongjian-proposal.md     # 🟡 中间路线方案（大任务时）
    ├── dangwei-decision.md       # ⭐ 党委最终决策
    ├── guowuyuan-tasks.md        # 🏢 国务院子任务清单
    ├── buwei-{N}-result.md       # 🔧 各部委执行报告
    ├── jiwei-verdict.md          # 🔍 纪委审查报告
    └── zhiku-report.md           # 📚 智库调研报告（按需生成）
```

## 🤔 FAQ

**Q: 这是认真的吗？**

A: 隐喻不是装饰，它就是架构。LLM 天然倾向附和——让两个 agent "自由讨论"，它们会迅速达成一致，盲区没人暴露。民主集中制直接解决这个问题：左派 system prompt 写死了"研究 SOTA、推倒重来"，右派写死了"复用现有、最小改动"。党委拿到的不是一个方案和一堆"我同意"，而是路线对立的具体方案各自带着 diff 和风险分析。对抗性辩论在法律（控辩）、学术（peer review）、军事（红蓝对抗）中都已验证，我们只是用政治隐喻命名了角色。

**Q: 所有 agent 都是同一个模型，"左右辩论"不是自己跟自己吵吗？**

A: 同一个模型 + 不同约束 = 不同输出。左派的工作流是搜索业界最佳实践再提革新方案，右派是摸清现有可复用资产再提最小改动。它们读的代码不同、搜索的东西不同、评估的维度不同。价值不在于"观点"，而在于强制搜索束覆盖更大的解空间——一个 agent 探索一条路径，两个对立 agent 至少探索两条。

**Q: 和 directive（美国宪政）、edict（三省六部）的核心区别？**

A: 三个框架都做全流程（规划→执行→审查）。区别在决策前：directive 的 NSC 独自规划，Senate 只能批准或否决；edict 的中书省独自规划，门下省只能驳回。审查都是二元的（行不行？）。SWCC 的协商是生成式的（有没有更好的方案？）——左右两派必须提出结构性不同的完整方案，党委综合裁决。驳回烂方案容易，但驳回之后还是同一个 agent 改一改再交——不如一开始就把不同路线摆上桌。

**Q: 如果党委做了错误的决策怎么办？**

A: 因为有对抗性协商，党委看到的是多个立场对立的方案和互相的风险批评，盲区在决策前就暴露了，"完全错误"的概率本身就低。即便如此，纪委会在执行后同时做代码审查和跑自动化测试，驳回后自动重试最多 2 轮，之后交人工。所有中间产物（`.tmp/swcc/`）完整保留，可以定位哪个环节出了问题。

**Q: token 消耗大吗？**

A: 小任务跳过辩论（3-4 次 agent 调用），中任务加左右辩论和党委（6-7 次），大任务再加中间路线（8-9 次）。不便宜，但一次错误的架构决策导致 debug 两小时，成本远超 10 分钟的 LLM 辩论。任务明确不需要讨论就用 `/juguo` 跳过所有协商直接干。

## Contributing

PRs welcome. 无论你是左派还是右派，我们都欢迎。

## License

MIT — 比任何政治制度都自由。

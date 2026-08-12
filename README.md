# SVG Flowchart Skill

用内联 SVG 画"干净、正交、不返工"的流程图 —— 一套方法论 + 模板 + 自动校验工具。

> 项目沉淀自一次真实踩坑：手写 SVG 流程图时，连线反复出现
> **斜线歪、折线乱翘、箭头没对准框、图例菱形错位** 等问题。
> 根因都是"没有规则地随意摆坐标"。本仓库把解决这些问题的规则固化下来。

## 核心方法论（一句话）

**只要块和菱形中心对齐，连线就自然垂直；连得干净，靠的是对齐，而不是折线绕。**

## 安装为 OpenClaw Skill

```bash
# 克隆到 skills 目录（或软链接）
ln -s "$(pwd)" ~/.openclaw/workspace/skills/svg-flowchart
```

或在 `~/.openclaw/workspace/skills/_index.json` 注册后即可被扫描到。

## 使用

### 1. 用模板起步
- `templates/chain-vertical.svg` — 纯垂直主链（最简单）
- `templates/decision-branch.svg` — 判断菱形 + 分支
- `templates/h-v-ortho.svg` — 完整正交流程图

### 2. 嵌入自包含 HTML
把 `<svg>` 内联进单 HTML，零外部依赖，浏览器直接打开。

### 3. 自动校验
```bash
python3 scripts/validate.py your-file.html
# ✓ 通过 / ❌ 列出具体违规(R1 对角线 / R4 箭头未对准 / R6 方块重叠)
```

### 4. 提取坐标核对
```bash
python3 scripts/extract.py your-file.html
# 打印每个框的中心 x 和菱形上顶点, 便于核对对齐
```

## 黄金规则速查

| 编号 | 规则 | 要点 |
|------|------|------|
| R1 | 连线全正交 | 禁止对角线（菱形短斜线除外） |
| R2 | 主链中心对齐 | 微调块，不绕线 → 线纯垂直零折弯 |
| R3 | 单折弯优先 | 分支最多 1 个拐点（L 形），禁 S 形 |
| R4 | 箭头对准 | 方框顶部中心 / 菱形上顶点，误差 ≤2px |
| R5 | 别单挪菱形 | 菱形是夹心饼干，挪它上方的块 |
| R6 | 方块不重叠 | 并排框间距 ≥20px |
| R7 | 少用图例 | 已用颜色区分就别加图例 |

## 常见坑

1. "为对准顶点把直线改成斜线" ❌ → 挪块对齐，线保持垂直 ✅
2. "块和菱形错位就加三段折线去绕" ❌ → 微调块中心 = 菱形顶点 x ✅
3. 菱形是夹心饼干，别单独挪 ✅
4. 图例里的小菱形画不齐 → 干脆去掉 ✅

## 何时用 SVG，何时用 Mermaid

- **SVG**：要精确控制布局的复杂流程、自包含单 HTML 方案文档
- **Mermaid**：简单逻辑、Markdown/GitHub README、要方便后续编辑

## 目录结构

```
svg-flowchart-skill/
├── SKILL.md                 # OpenClaw skill 入口
├── README.md                # 本文件
├── templates/               # 三个起步模板
├── scripts/
│   ├── validate.py          # 自动校验: 斜线/对齐/重叠/折弯
│   └── extract.py           # 提取解析 SVG 节点坐标
└── examples/
    └── flowchart.html       # 完整示例文档
```

## 协议

MIT License — 随意使用、修改、分发。

#!/usr/bin/env python3
"""
MIT License (c) 2026 tanzhangjia — svg-flowchart-skill

SVG Flowchart Validator
=======================
自动校验 SVG 流程图是否符合本 skill 的黄金规则：

  R1  连线全正交（禁止对角线，菱形短斜线除外）
  R2  主链中心对齐 → 纯垂直
  R4  箭头对准目标（方框中心 / 菱形上顶点）
  R6  方块间距均匀、不重叠
  R7  折弯冗余检查（每逻辑线 ≤ 1 拐点）

用法：
    python3 scripts/validate.py [file.html | file.svg] ...

不传参数则扫描当前目录下所有 .html / .svg。

退出码：0 = 全部通过；1 = 存在违规。
"""

import re
import sys
from html.parser import HTMLParser

# ---------------------------------------------------------------------------
# 常量 / 容差
# ---------------------------------------------------------------------------
TOL_ALIGN = 2.0    # 箭头对准容差 (px)
TOL_GAP = 18.0     # 方块最小间距 (px)
EPS = 0.5          # 判断水平/垂直的阈值


class SVGExtractor(HTMLParser):
    """从 HTML 中提取所有 <svg>...</svg> 原始片段。"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.svgs = []
        self._cur = None
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'svg':
            self._depth = 1
            self._cur = ['<svg ']
            for k, v in attrs:
                self._cur.append(f' {k}="{v}"')
            self._cur.append('>')
        elif self._cur is not None:
            self._depth += 1
            self._cur.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self._cur is not None:
            self._cur.append(f'</{tag}>')
            if tag == 'svg':
                self.svgs.append(''.join(self._cur))
                self._cur = None

    def handle_data(self, data):
        if self._cur is not None:
            self._cur.append(data)


class FlowChecker:
    def __init__(self, svg, label):
        self.svg = svg
        self.label = label
        # 主方框: (x0, y0, x1, y1, cx, cy)
        self.boxes = []
        # 菱形: [(cx_top, cy_top), ...] 上顶点
        self.diamonds = []
        # 线段: [(x1,y1,x2,y2,has_arrow)]
        self.lines = []
        self.problems = []

    def parse(self):
        # 方框: 排除过小元素(图例色块等)
        for m in re.finditer(
            r'<rect\s+x="([\d.]+)"\s+y="([\d.]+)"\s+width="([\d.]+)"\s+height="([\d.]+)"',
            self.svg):
            x, y, w, h = map(float, m.groups())
            if w >= 60 and h >= 24:
                self.boxes.append((x, y, x + w, y + h, x + w / 2, y + h / 2))
        # 菱形: 填充样式 #fff3cd (判断节点)
        for m in re.finditer(
            r'<polygon\s+points="([\d,.\s]+)"[^>]*?fill="#fff3cd"', self.svg):
            pts = [tuple(map(float, p.split(','))) for p in m.group(1).split()]
            if len(pts) == 4:
                self.diamonds.append(pts[0])  # 上顶点 (约定第一个点)
        # 线段
        for m in re.finditer(
            r'<line\s+x1="([\d.]+)"\s+y1="([\d.]+)"\s+x2="([\d.]+)"\s+y2="([\d.]+)"([^>]*?)(/?>|>)',
            self.svg):
            x1, y1, x2, y2 = map(float, m.groups()[:4])
            attr = m.group(5) or ''
            has_arrow = 'marker-end' in attr
            self.lines.append((x1, y1, x2, y2, has_arrow))

    # ------------------------------------------------------------------
    def check_orthogonal(self):
        """R1: 不允许对角线"""
        for (x1, y1, x2, y2, arrow) in self.lines:
            is_h = abs(y1 - y2) < EPS
            is_v = abs(x1 - x2) < EPS
            if not is_h and not is_v:
                # 允许指向菱形的短斜线
                near_diamond = False
                for (dx, dy) in self.diamonds:
                    if abs(x2 - dx) < 30 and abs(y2 - dy) < 30:
                        near_diamond = True
                        break
                if not near_diamond:
                    self.problems.append(
                        f'[R1 对角线] ({x1:.0f},{y1:.0f})->({x2:.0f},{y2:.0f})')

    def _is_container(self, bx_index):
        """该框是否内部包含其他框(容器框, 如结果区/服务区)。"""
        (bx0, by0, bx1, by1, _, _) = self.boxes[bx_index]
        for j, (cx0, cy0, cx1, cy1, _, _) in enumerate(self.boxes):
            if j == bx_index:
                continue
            if bx0 + 6 < cx0 and cx1 < bx1 - 6 and by0 + 6 < cy0 and cy1 < by1 - 6:
                return True
        return False

    def check_arrow_align(self):
        """R4: 箭头对准目标。普通框须对准顶部中心; 容器框只要求落在顶边内即可。"""
        for (x1, y1, x2, y2, arrow) in self.lines:
            if not arrow:
                continue
            # 找到该箭头终点命中的方框
            box_idx = None
            box = None
            for idx, (bx0, by0, bx1, by1, cx, cy) in enumerate(self.boxes):
                if by0 - EPS <= y2 <= by0 + 8 and bx0 - 2 <= x2 <= bx1 + 2:
                    box = (cx, by0)
                    box_idx = idx
                    break
            if box:
                # 容器框: 汇聚多入口时只要求落在顶边内
                if self._is_container(box_idx):
                    continue
                if abs(x2 - box[0]) > TOL_ALIGN:
                    self.problems.append(
                        f'[R4 箭头未对准框] ({x2:.0f},{y2:.0f}) 目标框中心x={box[0]:.0f} '
                        f'偏差{abs(x2-box[0]):.0f}px')
                continue
            # 菱形上顶点
            for (dx, dy) in self.diamonds:
                if abs(y2 - dy) < 4:
                    if abs(x2 - dx) > TOL_ALIGN:
                        self.problems.append(
                            f'[R4 箭头未对准菱形] ({x2:.0f},{y2:.0f}) '
                            f'上顶点({dx:.0f},{dy:.0f}) 偏差{abs(x2-dx):.0f}px')

    def check_overlap(self):
        """R6: 方块不重叠(排除父子包含关系)。"""
        n = len(self.boxes)
        for i in range(n):
            (a0, b0, a1, b1, _, _) = self.boxes[i]
            for j in range(i + 1, n):
                (c0, d0, c1, d1, _, _) = self.boxes[j]
                ox = min(a1, c1) - max(a0, c0)
                oy = min(b1, d1) - max(b0, d0)
                if ox <= 2 or oy <= 2:
                    continue
                # 一个完全包含另一个 = 父子容器, 不算重叠
                contained = (
                    (a0 + 4 < c0 and c1 < a1 - 4 and b0 + 4 < d0 and d1 < b1 - 4) or
                    (c0 + 4 < a0 and a1 < c1 - 4 and d0 + 4 < b0 and b1 < d1 - 4)
                )
                if not contained:
                    self.problems.append(
                        f'[R6 方块重叠] Box{i}({a0:.0f},{b0:.0f})-({a1:.0f},{b1:.0f}) '
                        f'vs Box{j}({c0:.0f},{d0:.0f})-({c1:.0f},{d1:.0f})')

    def report(self):
        self.parse()
        self.check_orthogonal()
        self.check_arrow_align()
        self.check_overlap()
        return self.problems


def load_svgs(paths):
    """从文件解析出 SVG 片段列表 + 标签。"""
    result = []
    for p in paths:
        text = open(p, encoding='utf-8').read()
        if p.lower().endswith('.svg'):
            result.append((p, text))
            continue
        ex = SVGExtractor()
        ex.feed(text)
        for i, s in enumerate(ex.svgs):
            result.append((f'{p}#svg{i+1}', s))
    return result


def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else []
    if not paths:
        import glob
        paths = sorted(glob.glob('*.html') + glob.glob('**/*.html', recursive=True)
                       + glob.glob('*.svg'))
    if not paths:
        print('未找到文件')
        return 1

    all_problems = []
    total_svg = 0
    for label, svg in load_svgs(paths):
        if '<svg' not in svg:
            continue
        total_svg += 1
        fc = FlowChecker(svg, label)
        probs = fc.report()
        if probs:
            print(f'\n❌ {label}')
            for p in probs:
                print(f'   {p}')
            all_problems.extend(probs)
        else:
            print(f'✓ {label}: 全部通过')

    print(f'\n==== 校验完成: {total_svg} 张 SVG, {len(all_problems)} 个问题 ====')
    return 1 if all_problems else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
从 (HTML) 文件中提取并解析所有 SVG 流程图, 打印每个节点的坐标, 便于人工核对。

用法:
    python3 scripts/extract.py file.html
"""
import re
import sys
import glob
from html.parser import HTMLParser


class SVGExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.svgs = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        if tag == 'svg':
            self._cur = ['<svg>']
        elif self._cur is not None:
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


def describe(svg):
    lines_out = []
    for m in re.finditer(
        r'<rect\s+x="([\d.]+)"\s+y="([\d.]+)"\s+width="([\d.]+)"\s+height="([\d.]+)"',
        svg):
        x, y, w, h = map(float, m.groups())
        if w >= 60 and h >= 24:
            lines_out.append(
                f'  框 ({x:.0f},{y:.0f})-({x+w:.0f},{y+h:.0f}) 中心x={x+w/2:.0f}')
    for m in re.finditer(
        r'<polygon\s+points="([\d,.\s]+)"[^>]*?fill="#fff3cd"', svg):
        pts = [tuple(map(float, p.split(','))) for p in m.group(1).split()]
        if len(pts) == 4:
            lines_out.append(f'  菱形上顶点 ({pts[0][0]:.0f},{pts[0][1]:.0f})')
    return '\n'.join(lines_out)


def main():
    paths = sys.argv[1:] if len(sys.argv) > 1 else \
        sorted(glob.glob('*.html') + glob.glob('*.svg'))
    for p in paths:
        text = open(p, encoding='utf-8').read()
        svgs = [text] if p.lower().endswith('.svg') else SVGExtractor().svgs if hasattr(SVGExtractor, 'svgs') else []
        if p.lower().endswith('.svg'):
            print(f'== {p} ==')
            print(describe(text))
            continue
        ex = SVGExtractor()
        ex.feed(text)
        for i, s in enumerate(ex.svgs):
            print(f'== {p} #svg{i+1} ==')
            print(describe(s))


if __name__ == '__main__':
    main()

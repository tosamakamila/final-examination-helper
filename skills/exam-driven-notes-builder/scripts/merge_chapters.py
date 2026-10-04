# -*- coding: utf-8 -*-
"""
通用章节合并脚本
功能：把分章笔记 第N章*.md 按章号顺序合并为一个文件，章间用 --- 分隔
用法：python merge_chapters.py <分章目录> [-o 输出.md]
示例：python merge_chapters.py "输出/遗传学" -o "输出/遗传学/遗传学_复习笔记（合并版）.md"

说明：
- 输入为目录时，取目录下所有 第N章*.md（N为阿拉伯数字），按章号升序合并
- 读取自动兼容 UTF-8 BOM（合并版文件常见），输出为无 BOM 的 UTF-8
- 未指定 -o 时，默认输出到该目录下 [目录名]_复习笔记（合并版）.md
- 合并版命名遵循《教材整理规则.md》第八节
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')


def chapter_num(filename):
    """从文件名提取章号（第N章），无章号返回 None"""
    m = re.match(r'第(\d+)章', filename)
    return int(m.group(1)) if m else None


def collect_chapter_files(path):
    """收集待合并文件：目录取全部 第N章*.md，文件直接返回"""
    if os.path.isdir(path):
        files = [f for f in os.listdir(path)
                 if f.endswith('.md') and chapter_num(f) is not None]
        files.sort(key=lambda f: chapter_num(f))
        if not files:
            raise FileNotFoundError(f'目录下未找到 第N章*.md 文件: {path}')
        numbers = [chapter_num(f) for f in files]
        duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
        if duplicates:
            raise ValueError(f'存在同章多个文件，请先确定唯一成品，未写入合并版: {duplicates}')
        return [os.path.join(path, f) for f in files]
    if not os.path.isfile(path):
        raise FileNotFoundError(f'路径不存在: {path}')
    return [path]


def merge_chapters(path, output=None):
    """按章号顺序合并分章md，返回输出路径"""
    files = collect_chapter_files(path)

    if output is None:
        base = path if os.path.isdir(path) else os.path.dirname(path) or '.'
        name = os.path.basename(os.path.abspath(base))
        output = os.path.join(base, f'{name}_复习笔记（合并版）.md')

    if os.path.normcase(os.path.abspath(output)) in {os.path.normcase(os.path.abspath(fp)) for fp in files}:
        raise ValueError('合并输出不能覆盖输入章节文件')

    parts = []
    for fp in files:
        with open(fp, 'r', encoding='utf-8-sig') as f:
            parts.append(f.read().strip())
        print(f'  + {os.path.basename(fp)}')

    with open(output, 'w', encoding='utf-8') as f:
        f.write('\n\n---\n\n'.join(parts) + '\n')

    print(f'合并完成，共 {len(files)} 章 -> {output}')
    return output


def main():
    parser = argparse.ArgumentParser(description='按章号顺序合并分章笔记')
    parser.add_argument('path', help='分章md所在目录（或单个md文件）')
    parser.add_argument('-o', '--output', default=None, help='输出文件路径（默认 [目录名]_复习笔记（合并版）.md）')
    args = parser.parse_args()
    merge_chapters(args.path, args.output)


if __name__ == '__main__':
    main()

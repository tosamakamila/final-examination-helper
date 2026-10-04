# -*- coding: utf-8 -*-
"""
通用按章拆分脚本
功能：将合并的考试重点笔记按"# 第X章"标题拆分为单章md文件
用法：python split_chapters.py <输入md> <输出目录>
示例：python split_chapters.py "输出/动物生理学/动物生理学_考试重点.md" "缓存/动物生理学/章节拆分"

说明：按"# 第X章"一级标题切分（章号后可带或不带标题文字），输出文件名为"第N章.md"（章号支持一~九十九）
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cn_to_num(s):
    """中文数字转阿拉伯数字（支持 一~九十九，如 二十、三十五）"""
    if s in CN_NUM:
        return CN_NUM[s]
    m = re.fullmatch(r'([一二三四五六七八九]?)十([一二三四五六七八九]?)', s)
    if m:
        tens = CN_NUM[m.group(1)] if m.group(1) else 1
        ones = CN_NUM[m.group(2)] if m.group(2) else 0
        return tens * 10 + ones
    raise ValueError(f'无法解析章节号"{s}"（仅支持一~九十九），请检查章节标题格式')


def split_chapters(input_file, output_dir):
    """按章拆分笔记，返回章节列表"""
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    chapters = []
    current_start = None
    current_title = None
    fence = None
    for i, line in enumerate(lines):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line.rstrip('\n'))
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            continue
        if marker:
            fence = marker[1]
            continue
        m = re.match(r'^#\s+(第\s*(?:\d+|[一二三四五六七八九十]+)\s*章.*)', line)
        if m:
            if current_start is not None:
                chapters.append((current_title, current_start, i))
            current_title = m.group(1)
            current_start = i
    if current_start is not None:
        chapters.append((current_title, current_start, len(lines)))

    if not chapters:
        print(f'未找到"# 第X章"标题，请检查输入文件格式: {input_file}')
        return []

    numbered = []
    for title, start, end in chapters:
        m = re.match(r'第\s*(\d+|[一二三四五六七八九十]+)\s*章', title)
        token = m.group(1)
        ch_num = int(token) if token.isdigit() else cn_to_num(token)
        if ch_num in [item[0] for item in numbered]:
            raise ValueError(f'重复章节号 {ch_num}，未写入章节，先核对正文与目录标题')
        numbered.append((ch_num, title, start, end))

    for ch_num, title, start, end in numbered:
        out_path = os.path.join(output_dir, f'第{ch_num}章.md')
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(''.join(lines[start:end]))
        print(f'{title}: lines {start + 1}-{end}, saved to {out_path}')

    print(f'拆分完成，共 {len(chapters)} 章 -> {output_dir}')
    return chapters


def main():
    parser = argparse.ArgumentParser(description='按章拆分考试重点笔记')
    parser.add_argument('input', help='合并的md笔记路径')
    parser.add_argument('output_dir', help='输出目录')
    args = parser.parse_args()
    split_chapters(args.input, args.output_dir)


if __name__ == '__main__':
    main()

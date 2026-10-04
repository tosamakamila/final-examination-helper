import re
import sys
import os
import argparse

sys.stdout.reconfigure(encoding='utf-8')


def clean_textbook(content):
    lines = content.split('\n')
    # 未核准章节范围时不自动裁剪首尾；目录、习题和来源定位供下游索引。
    body_lines = lines

    cleaned = []
    prev_empty = False
    for line in body_lines:
        stripped = line.strip()

        if re.match(r'^·\d+·$', stripped):
            continue
        if re.match(r'^#\s+第[一二三四五六七八九十]+章\s+', stripped) and re.search(r'[·…]{2,}', stripped):
            continue
        if re.match(r'^##\s+', stripped) and re.search(r'[·…]{2,}$', stripped):
            continue

        is_empty = stripped == ''
        if is_empty and prev_empty:
            prev_empty = True
            continue
        prev_empty = is_empty

        cleaned.append(line)

    return '\n'.join(cleaned)


def clean_ppt(content):
    lines = content.split('\n')
    cleaned = []
    prev_empty = False

    for line in lines:
        stripped = line.strip()

        # 保留幻灯片编号与分隔线，不能丢失题目/图示的来源位置。
        if not stripped:
            if prev_empty:
                continue
            prev_empty = True
            cleaned.append(line)
            continue
        prev_empty = False

        cleaned.append(line)

    return '\n'.join(cleaned)


def detect_source_type(content):
    if re.search(r'^(?:#\s*幻灯片\s*\d+|===\s*幻灯片\s*\d+\s*===)', content, re.MULTILINE):
        return 'ppt'
    if re.search(r'^#\s*第[一二三四五六七八九十]+章', content, re.MULTILINE):
        return 'textbook'
    return 'unknown'


def clean_file(input_path, output_path=None, source_type='auto'):
    """清理单个文本文件，返回清理后的内容"""
    output_path = output_path or input_path

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_lines = len(content.split('\n'))

    if source_type == 'auto':
        source_type = detect_source_type(content)
        print(f'自动检测内容类型: {source_type}')

    if source_type == 'textbook':
        result = clean_textbook(content)
    elif source_type == 'ppt':
        result = clean_ppt(content)
    else:
        print('无法识别内容类型，使用课本模式清理')
        result = clean_textbook(content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    result_lines = len(result.split('\n'))
    print(f'原始行数: {original_lines}')
    print(f'清理后行数: {result_lines}')
    print(f'删除行数: {original_lines - result_lines}')
    print(f'输出: {output_path}')
    return result


def main():
    parser = argparse.ArgumentParser(description='OCR/PPT文本清理工具')
    parser.add_argument('input', help='待清理的Markdown文件路径')
    parser.add_argument('-o', '--output', default=None, help='输出文件路径（默认覆盖原文件）')
    parser.add_argument('-t', '--type', choices=['auto', 'textbook', 'ppt'], default='auto',
                        help='内容类型：auto(自动检测)、textbook(课本)、ppt(幻灯片)')
    args = parser.parse_args()

    clean_file(args.input, args.output, args.type)


if __name__ == '__main__':
    main()

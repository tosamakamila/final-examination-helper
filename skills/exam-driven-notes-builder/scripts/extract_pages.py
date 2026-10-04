# -*- coding: utf-8 -*-
"""
按页码范围提取已缓存文本
功能：从已提取的全文txt文件中，按页码范围提取指定章节文本
用法：python extract_pages.py <全文txt路径> <起始页> <结束页> <输出txt路径>
示例：python extract_pages.py "缓存/酶工程_课本全文.txt" 243 281 "缓存/酶工程_ch9.txt"

说明：全文txt文件需用 extract_pdf_full.py 生成，格式为"=== 第N页 ==="
"""
import sys
import re


def extract_pages(full_text_path, start_page, end_page, out_file):
    """从全文txt中按页码范围提取文本"""
    with open(full_text_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    current_page = None
    page_texts = {}

    for line in lines:
        m = re.match(r'=== 第(\d+)页 ===', line.strip())
        if m:
            current_page = int(m.group(1))
            page_texts[current_page] = []
        elif current_page is not None:
            page_texts[current_page].append(line)

    out = []
    for p in range(start_page, end_page + 1):
        if p in page_texts:
            out.append(f'=== 第{p}页 ===')
            out.append('\n'.join(page_texts[p]))

    result = '\n'.join(out)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f'写出 {len(result)} 字符 -> {out_file} (第{start_page}-{end_page}页)')
    return out_file


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('用法: python extract_pages.py <全文txt路径> <起始页> <结束页> <输出txt路径>')
        sys.exit(1)
    extract_pages(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])

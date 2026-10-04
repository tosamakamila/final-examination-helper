# -*- coding: utf-8 -*-
"""
PDF目录显示脚本
功能：显示PDF文件的目录（书签）结构
用法：python show_pdf_toc.py <PDF路径> [最大层级]
示例：python show_pdf_toc.py "教材/酶工程/酶工程.pdf" 2

依赖：pip install pymupdf
"""
import fitz
import sys

sys.stdout.reconfigure(encoding='utf-8')


def show_pdf_toc(pdf_path, max_level=99):
    """显示PDF目录结构，返回目录列表"""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    print(f'=== 目录 (共{len(toc)}条) ===')
    for level, title, page in toc:
        if level <= max_level:
            indent = '  ' * (level - 1)
            print(f'{indent}[L{level}] {title} -> p{page}')
    doc.close()
    return toc


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python show_pdf_toc.py <PDF路径> [最大层级]')
        sys.exit(1)
    max_level = int(sys.argv[2]) if len(sys.argv) > 2 else 99
    show_pdf_toc(sys.argv[1], max_level)

# -*- coding: utf-8 -*-
"""
PDF全文提取脚本
功能：从PDF文件提取全文文本，按页保存到txt文件
用法：python extract_pdf_full.py <PDF路径> <输出txt路径>
示例：python extract_pdf_full.py "教材/酶工程/酶工程.pdf" "缓存/酶工程_课本全文.txt"

依赖：pip install pymupdf
"""
import fitz
import sys

sys.stdout.reconfigure(encoding='utf-8')


def extract_pdf_full(pdf_path, out_path):
    """从PDF提取全文文本，按页保存到txt文件"""
    doc = fitz.open(pdf_path)
    print(f'总页数: {doc.page_count}')

    all_text = []
    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text()
        if text.strip():
            all_text.append({'page': i + 1, 'text': text})
        if (i + 1) % 50 == 0:
            print(f'已处理 {i + 1}/{doc.page_count} 页...')

    with open(out_path, 'w', encoding='utf-8') as f:
        for item in all_text:
            f.write('=== 第{}页 ===\n'.format(item['page']))
            f.write(item['text'])
            f.write('\n\n')

    print(f'完成! 共提取 {len(all_text)} 页文本 -> {out_path}')
    doc.close()
    return out_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python extract_pdf_full.py <PDF路径> <输出txt路径>')
        sys.exit(1)
    extract_pdf_full(sys.argv[1], sys.argv[2])

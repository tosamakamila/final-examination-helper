# -*- coding: utf-8 -*-
"""
Word文档提取脚本（支持.docx和.doc）
功能：提取Word文档中的段落和表格文本，输出Markdown
用法：python extract_word.py <Word路径> <输出md路径>
示例：python extract_word.py "教材/遗传学/课后题目.docx" "缓存/遗传学/课后题目.md"

说明：
- .docx 用 python-docx 提取：Heading/标题 样式映射为 # 层级，表格转为Markdown表格
- .doc 用 win32com（Word COM自动化）提取纯文本，需安装 Microsoft Word
- 自动根据扩展名选择提取方式
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')


def _heading_level(style_name):
    """识别标题样式，返回层级数字（1-6），非标题返回 None"""
    if not style_name:
        return None
    m = re.match(r'(?:heading|标题)\s*(\d+)', style_name.strip(), re.IGNORECASE)
    return min(int(m.group(1)), 6) if m else None


def _table_to_md(tbl):
    """python-docx 表格转 Markdown 表格"""
    rows = [[cell.text.strip().replace('\n', ' ') for cell in row.cells] for row in tbl.rows]
    if not rows:
        return ''
    out = ['| ' + ' | '.join(rows[0]) + ' |',
           '| ' + ' | '.join(['---'] * len(rows[0])) + ' |']
    for row in rows[1:]:
        out.append('| ' + ' | '.join(row) + ' |')
    return '\n'.join(out)


def extract_docx(path):
    """用 python-docx 提取 .docx（保持段落与表格顺序）"""
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(path)
    out = []
    for child in doc.element.body.iterchildren():
        if child.tag == qn('w:p'):
            para = Paragraph(child, doc)
            text = para.text.strip()
            if not text:
                continue
            level = _heading_level(para.style.name if para.style else '')
            out.append(f'{"#" * level} {text}' if level else text)
        elif child.tag == qn('w:tbl'):
            md = _table_to_md(Table(child, doc))
            if md:
                out.append(md)
    return '\n\n'.join(out)


def extract_doc_via_com(path):
    """用 win32com 提取 .doc 纯文本（需安装 Word）"""
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = None
    try:
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(path), ReadOnly=True)
        text = doc.Content.Text
        doc.Close(False)
        # COM 段落符 \r 转换为换行；\x07 为表格单元格分隔符
        return text.replace('\x07', ' ').replace('\r', '\n')
    finally:
        if word:
            word.Quit()
        pythoncom.CoUninitialize()


def extract_word(path):
    """按扩展名自动选择提取方式，返回文本内容"""
    if path.lower().endswith('.docx'):
        return extract_docx(path)
    if path.lower().endswith('.doc'):
        return extract_doc_via_com(path)
    raise ValueError(f'不支持的文件类型（仅 .docx/.doc）: {path}')


def main():
    if len(sys.argv) < 3:
        print('用法: python extract_word.py <Word路径> <输出md路径>')
        sys.exit(1)

    word_path, out_path = sys.argv[1], sys.argv[2]
    print(f'处理: {word_path}')
    try:
        content = extract_word(word_path)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'-> {out_path} ({len(content)} 字符)')
    except Exception as e:
        print(f'错误: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()

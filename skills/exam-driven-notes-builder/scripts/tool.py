# -*- coding: utf-8 -*-
"""
统一工具调用入口（教材生成工作流）
功能：一条命令调度所有子工具，无需重写脚本
用法：python tool.py <子命令> [参数]

子命令：
  pdf-full     <PDF> <out.txt>               提取PDF全文文本
  pdf-toc      <PDF> [层级]                   显示PDF目录
  pdf-pages    <全文.txt> <起> <止> <out.txt>  按页提取章节文本
  ocr          <PDF> <out.txt> [--start N] [--end N] [--dpi N] [--gpu]   PDF OCR识别
  image        <图片或目录> <out.txt> [--gpu]  图片OCR识别
  word         <Word> <out.md>                提取Word文档文本(.docx/.doc)
  ppt          <PPT> <out.txt>               提取单个PPT文本
  ppt-all      <PPT目录> <输出目录>            批量提取PPT文本
  clean        <文件> -o 输出 [-t 类型]      清理OCR/PPT文本并另存
  split-chapters <笔记.md> <输出目录>          按章拆分笔记
  merge        <分章目录> [-o 输出.md]         按章号顺序合并分章笔记
  lint-notes   <文件或目录> [--fix] [--source 课本文本]   笔记质量检查（教材整理规则）

示例：
  python tool.py pdf-full "教材/遗传学/遗传学.pdf" "缓存/遗传学_全文.txt"
  python tool.py ocr "教材/动物生理学/动物生理学.pdf" "缓存/动物生理学_OCR.txt" --start 1 --end 30 --gpu
  python tool.py merge "输出/遗传学"
  python tool.py lint-notes "输出/遗传学" --fix
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def cmd_pdf_full(args):
    from extract_pdf_full import extract_pdf_full
    extract_pdf_full(args.pdf, args.out)


def cmd_pdf_toc(args):
    from show_pdf_toc import show_pdf_toc
    show_pdf_toc(args.pdf, args.level)


def cmd_pdf_pages(args):
    from extract_pages import extract_pages
    extract_pages(args.full, args.start, args.end, args.out)


def cmd_ocr(args):
    from ocr_pdf import ocr_pdf
    ocr_pdf(args.pdf, args.out, args.start, args.end, args.dpi, args.gpu)


def cmd_image(args):
    from ocr_image import ocr_images
    ocr_images(args.input, args.out, args.gpu)


def cmd_word(args):
    from extract_word import extract_word
    content = extract_word(args.word)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'-> {args.out} ({len(content)} 字符)')


def cmd_ppt(args):
    from extract_ppt import extract_ppt
    content = extract_ppt(args.ppt)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'-> {args.out} ({len(content)} 字符)')


def cmd_ppt_all(args):
    from extract_all_ppt import extract_all_ppt
    extract_all_ppt(args.dir, args.outdir)


def cmd_clean(args):
    from clean_ocr import clean_file
    clean_file(args.input, args.output, args.type)


def cmd_split_chapters(args):
    from split_chapters import split_chapters
    split_chapters(args.input, args.outdir)


def cmd_merge(args):
    from merge_chapters import merge_chapters
    merge_chapters(args.path, args.output)


def cmd_lint_notes(args):
    from lint_notes import lint_notes
    sys.exit(1 if lint_notes(args.path, args.fix, args.source) else 0)


def build_parser():
    parser = argparse.ArgumentParser(
        prog='tool.py',
        description='教材生成工作流统一工具入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='运行 python tool.py <子命令> -h 查看子命令详细参数',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('pdf-full', help='提取PDF全文文本')
    p.add_argument('pdf')
    p.add_argument('out')
    p.set_defaults(func=cmd_pdf_full)

    p = sub.add_parser('pdf-toc', help='显示PDF目录')
    p.add_argument('pdf')
    p.add_argument('level', type=int, nargs='?', default=99)
    p.set_defaults(func=cmd_pdf_toc)

    p = sub.add_parser('pdf-pages', help='按页提取章节文本')
    p.add_argument('full')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('out')
    p.set_defaults(func=cmd_pdf_pages)

    p = sub.add_parser('ocr', help='PDF OCR识别')
    p.add_argument('pdf')
    p.add_argument('out')
    p.add_argument('--start', type=int, default=None)
    p.add_argument('--end', type=int, default=None)
    p.add_argument('--dpi', type=int, default=200)
    p.add_argument('--gpu', action='store_true')
    p.set_defaults(func=cmd_ocr)

    p = sub.add_parser('image', help='图片OCR识别（单张或目录）')
    p.add_argument('input')
    p.add_argument('out')
    p.add_argument('--gpu', action='store_true')
    p.set_defaults(func=cmd_image)

    p = sub.add_parser('word', help='提取Word文档文本(.docx/.doc)')
    p.add_argument('word')
    p.add_argument('out')
    p.set_defaults(func=cmd_word)

    p = sub.add_parser('ppt', help='提取单个PPT文本')
    p.add_argument('ppt')
    p.add_argument('out')
    p.set_defaults(func=cmd_ppt)

    p = sub.add_parser('ppt-all', help='批量提取PPT文本')
    p.add_argument('dir')
    p.add_argument('outdir')
    p.set_defaults(func=cmd_ppt_all)

    p = sub.add_parser('clean', help='清理OCR/PPT文本')
    p.add_argument('input')
    p.add_argument('-o', '--output', required=True, help='另存的清理后文本路径，保留原始提取')
    p.add_argument('-t', '--type', choices=['auto', 'textbook', 'ppt'], default='auto')
    p.set_defaults(func=cmd_clean)

    p = sub.add_parser('split-chapters', help='按章拆分笔记')
    p.add_argument('input')
    p.add_argument('outdir')
    p.set_defaults(func=cmd_split_chapters)

    p = sub.add_parser('merge', help='按章号顺序合并分章笔记')
    p.add_argument('path')
    p.add_argument('-o', '--output', default=None)
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser('lint-notes', help='笔记质量检查（依据教材整理规则，错误须清零）')
    p.add_argument('path')
    p.add_argument('--fix', action='store_true', help='自动修复安全项')
    p.add_argument('--source', default=None, help='课本OCR/清理文本，用于定义原文对照')
    p.set_defaults(func=cmd_lint_notes)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "out"):
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    if args.command in {"clean", "merge"} and args.output:
        if args.command == "clean" and os.path.normcase(os.path.realpath(args.input)) == os.path.normcase(os.path.realpath(args.output)):
            parser.error('clean 必须另存，输出路径不能与原始提取相同')
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    args.func(args)


if __name__ == '__main__':
    main()

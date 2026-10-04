# -*- coding: utf-8 -*-
"""
批量提取文件夹下所有PPT文本
功能：批量提取指定文件夹下所有.ppt和.pptx文件的文本
用法：python extract_all_ppt.py <PPT文件夹> <输出文件夹>
示例：python extract_all_ppt.py "教材/酶工程" "缓存"

说明：
- .pptx用python-pptx提取（pip install python-pptx）
- .ppt用win32com（PowerPoint COM自动化），需安装PowerPoint
- 输出文件名格式：PPT_<原文件名>.txt
"""
import os
import sys
import glob

# 复用单文件提取逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_ppt import extract_ppt


def extract_all_ppt(ppt_dir, out_dir):
    """批量提取文件夹下所有PPT文本"""
    os.makedirs(out_dir, exist_ok=True)

    files = sorted(
        glob.glob(os.path.join(ppt_dir, '*.ppt')) +
        glob.glob(os.path.join(ppt_dir, '*.pptx'))
    )
    print(f'找到 {len(files)} 个PPT文件')

    for f in files:
        name = os.path.basename(f)
        out_file = os.path.join(out_dir, f'PPT_{name}.txt')
        print(f'\n处理: {name}')
        try:
            content = extract_ppt(f)
            with open(out_file, 'w', encoding='utf-8') as fp:
                fp.write(content)
            print(f'  -> {out_file} ({len(content)} 字符)')
        except Exception as e:
            print(f'  错误: {e}')
    return out_dir


def main():
    if len(sys.argv) < 3:
        print('用法: python extract_all_ppt.py <PPT文件夹> <输出文件夹>')
        sys.exit(1)
    extract_all_ppt(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()

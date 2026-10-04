# -*- coding: utf-8 -*-
"""
通用图片OCR脚本（RapidOCR，支持GPU加速）
功能：对单张/多张图片（或整个目录）OCR识别，输出按图片分段的txt
用法：python ocr_image.py <图片或目录> <输出txt路径> [--gpu]
示例：python ocr_image.py "教材/遗传学/图片" "缓存/遗传学/图片_OCR.txt" --gpu

说明：
- 复用 ocr_pdf.py 的引擎工厂（GPU优先，失败自动回退CPU）
- 支持格式：png / jpg / jpeg / bmp / tiff
- 输出格式：===== 图片 N: 文件名 =====
- 目录输入时按文件名排序依次识别
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}


def collect_images(path):
    """收集待识别图片：目录取全部图片文件，文件直接返回"""
    if os.path.isdir(path):
        files = [f for f in sorted(os.listdir(path))
                 if os.path.splitext(f)[1].lower() in IMG_EXTS]
        if not files:
            raise FileNotFoundError(f'目录下未找到图片文件: {path}')
        return [os.path.join(path, f) for f in files]
    if not os.path.isfile(path):
        raise FileNotFoundError(f'路径不存在: {path}')
    return [path]


def ocr_images(path, out_path, use_gpu=False):
    """OCR图片或图片目录，输出按图片分段txt"""
    import numpy as np
    from PIL import Image
    from ocr_pdf import _create_ocr_engine

    img_paths = collect_images(path)
    print(f'待识别图片: {len(img_paths)} 张')
    ocr = _create_ocr_engine(use_gpu)

    with open(out_path, 'w', encoding='utf-8') as f:
        for i, p in enumerate(img_paths, 1):
            img = Image.open(p)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            result, _ = ocr(np.array(img))
            f.write(f'===== 图片 {i}: {os.path.basename(p)} =====\n')
            if result:
                f.write('\n'.join(line[1] for line in result))
            f.write('\n\n')
            print(f'  完成 {i}/{len(img_paths)}: {os.path.basename(p)}', flush=True)

    print(f'完成! -> {out_path}')
    return out_path


def main():
    parser = argparse.ArgumentParser(description='通用图片OCR脚本（RapidOCR）')
    parser.add_argument('input', help='图片文件或目录路径')
    parser.add_argument('out', help='输出txt路径')
    parser.add_argument('--gpu', action='store_true', help='使用GPU加速（需onnxruntime-gpu）')
    args = parser.parse_args()

    ocr_images(args.input, args.out, args.gpu)


if __name__ == '__main__':
    main()

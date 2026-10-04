# -*- coding: utf-8 -*-
"""
通用PDF OCR脚本（RapidOCR，支持GPU加速）
功能：将PDF页面渲染为图片后OCR识别，输出按页分段的txt
用法：python ocr_pdf.py <PDF路径> <输出txt路径> [--start N] [--end N] [--dpi N] [--gpu]
示例：python ocr_pdf.py "教材/动物生理学/动物生理学.pdf" "缓存/动物生理学/教材_OCR.txt" --start 1 --end 30 --dpi 200 --gpu

说明：
- 用PyMuPDF渲染页面，RapidOCR识别（中英文自动识别）
- --gpu 使用CUDA加速（需安装 onnxruntime-gpu），失败自动回退CPU
- 输出格式：===== PDF 第 N 页 =====

依赖：pip install pymupdf rapidocr-onnxruntime pillow numpy
"""
import argparse
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')


def _create_ocr_engine(use_gpu=False):
    """创建RapidOCR引擎，GPU优先，失败回退CPU"""
    from rapidocr_onnxruntime import RapidOCR
    if use_gpu:
        try:
            import cuda_setup
            cuda_setup.setup_cuda_path()
            print('  使用GPU (CUDA) OCR...', flush=True)
            return RapidOCR(det_use_cuda=True, cls_use_cuda=True, rec_use_cuda=True)
        except Exception as e:
            print(f'  GPU初始化失败({e})，回退CPU...', flush=True)
    print('  使用CPU OCR...', flush=True)
    return RapidOCR()


def ocr_pdf(pdf_path, out_path, start=None, end=None, dpi=200, use_gpu=False):
    """OCR PDF指定页码范围，输出按页分段txt"""
    import fitz
    import numpy as np
    from PIL import Image

    doc = fitz.open(pdf_path)
    total = doc.page_count
    start = start or 1
    end = min(end or total, total)
    if start < 1:
        start = 1
    if end > total:
        end = total

    print(f'PDF总页数: {total} | 本次OCR: 第{start}-{end}页 | DPI: {dpi}')

    ocr = _create_ocr_engine(use_gpu)

    with open(out_path, 'w', encoding='utf-8') as f:
        for i in range(start - 1, end):
            page = doc[i]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pix.tobytes('png')))
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            arr = np.array(img)

            result, _ = ocr(arr)
            f.write(f'===== PDF 第 {i + 1} 页 =====\n')
            if result:
                f.write('\n'.join(line[1] for line in result))
            f.write('\n\n')

            if (i + 1 - start + 1) % 10 == 0:
                print(f'  OCR进度: {i + 1}/{end} 页', flush=True)

    doc.close()
    print(f'完成! -> {out_path}')
    return out_path


def main():
    parser = argparse.ArgumentParser(description='通用PDF OCR脚本（RapidOCR）')
    parser.add_argument('pdf', help='PDF文件路径')
    parser.add_argument('out', help='输出txt路径')
    parser.add_argument('--start', type=int, default=None, help='起始页（从1开始，默认1）')
    parser.add_argument('--end', type=int, default=None, help='结束页（默认最后一页）')
    parser.add_argument('--dpi', type=int, default=200, help='渲染分辨率（默认200）')
    parser.add_argument('--gpu', action='store_true', help='使用GPU加速（需onnxruntime-gpu）')
    args = parser.parse_args()

    ocr_pdf(args.pdf, args.out, args.start, args.end, args.dpi, args.gpu)


if __name__ == '__main__':
    main()

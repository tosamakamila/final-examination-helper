# -*- coding: utf-8 -*-
"""
CUDA DLL 路径配置
功能：将 site-packages/nvidia/*/bin 目录加入DLL搜索路径，使 onnxruntime-gpu 能找到CUDA库
用法：import cuda_setup; cuda_setup.setup_cuda_path()
"""
import os
import sys


def _find_nvidia_bin_dirs():
    """扫描site-packages下nvidia包的bin目录"""
    dirs = []
    for sp in sys.path:
        nvidia_dir = os.path.join(sp, 'nvidia')
        if not os.path.isdir(nvidia_dir):
            continue
        for pkg in os.listdir(nvidia_dir):
            bin_dir = os.path.join(nvidia_dir, pkg, 'bin')
            if os.path.isdir(bin_dir):
                dirs.append(bin_dir)
    return dirs


def setup_cuda_path():
    """将nvidia CUDA库目录加入DLL搜索路径，返回加入的目录数"""
    bin_dirs = _find_nvidia_bin_dirs()
    added = 0
    for d in bin_dirs:
        try:
            os.add_dll_directory(d)
            added += 1
        except Exception:
            pass
    # onnxruntime的provider加载依赖PATH搜索，需同时前置到PATH
    if bin_dirs:
        new_path = os.pathsep.join(bin_dirs) + os.pathsep + os.environ.get('PATH', '')
        os.environ['PATH'] = new_path
    if added:
        print(f'  CUDA DLL路径已配置: {added} 个目录', flush=True)
    return added


if __name__ == '__main__':
    setup_cuda_path()
    import onnxruntime as ort
    print('providers:', ort.get_available_providers())

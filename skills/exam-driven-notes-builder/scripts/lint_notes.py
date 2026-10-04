# -*- coding: utf-8 -*-
"""
笔记质量检查脚本（依据《教材整理规则.md》）
功能：检查分章/合并笔记格式，--fix 自动修复安全项，不改写科学内容
用法：python lint_notes.py <文件或目录> [--fix] [--source 课本OCR文本]
示例：
  python lint_notes.py "输出/遗传学"
  python lint_notes.py "输出/遗传学/第5章_数量性状的遗传.md" --fix
  python lint_notes.py "输出/遗传学" --source "缓存/遗传学/遗传学_清理后.md"

检查项（错误级=质量闸门，须清零；警告级=仅报告）：
  E1 三大部分标题（## 一、名词解释 / ## 二、核心知识点整合 / ## 三、知识联系与记忆框架）缺失或不规范
  E2 名词解释区条目缺编号（裸 ### 标题）或编号不连续；条目缺少定义行
  E3 标签冒号误入粗体（如 **定义：** 应为 **定义**：）——--fix 可修
  E4 名词条目间缺 --- 分隔——--fix 可修
  E5 名词定义未并入第二部分（规则§三7：名词区每条定义应能在核心知识点整合中找到）
  E6 课后习题区（## 四、课后习题）之后还有 ## 区块 / 区内无编号题目 / 区内含考题照应
  E7-E11 围栏、表格、部分顺序、知识树及禁止的记忆口诀区
  E12-E13 学习端教学单元划分、意外引入及不应进入课堂/闪卡的内部标签
  W2 --source 时定义句在课本原文中找不到（疑似非教材原文；OCR噪声可能误报，人工复核）

说明：
- 合并版/多章文件自动按 `# ` 一级标题分章逐章检查
- 目录扫描时跳过 _开头文件与 *合并版*.md（合并版=分章的拼接，单独检查会重复）
- 读取兼容 UTF-8 BOM；有错误时退出码 1，便于作为"本章完成"闸门
"""
import argparse
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

SECTION_PATTERNS = {
    '一': re.compile(r'^##\s*一、\s*名词解释\s*$'),
    '二': re.compile(r'^##\s*二、\s*核心知识点整合\s*$'),
    '三': re.compile(r'^##\s*三、\s*知识联系与记忆框架\s*$'),
    '四': re.compile(r'^##\s*四、\s*课后习题\s*$'),
}
DEF_LABEL = re.compile(r'^\*\*定义\*\*[：:]\s*(.+)$|^定义[：:]\s*(.+)$')
REF_TAG = '【考题照应：'


def normalize(text):
    """规范化文本用于原文比对：去掉加粗/引用标记和全部空白"""
    return re.sub(r'[\s*>#`]', '', text)


def _def_candidates(def_text):
    """检查完整定义，不允许只有首句就判定多句定义已并入。"""
    text = def_text.strip()
    cands = [text, text.rstrip('。；;，,、')]
    return [normalize(c) for c in cands if normalize(c)]


def visible_lines(lines):
    """屏蔽围栏内容但保持行号，返回可分析行和未闭围栏位置。"""
    result = []
    active = None
    opened = None
    for i, line in enumerate(lines):
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if active:
            result.append('')
            if match and match[1][0] == active[0] and len(match[1]) >= len(active) and not match[2].strip():
                active = None
                opened = None
        elif match:
            active = match[1]
            opened = i
            result.append('')
        else:
            result.append(line)
    return result, opened


def table_cells(line):
    """按非转义、非行内代码中的竖线分列。"""
    parts = []
    start = 0
    code = 0
    i = 0
    while i < len(line):
        if line[i] == '\\':
            i += 2
            continue
        if line[i] == '`':
            j = i + 1
            while j < len(line) and line[j] == '`':
                j += 1
            length = j - i
            code = 0 if code == length else (length if not code else code)
            i = j
            continue
        if line[i] == '|' and not code:
            parts.append(line[start:i].strip())
            start = i + 1
        i += 1
    parts.append(line[start:].strip())
    if parts and not parts[0]:
        parts.pop(0)
    if parts and not parts[-1]:
        parts.pop()
    return parts


def lint_rendering(lines, issues):
    visible, opened = visible_lines(lines)
    if opened is not None:
        issues.append(('E7', opened + 1, '代码围栏未闭合'))
    i = 0
    while i < len(visible):
        line = visible[i]
        if re.match(r'^\s*[├└│]', line):
            issues.append(('E10', i + 1, '知识树/分支流程须放在 text 围栏内'))
        if re.match(r'^(?:#{1,6}\s+|\*\*)?(?:记忆口诀|口诀总结|记忆提示)', line):
            issues.append(('E11', i + 1, '按用户偏好删除口诀或类似记忆提示，保留知识关系与易错点'))
        if not line.lstrip().startswith('|'):
            i += 1
            continue
        start = i
        rows = []
        while i < len(visible) and visible[i].lstrip().startswith('|'):
            rows.append(table_cells(visible[i]))
            i += 1
        count = len(rows[0])
        if len(rows) < 2 or not all(re.fullmatch(r':?-{3,}:?', cell) for cell in rows[1]):
            issues.append(('E8', start + 1, '表格缺少有效分隔行（使用至少三个连字符）'))
        for j, row in enumerate(rows):
            if len(row) != count:
                issues.append(('E8', start + j + 1, f'表格列数不一致：期望 {count}，实际 {len(row)}'))


def split_chapters(lines):
    """按 `# ` 一级标题把文件切为章块，返回 [(章标题, 起始行号0基), ...]"""
    visible, _ = visible_lines(lines)
    starts = [i for i, ln in enumerate(visible) if re.match(r'^# \S', ln)]
    if not starts:
        return [('', 0)]
    blocks = [(lines[i].strip(), i) for i in starts]
    if starts[0] > 0:
        blocks.insert(0, ('', 0))
    return blocks


def _section_span(chapter_lines):
    """返回三部分在各章行内的 (起,止) 区间字典；键为 一/二/三"""
    spans = {}
    starts = []
    chapter_lines, _ = visible_lines(chapter_lines)
    for i, ln in enumerate(chapter_lines):
        for key, pat in SECTION_PATTERNS.items():
            if pat.match(ln.strip()):
                spans[key] = i
                starts.append(i)
    # 每部分区间延伸到下一个 ## 或章末
    result = {}
    for key, s in spans.items():
        e = len(chapter_lines)
        for j in range(s + 1, len(chapter_lines)):
            if re.match(r'^##\s', chapter_lines[j]):
                e = j
                break
        result[key] = (s, e)
    return result


def _fix_label_colon(text):
    """E3 修复：**定义：** -> **定义**："""
    return re.sub(r'^\*\*([^*\n]{1,20}?)[：:]\*\*[ \t]?(.*)$',
                  r'**\1**：\2', text, flags=re.MULTILINE)


def _fix_separators(section_text):
    """E4 修复：名词解释区所有 ### 条目之间统一 \n\n---\n\n 分隔"""
    lines = section_text.split('\n')
    visible, _ = visible_lines(lines)
    starts = [i for i, line in enumerate(visible) if line.startswith('### ')]
    if not starts:
        return section_text
    head = '\n'.join(lines[:starts[0]]).rstrip('\n')
    entries = []
    for j, start in enumerate(starts):
        end = starts[j + 1] if j + 1 < len(starts) else len(lines)
        block = '\n'.join(lines[start:end]).strip('\n')
        entries.append(re.sub(r'(?:\n\s*---\s*)+$', '', block).rstrip())
    return head + '\n\n' + '\n\n---\n\n'.join(entries) + '\n'


def lint_chapter(title, lines, source_norm, fix, issues, offset=0):
    """检查单个章块，问题追加到 issues（元组：级别, 行号, 描述），返回自动修复后的行"""
    spans = _section_span(lines)
    visible, _ = visible_lines(lines)
    order = []
    for i, ln in enumerate(visible):
        for key, pattern in SECTION_PATTERNS.items():
            if pattern.match(ln.strip()):
                order.append(key)
                if order.count(key) > 1:
                    issues.append(('E9', offset + i + 1, f'部分标题重复：{key}'))
    if order != sorted(order, key=lambda key: '一二三四'.index(key)):
        issues.append(('E9', None, '主体部分顺序应为一、二、三、四'))

    # E1 三大部分完整性
    for key, name in (('一', '名词解释'), ('二', '核心知识点整合'), ('三', '知识联系与记忆框架')):
        if key not in spans:
            hint = '（可先跑 tool.py fix-format 补"三、"编号）' if key == '三' else ''
            issues.append(('E1', None, f'缺少 "## {key}、{name}" 部分{hint}'))

    # E6/W3 课后习题区（第四部分）：存在时校验位置与题目；缺失仅警告
    if '四' in spans:
        s4 = spans['四'][0]
        tail_heads = [i for i in range(s4 + 1, len(lines)) if re.match(r'^##\s', visible[i])]
        if tail_heads:
            issues.append(('E6', offset + tail_heads[0] + 1,
                           '"## 四、课后习题" 之后还有其他 ## 区块：课后习题必须是本章最后一个部分'))
        else:
            e4 = spans['四'][1]
            q_lines = [ln for ln in visible[s4 + 1:e4] if re.match(r'^(?:\d{1,3}[.、．）)]|[（(]\d{1,3}[）)]|[一二三四五六七八九十百]+[、.．）)])', ln.strip())]
            if not q_lines:
                issues.append(('E6', offset + s4 + 1, '"## 四、课后习题" 区内没有任何编号题目'))
            tagged = [ln for ln in visible[s4 + 1:e4] if REF_TAG in ln]
            if tagged:
                issues.append(('E6', None, f'课后习题区内出现 {len(tagged)} 处【考题照应】：该区只抄题干，不加任何标注'))

    # E3 标签冒号在粗体内（全文范围检查，修复后再做后续检查）
    e3_count = 0
    fixed_lines = []
    for i, ln in enumerate(lines):
        if visible[i] and re.match(r'^\*\*[^*\n]{1,20}?[：:]\*\*', ln.strip()):
            e3_count += 1
            fixed_lines.append(re.sub(r'^(\*\*[^*\n]{1,20}?)[：:]\*\*[ \t]?(.*)$',
                                      r'\1**：\2', ln))
        else:
            fixed_lines.append(ln)
    if e3_count:
        issues.append(('E3', None, f'{e3_count} 处标签冒号误入粗体（如 **定义：**）'
                                   + ('，已自动修复' if fix else '，--fix 可修')))
    lines = fixed_lines

    # 引用式和纯文本照应均有效；缺少可选题目不产生警告。

    if '一' in spans and '二' in spans:
        s1, e1 = spans['一']
        s2, e2 = spans['二']
        sec1 = lines[s1 + 1:e1]
        sec1_visible, _ = visible_lines(sec1)
        sec2_visible, _ = visible_lines(lines[s2:e2])
        sec2_text = '\n'.join(sec2_visible)
        sec2_norm = normalize(sec2_text)
        unit_positions = [i for i, ln in enumerate(sec2_visible)
                          if re.match(r'^###\s+（[一二三四五六七八九十百]+）', ln)]
        if not unit_positions:
            issues.append(('E12', offset + s2 + 1, '核心知识点区缺少 ### （一）大主题，学习端无法正确分教学单元'))
        elif any(ln.strip() for ln in sec2_visible[1:unit_positions[0]]):
            issues.append(('E12', offset + s2 + 1, '第一教学主题前有正文，会被学习端额外切成引入单元'))
        for i, ln in enumerate(visible):
            if re.search(r'【(?:定义来源|资料依据|覆盖状态)[：:]', ln):
                issues.append(('E13', offset + i + 1, '内部来源/覆盖标签应放缓存，避免混入课堂或闪卡答案'))

        # E2 条目编号与定义行
        entries = []  # (行号, 编号|None, 条目名)
        for j, ln in enumerate(sec1_visible):
            m = re.match(r'^###\s+(\d+)\.\s*(.*)$', ln.strip())
            if m:
                entries.append((j, int(m.group(1)), m.group(2)))
                continue
            if re.match(r'^###\s+\S', ln.strip()):
                entries.append((j, None, ln.strip()[4:]))
        for j, num, name in entries:
            if num is None:
                issues.append(('E2', offset + s1 + 1 + j, f'名词条目缺少编号: ### {name}'))
        nums = [num for _, num, _ in entries if num is not None]
        if nums and nums != list(range(1, len(nums) + 1)):
            issues.append(('E2', None, f'名词条目编号不连续: {nums[:20]}'))
        if not entries:
            issues.append(('E2', None, '名词解释区没有任何 ### 条目'))
        if fix and entries and all(num is None for _, num, _ in entries):
            # 全部条目均无编号时安全地顺序编号；混合情形编号有歧义，仅报告
            counter = 0
            for j, ln in enumerate(sec1):
                if sec1_visible[j] and re.match(r'^###\s+\S', ln.strip()):
                    counter += 1
                    sec1[j] = re.sub(r'^(\s*)###\s+(.+?)\s*$', rf'\1### {counter}. \2', ln)
            lines = lines[:s1 + 1] + sec1 + lines[e1:]
            entries = [(j, i + 1, name) for i, (j, _, name) in enumerate(entries)]
            issues.append(('E2', None, f'名词条目均无编号，已自动顺序编号 1-{counter}'))

        # 每个条目：定义行存在性(E2)、定义并入第二部分(E5)、原文对照(W2)
        for j, num, name in entries:
            # 条目区间到下一个条目或部分末尾
            k = j + 1
            while k < len(sec1) and not re.match(r'^###\s', sec1_visible[k].strip()):
                k += 1
            block, _ = visible_lines(sec1[j + 1:k])
            def_text = None
            for ln in block:
                m = DEF_LABEL.match(ln.strip())
                if m:
                    def_text = m.group(1) or m.group(2)
                    break
            if def_text is None:
                issues.append(('E2', offset + s1 + 1 + j, f'条目 "{name}" 缺少定义行'))
                continue
            cands = _def_candidates(def_text)
            if cands and not any(c in sec2_norm for c in cands):
                issues.append(('E5', offset + s1 + 1 + j,
                               f'"{name}" 的完整定义未在第二部分找到（须在对应主题复用）'))
            if source_norm is not None and cands and not any(c in source_norm for c in cands):
                issues.append(('W2', offset + s1 + 1 + j,
                               f'"{name}" 的定义未在 --source 找到（可能为归纳/其他来源或OCR差异，人工复核）'))

        # E4 条目间 --- 分隔
        entry_idx = [j for j, _, _ in entries]
        missing = 0
        for a, b in zip(entry_idx, entry_idx[1:]):
            between = [ln.strip() for ln in sec1_visible[a + 1:b]]
            if '---' not in between:
                missing += 1
        if missing:
            issues.append(('E4', None, f'{missing} 处名词条目间缺 --- 分隔'
                                       + ('，已自动修复' if fix else '，--fix 可修')))
        if fix and entries and entry_idx and missing:
            sec1_text = '\n'.join(sec1)
            rebuilt = _fix_separators(sec1_text)
            new_lines = lines[:s1 + 1] + rebuilt.split('\n') + lines[e1:]
            lines = new_lines

    return lines


def lint_file(path, fix=False, source_norm=None):
    """检查单个文件，返回 (错误数, 警告数)；fix=True 时回写安全修复"""
    with open(path, 'r', encoding='utf-8-sig') as f:
        text = f.read()
    orig = text
    lines = text.split('\n')

    print(f'== {path}')
    issues = []
    lint_rendering(lines, issues)
    chapters = split_chapters(lines)
    new_lines = []
    for idx, (title, start) in enumerate(chapters):
        end = chapters[idx + 1][1] if idx + 1 < len(chapters) else len(lines)
        block = lines[start:end]
        fixed_block = lint_chapter(title, block, source_norm, fix, issues, offset=start)
        new_lines.extend(fixed_block)

    for level, lineno, msg in issues:
        loc = f'L{lineno}: ' if lineno else ''
        print(f'  [{level}] {loc}{msg}')
    errors = sum(1 for lv, _, _ in issues if lv.startswith('E'))
    warnings = sum(1 for lv, _, _ in issues if lv.startswith('W'))
    print(f'  -> 错误 {errors} / 警告 {warnings}')

    if fix and '\n'.join(new_lines) != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print('  （已写回自动修复）')
    return errors, warnings


def lint_notes(path, fix=False, source=None):
    """检查文件或目录，返回总错误数"""
    source_norm = None
    if source:
        with open(source, 'r', encoding='utf-8-sig') as f:
            source_norm = normalize(f.read())

    if os.path.isdir(path):
        files = sorted(f for f in os.listdir(path)
                       if f.endswith('.md') and not f.startswith('_') and '合并版' not in f)
        targets = [os.path.join(path, f) for f in files]
    else:
        targets = [path]

    if not targets:
        print('  [E1] 没有可检查的分章文件，不能判定教材已完成')
        return 1

    total_errors = total_warnings = 0
    for t in targets:
        e, w = lint_file(t, fix, source_norm)
        total_errors += e
        total_warnings += w

    print(f'== 共检查 {len(targets)} 个文件：错误 {total_errors}，警告 {total_warnings}')
    if total_errors:
        print('   存在错误级问题：--fix 可自动修复部分，其余须按提示补正后重跑至清零（质量闸门）')
    return total_errors


def main():
    parser = argparse.ArgumentParser(description='笔记质量检查（依据《教材整理规则.md》）')
    parser.add_argument('path', help='md文件或目录路径')
    parser.add_argument('--fix', action='store_true', help='自动修复安全项（E3冒号/E4分隔/全缺名词编号），保留引用式照应')
    parser.add_argument('--source', default=None, help='课本OCR/清理文本路径，用于定义原文对照(W2)')
    args = parser.parse_args()
    sys.exit(1 if lint_notes(args.path, args.fix, args.source) else 0)


if __name__ == '__main__':
    main()

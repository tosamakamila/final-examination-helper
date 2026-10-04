# -*- coding: utf-8 -*-
"""
文本处理脚本单元测试（unittest 标准库，无需额外依赖）
运行：python -m unittest discover -s tests -v
"""
import os
import sys
import shutil
import uuid
from pathlib import Path
import unittest
from contextlib import redirect_stdout, contextmanager
from io import StringIO

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT_DIR = str(Path(HERE).parent / 'skills' / 'exam-driven-notes-builder' / 'scripts')
sys.path.insert(0, TEXT_DIR)

from split_chapters import cn_to_num, split_chapters          # noqa: E402
from merge_chapters import chapter_num, merge_chapters        # noqa: E402
from lint_notes import lint_notes                              # noqa: E402
from clean_ocr import clean_textbook, clean_ppt, detect_source_type  # noqa: E402

GOOD_NOTE = '''# 第1章 测试章

## 一、名词解释

### 1. 遗传学（Genetics）

**定义**：研究生物遗传与变异的科学。

---

### 2. 变异（Variation）

**定义**：生物亲子代之间的差异现象。

【考题照应：2022A 名词解释第1题（变异）】

## 二、核心知识点整合

### （一）基础

遗传学是研究生物遗传与变异的科学。变异指生物亲子代之间的差异现象。

## 三、知识联系与记忆框架

知识关系：
- 概念、条件与结果的联系
'''


@contextmanager
def test_directory():
    # Windows 沙箱中 mode=0700 的临时目录可能无法继承访问权；使用工作区内普通目录。
    root = (Path(HERE).parent / '.tmp' / 'tests').resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = root / ('case-' + uuid.uuid4().hex)
    target.mkdir()
    try:
        yield str(target)
    finally:
        resolved = target.resolve()
        resolved.relative_to(root)
        if resolved == root:
            raise ValueError('测试清理不得删除临时根目录')
        shutil.rmtree(resolved)


def _write(path, text, bom=False):
    with open(path, 'w', encoding='utf-8-sig' if bom else 'utf-8') as f:
        f.write(text)


class TestCnToNum(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(cn_to_num('一'), 1)
        self.assertEqual(cn_to_num('十'), 10)
        self.assertEqual(cn_to_num('十五'), 15)
        self.assertEqual(cn_to_num('二十'), 20)
        self.assertEqual(cn_to_num('二十一'), 21)
        self.assertEqual(cn_to_num('三十五'), 35)
        self.assertEqual(cn_to_num('九十九'), 99)

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            cn_to_num('一百')


class TestSplitChapters(unittest.TestCase):
    def test_arabic_chapters_and_fenced_examples(self):
        with test_directory() as d:
            src = os.path.join(d, 'note.md')
            out = os.path.join(d, 'out')
            text = '# 第1章 A\n正文\n```text\n# 第2章 示例标题\n```\n# 第 3 章 C\n后章正文\n'
            _write(src, text)
            with redirect_stdout(StringIO()):
                chapters = split_chapters(src, out)
            self.assertEqual(len(chapters), 2)
            self.assertTrue(os.path.exists(os.path.join(out, '第1章.md')))
            self.assertTrue(os.path.exists(os.path.join(out, '第3章.md')))
            self.assertFalse(os.path.exists(os.path.join(out, '第2章.md')))

    def test_duplicate_numbers_do_not_overwrite_chapter(self):
        with test_directory() as d:
            src = os.path.join(d, 'note.md')
            out = os.path.join(d, 'out')
            os.makedirs(out)
            preserved = os.path.join(out, '第1章.md')
            _write(preserved, '已确认章节')
            _write(src, '# 第一章 A\n正文\n# 第1章 B\n重复\n')
            with self.assertRaises(ValueError):
                split_chapters(src, out)
            with open(preserved, encoding='utf-8') as f:
                self.assertEqual(f.read(), '已确认章节')

    def test_split_twenty_plus_and_bom(self):
        with test_directory() as d:
            src = os.path.join(d, 'note.md')
            out = os.path.join(d, 'out')
            text = '\n'.join([
                '# 第十九章 A', 'a', '# 第二十章 B', 'b',
                '# 第二十一章', 'c', '# 第三十五章 D', 'd', '',
            ])
            _write(src, text, bom=True)  # BOM 文件也必须正常切分
            with redirect_stdout(StringIO()):
                chapters = split_chapters(src, out)
            self.assertEqual(len(chapters), 4)
            for n in (19, 20, 21, 35):
                self.assertTrue(os.path.exists(os.path.join(out, f'第{n}章.md')))
            self.assertFalse(os.path.exists(os.path.join(out, '第0章.md')))


class TestMergeChapters(unittest.TestCase):
    def test_numeric_sort_and_bom(self):
        self.assertEqual(chapter_num('第9章_甲.md'), 9)
        self.assertEqual(chapter_num('第10章_乙.md'), 10)
        self.assertIsNone(chapter_num('绪论.md'))
        with test_directory() as d:
            _write(os.path.join(d, '第2章_乙.md'), '# 第2章 乙\n\n乙内容', bom=True)
            _write(os.path.join(d, '第10章_丁.md'), '# 第10章 丁\n\n丁内容')
            _write(os.path.join(d, '第1章_甲.md'), '# 第1章 甲\n\n甲内容')
            out = os.path.join(d, 'merged.md')
            with redirect_stdout(StringIO()):
                merge_chapters(d, out)
            with open(out, encoding='utf-8') as f:
                content = f.read()
            self.assertNotIn('\ufeff', content)
            order = [content.index(f'第{n}章') for n in (1, 2, 10)]
            self.assertEqual(order, sorted(order))
            self.assertIn('---', content)

    def test_default_output_name(self):
        with test_directory() as d:
            _write(os.path.join(d, '第1章_甲.md'), '# 第1章 甲')
            with redirect_stdout(StringIO()):
                out = merge_chapters(d)
            self.assertTrue(out.endswith('_复习笔记（合并版）.md'))
            self.assertTrue(os.path.exists(out))


class TestLintNotes(unittest.TestCase):
    def _run(self, d, fix=False, source=None):
        buf = StringIO()
        with redirect_stdout(buf):
            errors = lint_notes(d, fix, source)
        return errors, buf.getvalue()

    def test_good_note_passes(self):
        with test_directory() as d:
            _write(os.path.join(d, '第1章_测试.md'), GOOD_NOTE)
            errors, out = self._run(d)
            self.assertEqual(errors, 0, out)

    def test_detects_and_fixes_mechanical_issues(self):
        bad = GOOD_NOTE.replace('**定义**：研究生物遗传与变异的科学。',
                                '**定义：** 研究生物遗传与变异的科学。')
        bad = bad.replace('\n---\n', '\n')  # 去掉分隔
        bad = bad.replace('【考题照应：2022A 名词解释第1题（变异）】',
                          '> 【考题照应：2022A 名词解释第1题（变异）】')
        with test_directory() as d:
            fp = os.path.join(d, '第1章_测试.md')
            _write(fp, bad)
            errors, out = self._run(d)
            self.assertGreater(errors, 0)
            self.assertIn('E3', out)
            self.assertIn('E4', out)
            # --fix 后机械问题清零，E5（甲的定义句仍能并入）不应误报
            errors2, out2 = self._run(d, fix=True)
            self.assertIn('已自动修复', out2)
            errors3, out3 = self._run(d)
            self.assertEqual(errors3, 0, out3)
            with open(fp, encoding='utf-8') as f:
                self.assertIn('> 【考题照应：', f.read())

    def test_e5_missing_merge_detected(self):
        bad = GOOD_NOTE.replace('变异指生物亲子代之间的差异现象。', '（本句被删）')
        with test_directory() as d:
            _write(os.path.join(d, '第1章_测试.md'), bad)
            errors, out = self._run(d)
            self.assertGreater(errors, 0)
            self.assertIn('E5', out)

    def test_e1_missing_section(self):
        bad = GOOD_NOTE.split('## 三、')[0]  # 缺第三部分
        with test_directory() as d:
            _write(os.path.join(d, '第1章_测试.md'), bad)
            errors, out = self._run(d)
            self.assertIn('E1', out)

    def test_w2_source_check(self):
        with test_directory() as d:
            _write(os.path.join(d, '第1章_测试.md'), GOOD_NOTE)
            src = os.path.join(d, 'source.txt')
            _write(src, '课本原文里只有：研究生物遗传与变异的科学。没有另一句。')
            _, out = self._run(d, source=src)
            self.assertIn('W2', out)  # "变异"的定义不在原文中

    def test_merged_file_and_ledger_skipped_in_dir_scan(self):
        with test_directory() as d:
            _write(os.path.join(d, '第1章_测试.md'), GOOD_NOTE)
            _write(os.path.join(d, '课程_复习笔记（合并版）.md'), GOOD_NOTE)
            _write(os.path.join(d, '_进度.md'), '# 进度')
            _, out = self._run(d)
            headers = [l for l in out.splitlines()
                       if l.startswith('== ') and not l.startswith('== 共')]
            self.assertEqual(len(headers), 1)  # 只检查了分章文件

    def test_no_optional_exam_or_exercise_is_valid_without_warnings(self):
        note = GOOD_NOTE.replace('【考题照应：2022A 名词解释第1题（变异）】', '')
        with test_directory() as d:
            _write(os.path.join(d, '第1章.md'), note)
            errors, out = self._run(d)
            self.assertEqual(errors, 0, out)
            self.assertIn('警告 0', out)

    def test_empty_directory_cannot_pass_completion_check(self):
        with test_directory() as d:
            errors, out = self._run(d)
            self.assertGreater(errors, 0)
            self.assertIn('没有可检查', out)

    def test_teaching_units_and_internal_metadata_contract(self):
        cases = [
            (GOOD_NOTE.replace('### （一）基础', '### 1. 基础'), 'E12'),
            (GOOD_NOTE.replace('### （一）基础', '额外介绍\n\n### （一）基础'), 'E12'),
            (GOOD_NOTE + '\n> 【定义来源：B01 第3页】\n', 'E13'),
        ]
        for note, code in cases:
            with self.subTest(code=code), test_directory() as d:
                _write(os.path.join(d, '第1章.md'), note)
                errors, out = self._run(d)
                self.assertGreater(errors, 0)
                self.assertIn(code, out)

    def test_fix_is_idempotent_and_does_not_shift_next_chapter(self):
        first = GOOD_NOTE.replace('### 1. ', '### ').replace('### 2. ', '### ').replace('\n---\n', '\n')
        second = GOOD_NOTE.replace('# 第1章 测试章', '# 第2章 后章')
        with test_directory() as d:
            fp = os.path.join(d, '合并.md')
            _write(fp, first + '\n\n---\n\n' + second)
            self._run(fp, fix=True)
            with open(fp, encoding='utf-8') as f:
                once = f.read()
            self._run(fp, fix=True)
            with open(fp, encoding='utf-8') as f:
                twice = f.read()
            self.assertEqual(once, twice)
            self.assertTrue(once.endswith(second))
            errors, out = self._run(fp)
            self.assertEqual(errors, 0, out)

    def test_definition_tail_must_be_merged(self):
        note = GOOD_NOTE.replace('**定义**：研究生物遗传与变异的科学。',
                                 '**定义**：研究生物遗传与变异的科学。包括遗传信息传递的条件。')
        with test_directory() as d:
            _write(os.path.join(d, '第1章.md'), note)
            errors, out = self._run(d)
            self.assertGreater(errors, 0)
            self.assertIn('E5', out)

    def test_fenced_headings_do_not_split_chapters_and_are_preserved(self):
        block = '\n```text\n# 这是图示标题\n## 一、名词解释\n### 示例而非名词\n**定义：** 不应被改写\n| 这不是表格 |\n```\n'
        note = GOOD_NOTE.replace('### 1. 遗传学（Genetics）', '### 1. 遗传学（Genetics）' + block)
        with test_directory() as d:
            fp = os.path.join(d, '第1章.md')
            _write(fp, note)
            self._run(fp, fix=True)
            with open(fp, encoding='utf-8') as f:
                self.assertIn(block, f.read())
            errors, out = self._run(fp)
            self.assertEqual(errors, 0, out)

    def test_rendering_defects_are_detected(self):
        for extra, code in [('\n```text\n未闭合\n', 'E7'),
                            ('\n| A | B |\n| --- | --- |\n| 少一列 |\n', 'E8'),
                            ('\n├── 未放围栏\n', 'E10'),
                            ('\n**记忆口诀**：测试\n', 'E11')]:
            with self.subTest(code=code), test_directory() as d:
                _write(os.path.join(d, '第1章.md'), GOOD_NOTE + extra)
                errors, out = self._run(d)
                self.assertGreater(errors, 0)
                self.assertIn(code, out)

    def test_valid_table_with_code_and_escaped_pipes(self):
        table = '\n| 表达 | 说明 |\n| --- | --- |\n| `A|B` | A\\|B |\n'
        with test_directory() as d:
            _write(os.path.join(d, '第1章.md'), GOOD_NOTE + table)
            errors, out = self._run(d)
            self.assertEqual(errors, 0, out)

    def test_sections_reordered_or_duplicated_fail(self):
        for bad in [GOOD_NOTE.replace('## 一、名词解释', '## 三、知识联系与记忆框架'),
                    GOOD_NOTE + '\n## 二、核心知识点整合\n']:
            with test_directory() as d:
                _write(os.path.join(d, '第1章.md'), bad)
                errors, out = self._run(d)
                self.assertGreater(errors, 0)
                self.assertIn('E9', out)

    def test_original_parenthesized_exercise_number_is_accepted(self):
        note = GOOD_NOTE + '\n## 四、课后习题\n\n（1）解释遗传与变异。\n'
        with test_directory() as d:
            _write(os.path.join(d, '第1章.md'), note)
            errors, out = self._run(d)
            self.assertEqual(errors, 0, out)


class TestSourcePreservation(unittest.TestCase):
    def test_cleaning_preserves_location_numbers_and_exercises(self):
        source = '=== 第1页 ===\n# 第1章 绪论\n正文\n参考文献\n复习思考题\n（1）题目\n42\n'
        result = clean_textbook(source)
        for text in ['=== 第1页 ===', '# 第1章', '复习思考题', '（1）题目', '42']:
            self.assertIn(text, result)

    def test_current_and_legacy_ppt_locations_are_preserved(self):
        for marker in ['=== 幻灯片 1 ===', '# 幻灯片 1']:
            with self.subTest(marker=marker):
                source = marker + '\n主题\n\n\n正文\n'
                self.assertEqual(detect_source_type(source), 'ppt')
                self.assertIn(marker, clean_ppt(source))


class TestSafeMerge(unittest.TestCase):
    def test_duplicate_chapter_cannot_overwrite_existing_total(self):
        with test_directory() as d:
            _write(os.path.join(d, '第1章_甲.md'), '# 第1章 甲')
            _write(os.path.join(d, '第01章_粗版.md'), '# 第1章 粗版')
            out = os.path.join(d, '总稿.md')
            _write(out, '原有总稿')
            with self.assertRaises(ValueError):
                merge_chapters(d, out)
            with open(out, encoding='utf-8') as f:
                self.assertEqual(f.read(), '原有总稿')

    def test_total_cannot_overwrite_source_chapter(self):
        with test_directory() as d:
            fp = os.path.join(d, '第1章.md')
            _write(fp, '源章')
            with self.assertRaises(ValueError):
                merge_chapters(d, fp)
            with open(fp, encoding='utf-8') as f:
                self.assertEqual(f.read(), '源章')


if __name__ == '__main__':
    unittest.main(verbosity=2)

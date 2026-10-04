# Final Examination Helper — AI Skill

**这是一个 AI Skill（技能包）**，用于把课程 PPT、指定课本和可选试卷、辅导书整理成逐章的凝练复习教材。

仓库名为 `final-examination-helper`，实际技能名为 **`exam-driven-notes-builder`**。技能入口是 [SKILL.md](skills/exam-driven-notes-builder/SKILL.md)。当前重点支持生物课程的机制展开、概念对比、知识联系与学习系统交接；其他学科使用用户提供的对应模板。

## 工作流程

```text
资料盘点与课程章节映射
          ↓
PPT + 可用老师试卷 / 往年卷：建立粗版
          ↓
可用辅导书：补机制、对比、例子与答题逻辑
          ↓
指定课本：逐节查漏、校准定义、补全与延伸
          ↓
逐章审校、保存进度、检查 Markdown
          ↓
合并约定范围，按需准备学习系统交接
```

稳定基础输入是 **PPT + 课本**。没有试卷或辅导书时跳过相应阶段，不伪造考题、不缩成只覆盖已考知识的清单。课件可以是 PPT 文件，也可以是图片式 PDF 和截图。

## 配套项目：课件收集助手

[NWAFU-zhi_hui_jiao_shi — 课件收集助手](https://github.com/tosamakamila/NWAFU-zhi_hui_jiao_shi)用于在 Windows 上从“智慧课堂”回放收集课件，按课程保存图片和 PDF。

收集好的课件可以作为本 Skill 的输入，再配合指定课本制作凝练复习教材。该工具负责上游课件收集，本 Skill 负责后续知识整理与审校；已有课件时可直接使用本 Skill，无需安装收集助手。具体使用方法以该项目 README 为准。

## 技能提供的能力

- 按老师课程大纲重组课本章节，逐章制作并支持中断续做。
- 生物主题内连续展开概念、机制、条件、对比、实验依据和理解延伸。
- 名词解释、核心知识、知识联系和原书课后题分区组织。
- 用户要求时可按章分配子代理；没有子代理工具时串行完成。
- 保留知识树、易错点和跨章联系，**不生成记忆口诀或押韵口号**。
- 资料提取、OCR、文本清理、分章、合并及格式检查的辅助脚本。
- 可选学习交接规则：名词转待审卡、主题切教学单元、原题单独使用，核对已有学习进度。

AI 负责阅读、理解、整合和科学审校；辅助脚本处理文件和确定性检查。使用此技能无需独立配置模型 API、服务地址或本地大语言模型。学习系统不是必需依赖，实际导入依用户请求及目标系统接口执行。

## 安装和使用

将 `skills/exam-driven-notes-builder/` **整个目录**复制到你的 AI 工具支持的技能目录，例如项目中的 `.agents/skills/`。保留目录内的 `references/`、`assets/` 和 `scripts/`，不要只复制 `SKILL.md`。

也可以让支持本地文件读取的 AI 直接读取该技能入口。

示例请求：

```text
使用 $exam-driven-notes-builder，为这门生物课逐章制作凝练教材。
课件：[PPT、课件PDF或截图路径]
指定课本：[路径、版本]
可选资料：[实际存在的试卷或辅导书，没有则省略]
课程范围：[老师大纲或需要制作的章节]
工作目录：[本次教材、缓存和输出所在目录]

按技能默认流程制作，保留机制展开、概念对比和跨章联系。
每章通过审校后保存并继续下一章，不生成口诀。
```

规则和工具相对于技能安装目录定位；课程资料与产物写入用户指定的工作目录。没有扫描资料时不用安装 OCR；只运行文本清理、分章、合并和格式检查时无需第三方 Python 包。

## 辅助工具

推荐使用 Python 3.12 或更新版本。以下示例在本仓库根目录执行；安装到其他位置时替换技能目录路径。

```text
# PDF文字提取、DOCX与PPTX解析依赖
python -m pip install -r skills/exam-driven-notes-builder/scripts/requirements.txt

# 需要扫描PDF或图片OCR时再安装
python -m pip install -r skills/exam-driven-notes-builder/scripts/requirements-ocr.txt

# 查看工具命令
python skills/exam-driven-notes-builder/scripts/tool.py --help

# 提取课件；输出目录自动创建
python skills/exam-driven-notes-builder/scripts/tool.py ppt "资料/课件.pptx" "缓存/课程/原始提取/P01.txt"

# 清理另存，保留原始提取
python skills/exam-driven-notes-builder/scripts/tool.py clean "缓存/课程/原始提取/P01.txt" -o "缓存/课程/清理后/P01.txt" -t ppt

# 本章格式检查
python skills/exam-driven-notes-builder/scripts/tool.py lint-notes "输出/课程/第1章_章节名.md"

# 按章号合并
python skills/exam-driven-notes-builder/scripts/tool.py merge "输出/课程"
```

旧 `.doc/.ppt` 依赖 Windows、Microsoft Office 和可选的 `requirements-legacy-office.txt`；优先提供 `.docx/.pptx`。GPU OCR 是可选优化，不是运行前提。

格式检查不能证明科学准确性或资料覆盖完整。还需按技能的覆盖表逐项核对原资料；学习导入成功也不能替代真实课堂效果验证。

## 仓库内容

```text
skills/exam-driven-notes-builder/
├── SKILL.md                 # 技能入口
├── agents/openai.yaml       # 技能显示信息
├── references/              # 格式、生物展开、流程、分工和学习交接
├── assets/                  # Markdown模板和可选预览样式
├── scripts/                 # 本流程需要的辅助工具及依赖清单
└── LICENSE
tests/                       # 辅助工具回归测试
```

本仓库只发布技能及必要支持文件。教材、课件、试卷、生成笔记、截图、缓存、学习状态、备份、个人配置和旧 API 引擎均不在发布内容中。

## 验证

```text
python -m unittest discover -s tests -v
```

测试覆盖来源位置保留、可选资料缺失、定义并入、教学单元结构、表格和围栏、连续修复、分章与安全合并。模板中的占位说明属于制作示例，生成成品时必须替换或删除。

本项目采用 [MIT License](LICENSE)。

## 联系方式

使用反馈、问题交流与改进建议可联系：**QQ：2381105138**。

## 免责声明

1. **学习辅助与内容核对**：本 Skill 提供资料整理和复习辅助流程。AI 生成、OCR 识别及自动提取可能出现错误、遗漏或不准确的推断；重要定义、机制、公式、数值及题目答案应与原始资料核对，不应将生成内容直接视为权威教材或教师的正式结论。
2. **考试结果**：本项目不保证覆盖全部考点，也不承诺押题、通过考试或取得特定成绩。课程要求和考试安排以学校、任课教师正式发布的信息为准。
3. **资料版权与使用权限**：课件、课本、试卷、辅导书及其他输入资料的权利属于各自权利人。请在获得相应权限的前提下使用，并遵守原始资料的授权条件与学校规定；未经许可，不应公开传播、售卖或重新发布受保护的资料。项目代码的 MIT 许可不自动授予第三方资料的使用权，生成内容中引用或改编原资料的部分仍需遵守相应授权。
4. **隐私与第三方服务**：在向 AI 平台或其他第三方服务提交资料前，请确认使用权限，并处理姓名、学号、成绩等个人信息。相关服务的隐私政策、收费规则与使用条款由其提供方制定，请自行确认。
5. **项目身份**：本项目由个人维护，与学校、任课教师、出版社及所链接的第三方服务不存在当然的官方隶属或背书关系。
6. **使用责任与许可**：本项目按现状提供，不对准确性、完整性、特定用途适用性或持续可用性作出保证。请备份原始资料、核对处理结果，并自行判断是否用于学习或其他场景；具体许可与免责条款以 [MIT License](LICENSE) 为准。

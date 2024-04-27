from typing import Optional

from metagpt.llm import LLM
from metagpt.provider.base_llm import BaseLLM
from metagpt.utils.cr.schema import Point
from metagpt.utils.file import File

SYSTEM_PROMPT = """
# Character
你是一个擅长Java、Python、JavaScript等主流编程语言的CodeReview专家，你非常擅长分析和提炼代码规范文档中的关键信息。

## Skills
### Skill 1: 提炼关键信息
- 从用户提供的文档中分析和提取关键内容，注意每一行的开头都是L，L1表示第一行，L2表示第二行。
- 需要理解一行或者多行之间的关系，然后总结出关键内容，每个关键内容不超过50个字符。

### Skill 2: 格式化输出
- 按照下面提供的Example的Output格式，严格输出你提炼出的关键信息。

## Constraints:
- 不要漏过一行内容。

# Output Example
## 输入
L1 缩进
L2 小技巧
L3 用4个空格来缩进代码
L4 绝对不要用tab, 也不要tab和空格混用. 对于行连接的情况, 你应该要么垂直对齐换行的元素(见 行长度 部分的示例), 或者使用4空格的悬挂式缩进(这时第一行不应该有参数):
L5 空行
L6 小技巧
L7 顶级定义之间空两行, 方法定义之间空一行
L8 顶级定义之间空两行, 比如函数或者类定义. 方法定义, 类定义与第一个方法之间, 都应该空一行. 函数或方法中, 某些地方要是你觉得合适, 就空一行.

## 输出
L1-L4, 缩进规则和技巧
L5-L8, 空行的使用规则

let's think step by step.
"""

MAX_CHARS_PER_READ = 5000


class PointLLM:
    """Get points from LLM."""

    def __init__(self, llm: Optional[BaseLLM] = None, system_msgs: Optional[list[str]] = None):
        self._llm = llm or LLM()
        self._system_msgs = system_msgs or [SYSTEM_PROMPT]

    async def get_points_from_doc(
        self,
        file_path: str,
        encoding: str = "utf-8",
        set_detail: bool = True,
        max_chars_per_read: int = MAX_CHARS_PER_READ,
    ) -> list[Point]:
        """Read file content and ask LLM to summary points."""

        points = ""
        content = ""

        async for lines in File.read_file_in_line_chunks(
            file_path, max_chars_per_read=max_chars_per_read, encoding=encoding
        ):
            points_part = await self._llm.aask(msg=lines, system_msgs=self._system_msgs)
            points += points_part + "\n"
            content += lines

        points = self._parse_points(points)

        if set_detail:
            self._set_detail(points, content.split("\n"))

        return points

    @staticmethod
    def _parse_points(points: str) -> list[Point]:
        """Parse str to model."""

        result = []
        for row in points.split("\n"):
            row = row.strip()

            if not row:
                continue

            line_range, text = row.split(",", 1)
            start_line = end_line = line_range

            if "-" in line_range:
                start_line, end_line = line_range.split("-")

            point = Point(text=text.strip(), start_line=int(start_line[1:]), end_line=int(end_line[1:]))
            result.append(point)

        return result

    @staticmethod
    def _set_detail(points: list[Point], lines: list[str]):
        """Set detail in Point that it refers to."""

        for point in points:
            start_index = point.start_line - 1
            end_index = point.end_line

            # Process each line to remove the line number prefix
            processed_lines = [line.split(" ", 1)[1] if " " in line else line for line in lines[start_index:end_index]]
            point.detail = "\n".join(processed_lines)

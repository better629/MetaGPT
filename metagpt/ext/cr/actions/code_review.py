#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import json

from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.utils.common import parse_json_code_block
from metagpt.utils.cr.cleaner import (
    add_line_num_on_patch,
    get_code_block_from_patch,
    rm_patch_useless_part,
)
from metagpt.utils.cr.schema import Point

CODE_REVIEW_PROMPT_TEMPLATE = """
NOTICE
With the given pull-request(PR) Patch, and referenced Points(Code Standards), you should compare each point with the code one-by-one.

The Patch code has added line no at the first character each line for reading, but the review should focus on new added code inside the `Patch` (lines starting with line no and '+').
Each point is start with a line no and follows with the point description.

## Patch
```
{patch}
```

## Points
{points}

## Output Format
```json
[
    {{
        "commented_file": "The file name which you give a comment from the patch",
        "comment": "The chinese comment of code which do not meet point description and give modify suggestions",
        "code_start_line": "the code start line no like `10` in the Patch of current comment",
        "code_end_line": "the code end line no like `15` in the Patch of current comment",
        "point_id": "The point id which the `comment` references to"
    }}
]
```

CodeReview guidelines:
- Generate code `comment` that do not meet the point description.
- Each `comment` should be restricted inside the `commented_file`
- Provide up to 15 comments of the patch code. Try to provide diverse and insightful comments across different `commented_file`.
- Don't suggest to add docstring unless it's necessary indeed.

Just print the PR Patch comments in json format like **Output Format**.
"""

CODE_REVIEW_COMFIRM_SYSTEM_PROMPT = """
You are a professional engineer with Python and Java stack, and good at code review comment result judgement.
"""

CODE_REVIEW_COMFIRM_TEMPLATE = """
## Code
```
{code}
```
## Comment
{comment}

## Point
{point}

With the PR code block, to think if the `comment` matches the description of the point.
Just print `True` if matches else `False`.
"""


class CodeReview(Action):
    name: str = "CodeReview"

    def format_comments(self, comments: list[dict], points: list[Point], patch: PatchSet):
        new_comments = []
        logger.debug(f"original comments: {comments}")
        for cmt in comments:
            for p in points:
                if int(cmt.get("point_id", -1)) == p.id:
                    code_start_line = cmt.get("code_start_line")
                    code_end_line = cmt.get("code_end_line")
                    code = get_code_block_from_patch(patch, code_start_line, code_end_line)
                    new_comments.append(
                        {
                            "commented_file": cmt.get("commented_file"),
                            "code": code,
                            "comment": cmt.get("comment"),
                            "point_id": p.id,
                            "point": p.text,
                            # "point_raw_cont": p.detail,
                        }
                    )
                    break

        logger.debug(f"new_comments: {new_comments}")
        return new_comments

    async def confirm_comments(self, comments: list[dict]) -> list[dict]:
        new_comments = []
        for cmt in comments:
            prompt = CODE_REVIEW_COMFIRM_TEMPLATE.format(
                code=cmt.get("code"), comment=cmt.get("comment"), point=cmt.get("point")
            )
            resp = await self.llm.aask(prompt, system_msgs=[CODE_REVIEW_COMFIRM_SYSTEM_PROMPT])
            if "True" in resp or "true" in resp:
                new_comments.append(cmt)
        logger.info(f"original comments num: {len(comments)}, confirmed comments num: {len(new_comments)}")
        return new_comments

    async def run(self, patch: PatchSet, points: list[Point]):
        patch: PatchSet = rm_patch_useless_part(patch)
        patch: PatchSet = add_line_num_on_patch(patch)
        logger.debug(f"patch with line no\n{str(patch)}")

        points_str = "\n".join([f"{p.id} {p.text}" for p in points])
        logger.info(f"\npoints_str: \n{points_str}")
        prompt = CODE_REVIEW_PROMPT_TEMPLATE.format(patch=str(patch), points=points_str)
        resp = await self.llm.aask(prompt)
        json_str = parse_json_code_block(resp)[0]
        comments = json.loads(json_str)

        comments = self.format_comments(comments, points, patch)

        comments = await self.confirm_comments(comments)

        logger.info(f"the comments of the PR:\n{comments}")
        return comments

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

import json

from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.utils.common import parse_json_code_block
from metagpt.utils.cr.cleaner import rm_patch_useless_part
from metagpt.utils.cr.schema import Point

CODE_REVIEW_PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer with Python and Java stack.
With the given pull-request(PR) Patch, and reference standard Points, you should give comments of the PR and output in json format.

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
        "commented_file": "The file name which you give comments from the patch",
        "comment": "The comment of the code",
        "code": "The code in the Patch which to be commented, three lines code before and after",
        "point_id": "The point id which the comment references to"
    }}
]
```

just print the PR Patch comments in json format like **Output Format**.
"""


CODE_REVIEW_COMFIRM_TEMPLATE = """
NOTICE
Role: You are a professional engineer with Python and Java stack.
With the PR code and its comment reference point, to judge if it's a valid comment.

## Code
```
{code}
```

## Point
{point}

## Comment
{comment}

just print True if it's a valid code comment with the point else False.
"""


class CodeReview(Action):
    name: str = "CodeReview"

    def format_comments(self, comments: list[dict], points: list[Point]):
        new_comments = []
        for cmt in comments:
            for p in points:
                if int(cmt.get("point_id", -1)) == p.id:
                    new_comments.append(
                        {
                            "commented_file": cmt.get("commented_file"),
                            "code": cmt.get("code"),
                            "comment": cmt.get("comment"),
                            "point": p.text,
                            "point_raw_cont": p.detail,
                        }
                    )
        return new_comments

    async def confirm_comments(self, comments: list[dict]) -> list[dict]:
        new_comments = []
        for cmt in comments:
            prompt = CODE_REVIEW_COMFIRM_TEMPLATE.format(
                code=cmt.get("code"), comment=cmt.get("comment"), point=cmt.get("point_raw_cont")
            )
            resp = await self.llm.aask(prompt)
            if "True" in resp or "true" in resp:
                new_comments.append(cmt)
        logger.info(f"original comments num: {len(comments)}, confirmed comments num: {len(new_comments)}")
        return new_comments

    async def run(self, patch: PatchSet, points: list[Point]):
        patch: PatchSet = rm_patch_useless_part(patch)

        points_str = "\n".join([f"{p.id} {p.text}" for p in points])
        prompt = CODE_REVIEW_PROMPT_TEMPLATE.format(patch=str(patch), points=points_str)
        resp = await self.llm.aask(prompt)
        json_str = parse_json_code_block(resp)[0]
        comments = json.loads(json_str)

        comments = self.format_comments(comments, points)

        comments = await self.confirm_comments(comments)

        logger.info(f"the comments of the PR:\n{comments}")
        return comments

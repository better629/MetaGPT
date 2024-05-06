#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : code review particular PR
#    step1, generate PR patch file with `git diff 5483cc6^..d0b00e3 > pr_1193_5483cc6-d0b00e3.patch
#    step2, run the code review script

"""
cd ./examples
python3 cr/point.py
python3 cr/code_review.py
"""

import asyncio

from unidiff import PatchSet

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.ext.cr.roles.code_reviewer import CodeReviewer, PatchPoints
from metagpt.schema import Message
from metagpt.tools.libs.cr import PointManager

INPUT_PATCH_FILE = EXAMPLE_DATA_PATH / "cr/mg_pr_1193_5483cc6-d0b00e3.patch"


async def main():
    # get points from existed result
    p = PointManager()
    points = await p.get_points()

    patch: PatchSet = PatchSet(INPUT_PATCH_FILE.read_text())

    crer = CodeReviewer()
    await crer.run(Message(content="code review on PR patch", instruct_content=PatchPoints(patch=patch, points=points)))


if __name__ == "__main__":
    asyncio.run(main())

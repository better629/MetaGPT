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
import json
from datetime import datetime

from unidiff import PatchSet

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.ext.cr.roles.code_reviewer import CodeReviewer, PatchPoints
from metagpt.schema import Message
from metagpt.tools.libs.cr import PointManager

INPUT_PATCH_FILE = EXAMPLE_DATA_PATH / "cr/6.patch"
patch_file_name = "6"

async def main():
    # get points from existed result
    p = PointManager()
    points = await p.get_points()

    patch: PatchSet = PatchSet(INPUT_PATCH_FILE.read_text(encoding='utf-8'))

    crer = CodeReviewer()
    msg = await crer.run(Message(content="code review on PR patch", instruct_content=PatchPoints(patch=patch, points=points)))
    with open(f'CR-{patch_file_name}-{datetime.timestamp(datetime.now())}-result.json', 'w', encoding='utf-8') as file:
        file.writelines(json.dumps(msg.instruct_content.cr_comments, ensure_ascii=False))
    return msg

if __name__ == "__main__":
    asyncio.run(main())

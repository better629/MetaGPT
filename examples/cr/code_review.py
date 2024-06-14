#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : code review particular PR
#    step1, generate PR patch file with `git diff 5483cc6^..d0b00e3 > pr_1193_5483cc6-d0b00e3
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

patch_list = ['10001']

# patch_list = ['3004', '2805', '18785', '18509', '16834', '35', '1017', '1262', '11537', '10001', '12891', '10905', '819', '800', '621']
# patch_list = ['1', '2', '3', '4', '5', '6', '7', '8', '14', '99', '356', '812', '1000', '1090', '2723']


async def main():
    # get points from existed result
    p = PointManager()
    points = await p.get_points()
    for patch_no in patch_list:
        input_patch_file = EXAMPLE_DATA_PATH / f"cr/{patch_no}.patch"
        patch: PatchSet = PatchSet(input_patch_file.read_text(encoding='utf-8'))

        code_reviewer = CodeReviewer(pr=patch_no, mode=0, calculate_type="")
        await code_reviewer.run(Message(content="code review on PR patch", instruct_content=PatchPoints(patch=patch, points=points)))

    print("CR执行完毕，请检查输出文件")
if __name__ == "__main__":
    asyncio.run(main())

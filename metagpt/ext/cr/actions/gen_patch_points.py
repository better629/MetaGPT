#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : extract points from patch firstly or use the passed whole points


from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.utils.cr.schema import Point

EXTRACT_PROMPT = """
"""


class GenPatchPoints(Action):
    name: str = "PatchPoints"

    async def run(self, patch: PatchSet, points: list[Point], do_extract: bool = False) -> list[Point]:
        if not do_extract:
            # do the points extraction from the patch and then find the matched point from the points through RAG
            pass

        return points

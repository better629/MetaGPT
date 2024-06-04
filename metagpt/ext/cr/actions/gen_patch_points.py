#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : extract points from patch firstly or use the passed whole points

import json

from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.rag.engines.simple import SimpleEngine
from metagpt.rag.schema import FAISSRetrieverConfig
from metagpt.utils.common import parse_json_code_block
from metagpt.utils.cr.cleaner import rm_patch_useless_part
from metagpt.utils.cr.schema import Point

EXTRACT_COMMENTS_PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer with Python and Java stack.
With the given pull-request(PR) Patch, try to do the code review and print the comments.

## Patch
```
{patch}
```

## Output Format
```json
["comment_1", "comment_2", "comment_n]
```

output the comments in json format with list of str.
"""


SELECT_POINTS_PROMPT_TEMPLATE = """
With the given pull-request(PR) Patch, and referenced standard Points(Code Standards).
You should do the code review line-by-line, and check the points related to the problem code.

## Patch
```
{patch}
```

## Points
{points}

## Output Format
```json
[point_id0, point_idi, point_idn]
```

Output the point id list like **Output Format** which are probable related to the Patch code review result.
"""


class GenPatchPoints(Action):
    name: str = "PatchPoints"

    async def extract_patch_comments(self, patch: PatchSet, points: list[Point]) -> list[Point]:
        # do the comments extraction from the patch and then find the matched point from the points through RAG
        prompt = EXTRACT_COMMENTS_PROMPT_TEMPLATE.format(patch=str(patch))
        resp = await self.llm.aask(prompt)
        json_str = parse_json_code_block(resp)[0]
        comments = json.loads(json_str)

        # create retrieval engine
        engine = SimpleEngine.from_objs(
            points,
            retriever_configs=[FAISSRetrieverConfig(similarity_top_k=2)],
            # ranker_configs=[LLMRankerConfig()]
        )
        points_map = {}
        retri_cnt = 0
        for cmt in comments:
            nodes = await engine.aretrieve(query=cmt)
            for node in nodes:
                retri_cnt += 1
                point = node.metadata["obj"]
                points_map[point.id] = point
        points = list(points_map.values())
        points_str = "\n".join([f"{p.id} {p.text}" for p in points])
        logger.debug(f"retrieved points: {points_str}")
        logger.info(f"retrieved num: {retri_cnt}, merged num: {len(points)}")
        return points

    async def select_patch_points(self, patch: PatchSet, points: list[Point]) -> list[Point]:
        # do the points selection according to the patch
        point_ids = set()
        points_str = "\n".join([f"{p.id} {p.text}" for p in points])
        for patched_file in patch:
            prompt = SELECT_POINTS_PROMPT_TEMPLATE.format(patch=str(patched_file), points=points_str)
            resp = await self.llm.aask(prompt)
            json_str = parse_json_code_block(resp)[0]
            patched_file_point_ids = json.loads(json_str)
            if len(patched_file_point_ids) != 0:
                point_ids.update(patched_file_point_ids)

        new_points = []
        for point in points:
            if point.id in point_ids:
                new_points.append(point)
        return new_points

    async def run(self, patch: PatchSet, points: list[Point], do_extract: bool = True) -> list[Point]:
        # if do_extract:
        #     patch: PatchSet = rm_patch_useless_part(patch)
        #
        #     points = await self.select_patch_points(patch, points)

        return points

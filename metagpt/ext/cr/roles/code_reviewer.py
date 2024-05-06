#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : PR code review agent

from typing import Optional

from pydantic import BaseModel, ConfigDict
from unidiff import PatchSet

from metagpt.ext.cr.actions.code_review import CodeReview
from metagpt.ext.cr.actions.gen_patch_points import GenPatchPoints
from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.utils.cr.schema import Point


class PatchPoints(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    patch: Optional[PatchSet] = None
    points: list[Point] = []


class CRComments(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    cr_comments: list[dict] = []


class CodeReviewer(Role):
    name: str = "Jones"
    profile: str = "CodeReviewer"
    goal: str = "find potential mistakes or bugs from the code and then give comments"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_actions([GenPatchPoints, CodeReview])
        self._set_react_mode(RoleReactMode.BY_ORDER)

    async def _act(self) -> Message:
        msg = self.rc.memory.get(k=1)[0]
        todo = self.rc.todo
        if isinstance(todo, GenPatchPoints):
            patch_points = msg.instruct_content
            points = await todo.run(patch=patch_points.patch, points=patch_points.points)
            patch_points.points = points
            ic = patch_points
        elif isinstance(todo, CodeReview):
            patch_points = msg.instruct_content
            cr_comments = await todo.run(patch=patch_points.patch, points=patch_points.points)
            ic = CRComments(cr_comments=cr_comments)

        msg = Message(content=msg.content, instruct_content=ic)
        self.rc.memory.add(msg)
        return msg

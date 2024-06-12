#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : PR code modify agent

from typing import Optional

from pydantic import BaseModel, ConfigDict
from unidiff import PatchSet

from metagpt.roles.role import Role, RoleReactMode
from metagpt.schema import Message
from metagpt.ext.cr.actions.modify_code import ModifyCode


class PatchComments(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    patch: Optional[PatchSet] = None
    comments: list = []


class ModifyCoder(Role):
    name: str = "Jones"
    profile: str = "Modify-Coder"
    goal: str = "create Git patches to represent code modifications"
    pr: str = ""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([ModifyCode(pr=self.pr)])
        self._set_react_mode(RoleReactMode.BY_ORDER)

    async def _act(self) -> Message:
        msg = self.rc.memory.get(k=1)[0]
        todo = self.rc.todo
        if isinstance(todo, ModifyCode):
            patch_comments = msg.instruct_content
            await todo.run(patch=patch_comments.patch, comments=patch_comments.comments)

        msg = Message(content=f"PR-{self.pr}-已经输出修复文件")
        return msg

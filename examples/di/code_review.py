#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :

from pathlib import Path

import fire

from metagpt.roles.di.data_interpreter import DataInterpreter


async def main():
    di = DataInterpreter(tools=["PointManager", "CodeReviewer"])
    example_di_path = Path(__file__).parents[1]
    pr_file_path = example_di_path.joinpath("data/cr/mg_pr_1193_5483cc6-d0b00e3_small.patch").as_posix()
    standford_file_path = example_di_path.joinpath("data/cr/python_style.txt").as_posix()
    requirement = (
        f"load the standard point file `{standford_file_path}` and "
        f"do a code review on PR `{pr_file_path}` straightforwardly"
    )
    await di.run(requirement)


if __name__ == "__main__":
    fire.Fire(main)

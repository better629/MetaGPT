import asyncio

from unidiff import PatchSet

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.ext.cr.actions.summarize_patch import SummarizePatch

INPUT_PATCH_FILE = EXAMPLE_DATA_PATH / "cr/alvinc16-spring-petclinic-PR1.patch"


async def main():
    todo = SummarizePatch()
    patch = PatchSet(INPUT_PATCH_FILE.read_text())

    await todo.run(patch)


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import json

from unidiff import PatchSet

from metagpt.const import EXAMPLE_DATA_PATH, METAGPT_ROOT
from metagpt.ext.cr.roles.modify_code import ModifyCoder, PatchComments
from metagpt.schema import Message

patch_list = ['1']
# patch_list = ['1', '2', '3', '4', '5', '6', '7', '8', '14', '99', '356', '812', '1000', '1090', '2723']


async def main():
    for patch_no in patch_list:
        input_patch_file = EXAMPLE_DATA_PATH / f"cr/{patch_no}.patch"
        input_comments_file = EXAMPLE_DATA_PATH / f"modify_code/CR-{patch_no}-result.json"
        comments = json.loads(input_comments_file.read_text(encoding='utf-8'))
        patch = PatchSet(input_patch_file.read_text(encoding='utf-8'))

        modify_coder = ModifyCoder(pr=patch_no)
        await modify_coder.run(Message(content="code review on PR patch", instruct_content=PatchComments(patch=patch, comments=comments)))

if __name__ == "__main__":
    asyncio.run(main())

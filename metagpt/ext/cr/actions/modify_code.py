from unidiff import PatchSet

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.utils.cr.cleaner import add_line_num_on_patch, rm_patch_useless_part

MODIFY_CODE_PROMPT = """
NOTICE
With the given pull-request(PR) Patch, and referenced Comments(Code Standards), you should modify the code according the Comments.

The Patch code has added line no at the first character each line for reading, but the modification should focus on new added code inside the `Patch` (lines starting with line no and '+').

## Patch
```
{patch}
```

## Comments
{comments}

## Output Format
<the standard git patch>


Code Modification guidelines:
- Use `code_start_line` and `code_end_line` to locate the problematic code, fix the code by `comment` and `point_detail`.
- Create a patch that satifies the git patch standard.
- Do not print line no in the new patch code.

Just print the Patch in the format like **Output Format**.
"""


class ModifyCode(Action):
    name: str = "Modify Code"

    async def run(self, patch: PatchSet, comments: list[dict]) -> str:
        patch: PatchSet = rm_patch_useless_part(patch)
        patch: PatchSet = add_line_num_on_patch(patch)
        logger.debug(f"patch with line no\n{str(patch)}")

        resp = await self.llm.aask(
            MODIFY_CODE_PROMPT.format(patch=patch, comments=comments),
            system_msgs=[
                "You're an adaptive software developer who excels at refining code based on user inputs. You're proficient in creating Git patches to represent code modifications."
            ],
        )
        return resp

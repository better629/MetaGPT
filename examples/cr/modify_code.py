import asyncio

from unidiff import PatchSet

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.ext.cr.actions.modify_code import ModifyCode

INPUT_PATCH_FILE = EXAMPLE_DATA_PATH / "cr/alvinc16-spring-petclinic-PR1.patch"


COMMENTS = [
    {
        "code": '+\t\tSystem.out.println("Initializing new owner form.");',
        "code_end_line": "4",
        "code_start_line": "4",
        "comment": "不要使用 System.out.println 去打印，应使用日志系统来记录信息。",
        "commented_file": "OwnerController.java",
        "point": "不要使用 System.out.println 去打印",
        "point_detail": "缺陷类型：不要使用 System.out.println 去打印；修复方案：删除 System.out.println 语句",
    },
    {
        "code": '+\t\tString unusedVar = "This variable is not used";',
        "code_end_line": "11",
        "code_start_line": "11",
        "comment": "避免未使用的临时变量，此变量未在后续代码中使用。",
        "commented_file": "OwnerController.java",
        "point": "避免未使用的临时变量",
        "point_detail": "缺陷类型：避免未使用的临时变量；修复方案：删除未使用的临时变量",
    },
    {
        "code": "+\t\ttry {\n"
        "+\t\t\tOwner owner = this.owners.findById(ownerId);\n"
        "+\t\t\tmodel.addAttribute(owner);\n"
        "+\t\t\treturn VIEWS_OWNER_CREATE_OR_UPDATE_FORM;\n"
        "+\t\t} catch (Exception e) {\n"
        "+\n"
        "+\t\t}",
        "code_end_line": "27",
        "code_start_line": "21",
        "comment": "try 语句块不能为空，应包含逻辑代码。",
        "commented_file": "OwnerController.java",
        "point": "try 语句块不能为空",
        "point_detail": "缺陷类型：try 语句块不能为空；对应Fixer：EmptyTryBlockFixer；修复方案：删除整个 try 语句",
    },
]


async def main():
    todo = ModifyCode()
    patch = PatchSet(INPUT_PATCH_FILE.read_text())

    await todo.run(patch, COMMENTS)


if __name__ == "__main__":
    asyncio.run(main())

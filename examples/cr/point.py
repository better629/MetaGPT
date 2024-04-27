import asyncio

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.tools.libs.cr import PointManager
from metagpt.utils.cr.database import create_tables

INPUT_FILE = EXAMPLE_DATA_PATH / "cr/python_style.txt"


async def main():
    # 1. create db
    await create_tables()

    # 2. create points and save to db
    p = PointManager()
    await p.create_points_from_doc(input_file=INPUT_FILE)

    # 3. get points
    points = await p.get_points()
    print(points)


if __name__ == "__main__":
    asyncio.run(main())

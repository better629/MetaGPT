import asyncio

from metagpt.const import EXAMPLE_DATA_PATH
from metagpt.tools.libs.cr import PointManager
from metagpt.utils.cr.database import create_tables

INPUT_FILE = EXAMPLE_DATA_PATH / "cr/python_style.txt"


def print_points(points):
    print("id | text\t | start_line\t | end_line\t | detail")
    for point in points:
        detail = point.detail.replace("\n", " ")
        print(f"{point.id} | {point.text[:20]}\t | {point.start_line}\t | {point.end_line}\t | {detail[:30]}")


async def main():
    # 1. create db
    await create_tables()

    # 2. create points and save to db
    p = PointManager()
    await p.create_points_from_doc(input_file=INPUT_FILE)

    # 3. get points
    points = await p.get_points()
    print_points(points)


if __name__ == "__main__":
    asyncio.run(main())

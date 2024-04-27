from metagpt.tools.tool_registry import register_tool
from metagpt.utils.cr.cleaner import clean_and_mark_file
from metagpt.utils.cr.database import PointDAO
from metagpt.utils.cr.llm import PointLLM
from metagpt.utils.cr.schema import Point


@register_tool(
    tags=["codereview"],
    include_functions=["create_points_from_doc", "get_points", "get_points_by_ids"],
)
class PointManager:
    """Manage points."""

    def __init__(self):
        self._dao = PointDAO()
        self._llm = PointLLM()

    async def create_points_from_doc(self, input_file: str):
        """Create points from doc.

        Clean file and get points from llm, then save points to db.

        Args:
            input_file: Path to the file.
        """

        output_file = await clean_and_mark_file(input_file)

        points = await self._llm.get_points_from_doc(output_file)
        self._set_file_path(points, input_file)

        await self.create_points(points)

    async def create_points(self, points: list[Point]):
        """Save points to db.

        Args:
            points: List of Point.
        """

        rows = [point.model_dump(exclude="id") for point in points]
        await self._dao.create(rows)

    async def get_points(self, fields: list[str] = None) -> list[Point]:
        """Get points from db."""

        points = await self._dao.query(fields=fields)
        return [Point(**p) for p in points]

    async def get_points_by_ids(self, ids: list[int]) -> list[Point]:
        """Get points from db by ids.

        Args:
            ids: IDs of Points.
        """

        points = await self._dao.query_by_ids(ids=ids)
        return [Point(**p) for p in points]

    def _set_file_path(self, points: list[Point], file_path: str):
        for point in points:
            point.file_path = str(file_path)

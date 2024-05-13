from pathlib import Path

from unidiff import PatchSet

from metagpt.tools.tool_registry import register_tool
from metagpt.utils.cr.cleaner import clean_and_mark_file
from metagpt.utils.cr.database import PointDAO
from metagpt.utils.cr.schema import Point


@register_tool(
    tags=["codereview"],
    include_functions=["create_points_from_doc", "get_points", "get_points_by_ids"],
)
class PointManager:
    """Generate points from standard point file"""

    def __init__(self):
        from metagpt.utils.cr.llm import PointLLM

        self._dao = PointDAO()
        self._llm = PointLLM()

    async def create_points_from_doc(self, input_file: str):
        """Create points from standard point file.

        Clean file and get points from standard point file with llm, then save points to db.

        Args:
            input_file: Path to the standard point file.

        Returns:
            None
        """

        output_file = await clean_and_mark_file(input_file)

        points = await self._llm.get_points_from_doc(output_file)
        self._set_file_path(points, input_file)

        await self.create_points(points)

    async def create_points(self, points: list[Point]):
        """Save points to db.

        Args:
            points: List of Point.

        Returns:
            None
        """

        rows = [point.model_dump(exclude="id") for point in points]
        await self._dao.create(rows)

    async def get_points(self, fields: list[str] = None) -> list[Point]:
        """Get points from generated result

        Args:
            fields: points fields to filter, default None

        Returns:
            list[Point]: list of fetched points
        """

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


@register_tool(tags=["codereview"], include_functions=["run"])
class CodeReviewer:
    """Do the CodeReview of a PR patch"""

    async def run(self, patch_file_path: str, points: list[Point]) -> list[dict]:
        """Run the code review
        Read the patch file, and then do the code review with the points
        Args:
            patch_file_path: Path to the patch file
            points: list of Points generate from standard point file or load from generated result

        Returns
            list[dict]: list of code review comments, the comment is dict type, and keys of the comment are `commented_file`, `code`, `comment`, `point_id`, `point`.
        """
        from metagpt.ext.cr.actions.code_review import CodeReview
        from metagpt.ext.cr.actions.gen_patch_points import GenPatchPoints

        patch: PatchSet = PatchSet(Path(patch_file_path).read_text())

        gen_patch_points = GenPatchPoints()
        points = await gen_patch_points.run(patch, points)

        code_review = CodeReview()
        comments = await code_review.run(patch, points)

        return comments

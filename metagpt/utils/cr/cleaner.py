"""Cleaner."""

import tempfile

import aiofiles

from metagpt.logs import logger


class FileCleaner:
    @classmethod
    async def clean_and_mark_file(cls, input_file: str, output_file: str = "", encoding: str = "utf-8") -> str:
        """Clean file, to make LLM better understand the content.

        Create a temporary file if no output file is provided.
        """
        output_file = cls._ensure_output_file(output_file)
        await cls._clean_and_mark_file(input_file, output_file, encoding)

        return output_file

    @classmethod
    async def _clean_and_mark_file(cls, input_file: str, output_file: str, encoding: str):
        async with aiofiles.open(input_file, "r", encoding=encoding) as infile, aiofiles.open(
            output_file, "w", encoding=encoding
        ) as outfile:
            line_number = 1
            async for line in infile:
                # remove empty line and mark line numbers before each line, such as L1, L2, ...
                if line.strip():
                    await outfile.write(f"L{line_number} {line}")
                    line_number += 1

        logger.info(f"clean and mark file success, input_file: {input_file}, output_file: {output_file}")

    @classmethod
    def _ensure_output_file(cls, output_file: str) -> str:
        if not output_file:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                output_file = temp_file.name

        return output_file


clean_and_mark_file = FileCleaner.clean_and_mark_file

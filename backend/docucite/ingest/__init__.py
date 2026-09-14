"""Parse PDF, Word, and Markdown into text and tables."""

from .parsers import parse_document

__all__ = ["parse_document"]

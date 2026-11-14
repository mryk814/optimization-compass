"""Tests of the lesson figures, one file per module of scripts/lesson_figures."""

import pytest

# The shared article helpers assert; rewrite them like test modules so a failure shows the diff.
pytest.register_assert_rewrite(f"{__name__}.article_python")

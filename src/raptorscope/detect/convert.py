# SPDX-License-Identifier: GPL-3.0-or-later
"""Convert a Sigma rule to an Elastic (Lucene) query via pysigma."""
from pathlib import Path

from sigma.backends.elasticsearch import LuceneBackend
from sigma.collection import SigmaCollection


def convert_rule(path: str) -> str:
    """Return the Lucene query string for the Sigma rule at ``path``."""
    col = SigmaCollection.from_yaml(Path(path).read_text())
    return LuceneBackend().convert(col)[0]

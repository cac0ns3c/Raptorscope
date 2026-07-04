# SPDX-License-Identifier: GPL-3.0-or-later
"""ES-native detection: run the Sigma rules as Lucene queries against ES.

This is the scale path — instead of pulling every case doc into memory and
evaluating rules in-process (``evaluate.run_rules``), it pushes each rule's
generated Lucene query to Elasticsearch and reads back the matches. It emits the
**same alert shape** as ``run_rules`` (rule_id/title/level/dataset/doc_id/
evidence), so the API is identical regardless of engine.

**Parity requires the right field types.** The in-process evaluator does
case-sensitive *substring* matching; that only agrees with ES wildcard queries
when the matched field is a `keyword`/`wildcard` type, not an analyzed `text`
field. ``process.command_line`` is therefore mapped as `wildcard` (see
``es.template``). With that in place the two engines produce identical alerts —
verified by ``tests/detect/test_es_detector_parity.py`` against a live index.
"""
import glob

import yaml

from ..es.store import ESStore
from .convert import convert_rule
from .evaluate import Rule, _evidence, _rule_datasets


def _dataset_of(src: dict):
    return (src.get("event") or {}).get("dataset")


class ESDetector:
    def __init__(
        self,
        client,
        rules_dir: str = "detections/sigma",
        index_pattern: str = "raptorscope-*",
    ):
        self._client = client
        self._pattern = index_pattern
        # Compile (Rule, lucene) once at construction — rules don't change per run.
        self._compiled: list[tuple[Rule, str]] = []
        for path in sorted(glob.glob(f"{rules_dir}/*.yml")):
            doc = yaml.safe_load(open(path))
            detection = doc.get("detection", {})
            rule = Rule(
                id=doc.get("id"),
                title=doc.get("title"),
                level=doc.get("level", "informational"),
                tags=doc.get("tags", []),
                datasets=_rule_datasets(detection),
                detection=detection,
            )
            self._compiled.append((rule, convert_rule(path)))

    def run(self, host: str | None = None) -> list[dict]:
        """Return one alert per (rule, matching doc), same shape as run_rules."""
        alerts: list[dict] = []
        for rule, lucene in self._compiled:
            filters: list = [{"query_string": {"query": lucene}}]
            if host is not None:
                filters.append({"term": {"host.name": host}})
            resp = self._client.search(
                index=self._pattern,
                size=ESStore.MAX_WINDOW,
                query={"bool": {"filter": filters}},
            )
            for h in resp["hits"]["hits"]:
                src = dict(h.get("_source") or {})
                alerts.append(
                    {
                        "rule_id": rule.id,
                        "title": rule.title,
                        "level": rule.level,
                        "dataset": _dataset_of(src),
                        "doc_id": h.get("_id"),
                        "evidence": _evidence(src, rule.detection),
                    }
                )
        return alerts

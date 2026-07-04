# SPDX-License-Identifier: GPL-3.0-or-later
"""Elasticsearch index template for raptorscope ECS documents."""

INDEX_PATTERN = "raptorscope-*"

INDEX_TEMPLATE = {
    "index_patterns": [INDEX_PATTERN],
    "template": {
        "mappings": {
            "dynamic": True,
            "properties": {
                "@timestamp": {"type": "date"},
                "event": {
                    "properties": {
                        "kind": {"type": "keyword"},
                        "module": {"type": "keyword"},
                        "dataset": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "type": {"type": "keyword"},
                    }
                },
                "host": {
                    "properties": {
                        "name": {"type": "keyword"},
                        "os": {"properties": {"type": {"type": "keyword"}}},
                    }
                },
                "file": {
                    "properties": {
                        "path": {"type": "keyword"},
                        "name": {"type": "keyword"},
                    }
                },
                "process": {
                    "properties": {
                        "executable": {"type": "keyword"},
                        "command_line": {"type": "text"},
                        "code_signature": {
                            "properties": {
                                "exists": {"type": "boolean"},
                                "subject_name": {"type": "keyword"},
                                "trusted": {"type": "boolean"},
                            }
                        },
                    }
                },
                "raptorscope": {
                    "properties": {
                        "persistence": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "label": {"type": "keyword"},
                                "run_at_load": {"type": "boolean"},
                            }
                        }
                    }
                },
            },
        }
    },
}

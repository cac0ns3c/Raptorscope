# SPDX-License-Identifier: GPL-3.0-or-later
"""Elasticsearch index template for raptorscope ECS documents."""

INDEX_PATTERN = "raptorscope-*"


def put_index_template(client, name: str = "raptorscope") -> None:
    """Install the raptorscope ECS index template so ``raptorscope-*`` indices
    get correctly-typed fields (keyword/date/boolean) instead of dynamic guesses."""
    client.indices.put_index_template(
        name=name,
        index_patterns=INDEX_TEMPLATE["index_patterns"],
        template=INDEX_TEMPLATE["template"],
    )

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
                "user": {"properties": {"name": {"type": "keyword"}}},
                "url": {
                    "properties": {
                        "full": {"type": "keyword"},
                        "original": {"type": "keyword"},
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
                        "pid": {"type": "long"},
                        "name": {"type": "keyword"},
                        "executable": {"type": "keyword"},
                        # `wildcard` (not `text`) so Sigma `|contains` wildcard
                        # queries do true substring matching, matching the
                        # in-process evaluator. See detect/es_detector.py.
                        "command_line": {"type": "wildcard"},
                        "parent": {"properties": {"pid": {"type": "long"}}},
                        "code_signature": {
                            "properties": {
                                "exists": {"type": "boolean"},
                                "subject_name": {"type": "keyword"},
                                "trusted": {"type": "boolean"},
                            }
                        },
                    }
                },
                "source": {
                    "properties": {"ip": {"type": "ip"}, "port": {"type": "long"}}
                },
                "destination": {
                    "properties": {
                        "ip": {"type": "ip"},
                        "address": {"type": "keyword"},
                        "port": {"type": "long"},
                    }
                },
                "network": {
                    "properties": {
                        "transport": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "direction": {"type": "keyword"},
                    }
                },
                "raptorscope": {
                    "properties": {
                        "network": {"properties": {"state": {"type": "keyword"}}},
                        "persistence": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "label": {"type": "keyword"},
                                "run_at_load": {"type": "boolean"},
                                "hidden": {"type": "boolean"},
                                "schedule": {"type": "keyword"},
                                "payload_type": {"type": "keyword"},
                                "signed": {"type": "boolean"},
                                "btm_type": {"type": "keyword"},
                                "developer": {"type": "keyword"},
                                "uuid": {"type": "keyword"},
                            }
                        },
                        "quarantine": {
                            "properties": {"sender": {"type": "keyword"}}
                        },
                        "tcc": {
                            "properties": {
                                "service": {"type": "keyword"},
                                "client": {"type": "keyword"},
                                "client_type": {"type": "keyword"},
                                "allowed": {"type": "boolean"},
                            }
                        },
                        "app": {
                            "properties": {
                                "name": {"type": "keyword"},
                                "bundle_id": {"type": "keyword"},
                                "version": {"type": "keyword"},
                                "signed": {"type": "boolean"},
                            }
                        },
                    }
                },
            },
        }
    },
}

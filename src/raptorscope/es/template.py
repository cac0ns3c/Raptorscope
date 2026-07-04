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
                        "command_line": {"type": "text"},
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
                "raptorscope": {
                    "properties": {
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

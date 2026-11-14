# Historical alternative, not the current port candidate

`source/source_jiggle_metadata.py` and its25/26case CPU results are the earlier sidecar/pending-publication exploration. Root explicitly chose the smaller inline-or-explicit-omission contract. Keep those files and `before-publication-confirm-guard` as evidence; do not port them.

Independent review also found two unresolved defects in that historical version: retained source identity was checked after oversized/unserializable-base fallback, and malformed inner artifact receipts could raise AttributeError. Those findings are retained in `review/adapter-review-initial.json`. The minimal candidate checks identity before all optional budget handling and has no artifact receipt API. Passing historical tests did not establish those untested edge cases or any real native fit/adoption.

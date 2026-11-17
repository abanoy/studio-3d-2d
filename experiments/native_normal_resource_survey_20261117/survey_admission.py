"""Explicit missing admission boundary. This preparation must never launch natively."""

class Unstageable(RuntimeError):
    pass


def require_native_survey_admission():
    # Root must review a successor with a concrete current full-context/closed-
    # lane adapter and qualified known-B load dependency policy. A caller flag,
    # old157→new158 schema alias or fabricated empty resource inventory is not proof.
    raise Unstageable('SOURCE_ONLY: concrete current context and known-B load admission are not supplied')

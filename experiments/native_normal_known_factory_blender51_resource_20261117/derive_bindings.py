"""Pure two-literal survey binding; no runtime/native input access."""
import hashlib

PARENT_INDEX = '1eeca1e85d93c834c52c1208ed68d18aaa2b00bc1b62987cf0b89d5561ab6f90'
PARENT_SUPPORT = '2587a5168735ecf6b38dabe8ca00415d3fa35a167f3ed508aded87db5ff0ed1a'
SURVEY_INDEX = '9f8e24d0053d920dcdb7a5f5560a37ee0b493aa63351dc95e478435e95685369'
RULES = (
    (b"SURVEY = ROOT / 'experiments/native_normal_resource_survey_20261117'",
     b"SURVEY = ROOT / 'experiments/native_normal_blender51_resource_api_fix_20261117'"),
    (b"SURVEY_SHA = 'b6069eb8c87d7599d10165de987ab2d9924fb377890e12a4cb2f0bdaf9ab735c'",
     ("SURVEY_SHA = '" + SURVEY_INDEX + "'").encode()),
)


def render(raw):
    if hashlib.sha256(raw).hexdigest() != PARENT_SUPPORT: raise ValueError('exact parent support required')
    result = raw
    for old, new in RULES:
        if result.count(old) != 1: raise ValueError('unique binding literal required')
        result = result.replace(old, new, 1)
    inverse = result
    for old, new in reversed(RULES):
        if inverse.count(new) != 1: raise ValueError('unique inverse required')
        inverse = inverse.replace(new, old, 1)
    if inverse != raw: raise ValueError('whole support byte inverse differs')
    compile(result, 'diagnostic_support.py', 'exec')
    return result

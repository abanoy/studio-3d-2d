"""Output-only three-boundary amendment; old candidate remains untouched."""
from pathlib import Path
import hashlib,json,shutil
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
OLD=ROOT/'experiments/source_appearance/native_jiggle_main_plan_20261113/minimal-source'
SOURCE=BASE/'source';SOURCE.mkdir(exist_ok=False)
HISTORY=BASE/'old-context';HISTORY.mkdir(exist_ok=False)
names=('source_jiggle_metadata.py','source_jiggle_values.py','test_source_jiggle_metadata.py','authored_fixture.py')
before={name:hashlib.sha256((OLD/name).read_bytes()).hexdigest() for name in names}
for name in names:
    shutil.copy2(OLD/name,HISTORY/name);shutil.copy2(OLD/name,SOURCE/name)

path=SOURCE/'source_jiggle_metadata.py';text=path.read_text(encoding='utf-8')
def change(old,new):
    global text
    assert text.count(old)==1,(old,text.count(old))
    text=text.replace(old,new)
change('def _compact(value):', '''def _name_in_budget(value):
    if type(value) is not str: return False
    try: return len(value.encode("utf-8")) <= 256
    except UnicodeError: return False

def _compact(value):''')
change('and type(row["name"]) is str and len(row["name"].encode("utf-8")) <= 256 and type(row["parent"]) is int for row in native_bones)',
       'and _name_in_budget(row["name"]) and type(row["parent"]) is int for row in native_bones)')
change('if type(native_bones) is not list or len(native_bones) != metadata["native_bone_count"]: raise ValueError("Native bone catalogue domain differs")',
       '''if type(metadata.get("source_scale")) not in (int, float) or not math.isfinite(metadata["source_scale"]) or not 0 < metadata["source_scale"] <= 1e6:
        raise ValueError("Invalid finite numeric native metadata scale")
    if type(native_bones) is not list or len(native_bones) != metadata["native_bone_count"]: raise ValueError("Native bone catalogue domain differs")''')
change('or type(row.get("native_bone_name")) is not str or len(row["native_bone_name"].encode("utf-8")) > 256:',
       'or not _name_in_budget(row.get("native_bone_name")):')
change('def plan_report(base_report, inspection, newline="\\n"):',
       'def plan_report(base_report, inspection, newline="\\n", *, expected_native_mdl_sha256=None):')
change('Original/native source checks precede every optional serialization/budget gate.',
       '''Original/native source checks precede every optional serialization/budget gate.
    Nonempty inspections require expected_native_mdl_sha256 from the caller's
    independently frozen selected-MDL context, never from inspection metadata.
    No-rule/BSP no-op state publishes no new data and keeps its original writer.''')
change('''    else:
        raise ValueError("Unexpected optional metadata inspection state")
    try:
        base_bytes = report_bytes(base, newline)''',
       '''    else:
        raise ValueError("Unexpected optional metadata inspection state")
    if not _sha(expected_native_mdl_sha256) or context["native_mdl_sha256"] != expected_native_mdl_sha256:
        raise SourceIdentityError("Jiggle inspection differs from independently frozen selected-MDL identity")
    try:
        base_bytes = report_bytes(base, newline)''')
path.write_text(text,encoding='utf-8')

path=SOURCE/'test_source_jiggle_metadata.py';text=path.read_text(encoding='utf-8')
assert 'def plan(' not in text
text=text.replace('M.plan_report(', 'self.plan(')
needle='''        self.raw, self.bones = authored(); self.base = base_report(self.bones); self.attempt = inspect(self.raw, self.bones)
'''
assert text.count(needle)==1
text=text.replace(needle,needle+'''
    def plan(self, baseline, attempt, newline="\\n", *, native_raw=None):
        # Expected identity comes from this fixture's frozen input bytes, not
        # from a field in the candidate metadata being tested.
        raw = self.raw if native_raw is None else native_raw
        expected = hashlib.sha256(raw).hexdigest()
        return M.plan_report(baseline, attempt, newline, expected_native_mdl_sha256=expected)
''')
edits={
 'self.plan(baseline, inspect(raw, bones), "\\r\\n")':'self.plan(baseline, inspect(raw, bones), "\\r\\n", native_raw=raw)',
 'self.plan(baseline, {"state": "none"})':'M.plan_report(baseline, {"state": "none"})',
 'self.plan(self.base, inspect(bytes(raw), self.bones))':'self.plan(self.base, inspect(bytes(raw), self.bones), native_raw=bytes(raw))',
 'self.plan(baseline, unavailable)':'self.plan(baseline, unavailable, native_raw=bytes(raw))',
 'self.plan(base_report(bones), attempt)':'self.plan(base_report(bones), attempt, native_raw=raw)',
}
for old,new in edits.items():
    assert text.count(old)==1,(old,text.count(old))
    text=text.replace(old,new)
new_tests='''
    def test_surrogate_imported_name_is_explicit_optional_inventory_mismatch(self):
        bones = copy.deepcopy(self.bones); bones[0]["name"] = "bad\\ud800"
        before = copy.deepcopy(bones)
        attempt = inspect(self.raw, bones)
        self.assertEqual((attempt["state"], attempt["status"]["reason"]), ("unavailable", "native_inventory_mismatch"))
        self.assertNotIn("metadata", attempt); self.assertEqual(bones, before)
        result = self.plan(self.base, attempt)
        self.assertEqual(result["state"], "omitted_status_inline")
        self.assertEqual(result["omission"]["retained_rule_count"], 0)
        self.assertEqual(result["report"]["native_parameters"]["bones"], self.bones)

    def test_publication_requires_independently_frozen_native_sha_before_fallback(self):
        expected = hashlib.sha256(self.raw).hexdigest()
        poisoned = copy.deepcopy(self.attempt); poisoned["metadata"]["native_mdl_sha256"] = "0" * 64
        for baseline in (self.base, padded(self.base, M.REPORT_LIMIT + 1), {**copy.deepcopy(self.base), "bad": float("nan")}):
            with self.assertRaises(M.SourceIdentityError):
                M.plan_report(baseline, poisoned, expected_native_mdl_sha256=expected)
        for context in (None, "0" * 64, True):
            with self.assertRaises(M.SourceIdentityError):
                M.plan_report(self.base, self.attempt, expected_native_mdl_sha256=context)
        raw = bytearray(self.raw); struct.pack_into("<i", raw, 4, 48)
        raw = bytes(raw); expected_unavailable = hashlib.sha256(raw).hexdigest()
        unavailable = inspect(raw, self.bones)
        unavailable["status"]["native_mdl_sha256"] = "0" * 64
        with self.assertRaises(M.SourceIdentityError):
            M.plan_report(padded(self.base, M.REPORT_LIMIT + 1), unavailable, expected_native_mdl_sha256=expected_unavailable)
        # Altering only the inspection cannot alter this trusted caller value.
        self.assertEqual(expected, hashlib.sha256(self.raw).hexdigest())

    def test_metadata_scale_rejects_bool_nonfinite_and_invalid_numeric_values(self):
        baseline = copy.deepcopy(self.base); baseline["scale"] = 1.0
        attempt = M.inspect(self.raw, ORIGINAL, hashlib.sha256(self.raw).hexdigest(), self.bones, 1.0)
        self.assertEqual(self.plan(baseline, attempt)["state"], "embedded")
        for value in (True, False, float("nan"), float("inf"), 0.0, -1.0, 1000001.0):
            poisoned = copy.deepcopy(attempt); poisoned["metadata"]["source_scale"] = value
            for base in (baseline, padded(baseline, M.REPORT_LIMIT + 1)):
                with self.assertRaises(ValueError): self.plan(base, poisoned)
'''
assert text.count('if __name__ == "__main__":')==1
text=text.replace('if __name__ == "__main__":',new_tests+'\nif __name__ == "__main__":')
path.write_text(text,encoding='utf-8')
assert all(hashlib.sha256((OLD/name).read_bytes()).hexdigest()==digest for name,digest in before.items())
(BASE/'BASELINE.json').write_text(json.dumps({'format':'has_minimal_jiggle_three_boundary_amendment_1','old_candidate':str(OLD),'old_context_sha256':before,'old_candidate_unchanged':True,'scope':['Encode-safe name admission','Strict finite numeric non-bool metadata scale','Independently frozen nativeMDL SHA publication keyword'],'signature':'plan_report(base_report, inspection, newline="\\n", *, expected_native_mdl_sha256=None)','none_state':'No-rule/BSP no-op publishes no metadata and keeps original writer; keyword not required on that no-op','runtime_or_main_changes':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'source':str(SOURCE),'old_candidate_unchanged':True,'sha256':{name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in names}},indent=2))

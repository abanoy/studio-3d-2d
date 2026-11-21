# Camera cold-wire oracle v2

SOURCE ONLY, unparsed/unrun. The corrected6532/33237d55lens fixture and original6239/072d32are byte exact predecessors. Only oracle/helper controls change. The original24controls remain, plus five focused cases: adjacent large int64 distinction, rounded mixed collision refusal, exact representable large mixed acceptance, int64 conversion boundary refusal, and independent original interpolation drift. Total29controls.

Two int64 values are compared directly. Mixed numeric values require a finite whole float inside the int64 conversion domain, int(float)==original integer and float(integer)==float, with no lossy conversion acceptance. Two finite floats remain exact. Strict booleans, whole frames and exact original engine inputs remain, now also retaining original interpolation used by Timeline.sample. No epsilon, product or persistence changes.

The prior24version remains frozen. Root must run29controls before accepting the full original486camera regression matrix. This version is test-only and does not infer any new product defect from the measured serialization boundary.

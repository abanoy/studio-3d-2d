# Synthetic sequence-equality correction

V1 actual Root run stopped before Blender:12-test batch failed one assertion (11individual tests passed); no completed12 batch or scratch cases are credited. The measured_row helper canonicalizes matrices to tuples. The synthetic equality mock compared that tuple to an equal list and returned false because of container type.

V2 changes only the positive and changed-row synthetic callbacks to tuple(a)==tuple(b). This preserves numeric-sequence equality independent of container type and ensures the negative case fails because its values differ. Helper10395/4e8de7b8, native capture, original pinned C.close, all22 scratch cases and exact baseline gates remain unchanged. This is a fixture fix, not a model repair or tolerance change.

Old frozen source9557 and the actual failure remain preserved; v2 tests and Blender remain UNRUN.

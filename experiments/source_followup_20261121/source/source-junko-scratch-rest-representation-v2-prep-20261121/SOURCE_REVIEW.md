# Version2 source/API review

Cold independently verified exact reversal: the only code changes are two synthetic equality callbacks lambda a,b:a==b → lambda a,b:tuple(a)==tuple(b). New test2998/b92d68d601bcd5204171c5839e03bc27c249ea2c6b6cbb96622bf9851572a11a; helper10395/4e8de7b858127a25c0fa782730d27a1cfcee4e9acc06f0fd9b4d484269ad4ec9 byte-exact. SOURCE/API GO; no execution.

The positive tests equal numeric content across tuple/list; the negative now rejects the changed numeric value rather than merely container types. Production pinned close(), source matrix, all22 scratch experiments, cleanup and exact original baseline gates are unchanged.

V1 actual FAIL0 (11/12 individual successes, no fulfilled12 batch, no Blender launched) is retained. V2 pure12 and actual22 remain UNRUN, no actual model repair or export qualification.

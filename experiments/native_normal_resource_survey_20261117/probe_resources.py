"""Deliberately unstageable native entry; no bpy/native input IO before admission."""
from survey_admission import require_native_survey_admission


def main():
    # No command-line flag, environment variable or caller-supplied JSON can
    # turn a missing qualification into authorization. A reviewed, separately
    # sealed successor must implement the gates in NATIVE_CONTRACT.md first.
    require_native_survey_admission()
    raise RuntimeError('No qualified native resource-survey host exists in this packet')


if __name__ == '__main__': main()

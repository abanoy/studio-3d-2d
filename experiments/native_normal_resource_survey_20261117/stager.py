"""Refusing stage boundary, intentionally no native copies, lease or launch command."""
from survey_admission import require_native_survey_admission


def main():
    require_native_survey_admission()
    raise RuntimeError('No qualified resource-survey stager exists in this packet')


if __name__ == '__main__': main()

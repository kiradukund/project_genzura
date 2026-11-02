from itertools import product

import pytest

from app.messages import (
    LANGUAGE_MENU,
    LANGUAGES,
    MESSAGES,
    flag_label,
    is_gsm7,
    sms_result,
    text,
    ussd_result,
)

USSD_MAX = 182
SMS_MAX = 160
VERDICTS = ("high_risk", "suspicious", "low_risk")
FLAG_IDS = list(MESSAGES["en"]["flags"])


def all_strings(node):
    if isinstance(node, str):
        yield node
    else:
        for value in node.values():
            yield from all_strings(value)


def test_both_languages_have_the_same_keys():
    def keys(d, prefix=""):
        out = set()
        for k, v in d.items():
            out |= keys(v, f"{prefix}{k}.") if isinstance(v, dict) else {prefix + k}
        return out

    assert keys(MESSAGES["en"]) == keys(MESSAGES["rw"])


@pytest.mark.parametrize("lang", LANGUAGES)
def test_every_string_is_gsm7(lang):
    # Templates are checked after filling in, since {placeholders} are never sent.
    strings = [s for s in all_strings(MESSAGES[lang]) if "{" not in s]
    strings += [
        f(lang, {"verdict": v, "risk_score": 0, "flags": [flag] if flag else []})
        for f in (ussd_result, sms_result)
        for v in VERDICTS
        for flag in FLAG_IDS + [None]
    ]
    bad = [s for s in strings if not is_gsm7(s)]
    assert not bad, f"Non GSM-7 characters in: {bad}"
    assert is_gsm7(LANGUAGE_MENU)


@pytest.mark.parametrize("lang,verdict,flag", list(product(LANGUAGES, VERDICTS, FLAG_IDS + [None])))
def test_results_fit_on_screen_and_in_one_sms(lang, verdict, flag):
    result = {"verdict": verdict, "risk_score": 0, "flags": [flag] if flag else []}
    assert len(ussd_result(lang, result)) <= USSD_MAX
    assert len(sms_result(lang, result)) <= SMS_MAX


@pytest.mark.parametrize("lang", LANGUAGES)
def test_menus_fit_on_screen(lang):
    for key in ("main_menu", "ask_message", "invalid", "about"):
        assert len(text(lang, key)) <= USSD_MAX


def test_unknown_language_and_flag_fall_back():
    assert text("fr", "invalid") == text("en", "invalid")
    assert flag_label("rw", "new_rule") == "new rule"


def test_kinyarwanda_result_mentions_rib():
    out = ussd_result("rw", {"verdict": "high_risk", "risk_score": 90, "flags": ["upfront_fee"]})
    assert "IBYAGO BYINSHI" in out and "Basaba kwishyura mbere" in out and "166" in out

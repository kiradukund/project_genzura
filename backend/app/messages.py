"""USSD and SMS text in English and Kinyarwanda (Alier: wording and translations).

Rules for every string here:
- GSM-7 characters only (feature phones): plain ' quotes, no accents, no curly quotes.
- A USSD screen holds about 182 characters; a single SMS holds 160.
tests/test_messages.py checks both.

Abay: the USSD/SMS handlers can call these helpers. LANGUAGE_MENU is the
language-choice first screen the feature spec asks for.

Kinyarwanda is a working draft: a second native speaker must review it before launch.
"""

LANGUAGES = ("en", "rw")

# First USSD screen, shown before we know the user's language.
LANGUAGE_MENU = "Genzura\n1. English\n2. Kinyarwanda"
LANGUAGE_CHOICES = {"1": "en", "2": "rw"}

MESSAGES = {
    "en": {
        "main_menu": "Genzura scam check\n1. Job offer\n2. Scholarship\n3. Visa",
        "ask_message": "Type the message you received:",
        "invalid": "Invalid choice. Please dial again.",
        "about": "Genzura checks overseas job, scholarship and visa offers for scams.",
        "no_flags": "No red flags found",
        "ussd_result": "{verdict}\nReason: {reason}\nCall RIB 166 to verify.",
        "sms_result": "Genzura: {verdict} Reason: {reason}. Call RIB 166 to verify.",
        "verdict": {
            "high_risk": "HIGH RISK: likely a scam. Do not pay.",
            "suspicious": "MEDIUM RISK: be careful. Do not pay or share documents.",
            "low_risk": "LOW RISK: no major scam signs. Still verify.",
        },
        "flags": {
            "upfront_fee": "Upfront payment requested",
            "guaranteed_outcome": "Guaranteed outcome claim",
            "urgency_pressure": "Pressure to act fast",
            "free_email_contact": "Generic email address",
            "chat_app_only": "WhatsApp/Telegram only",
            "sensitive_info_request": "Asks for passport/ID/PIN",
            "blacklisted_entity": "Known scam company",
            "flagged_entity": "Suspicious company",
        },
    },
    "rw": {
        "main_menu": "Genzura: suzuma uburiganya\n1. Akazi\n2. Buruse\n3. Viza",
        "ask_message": "Andika ubutumwa wakiriye:",
        "invalid": "Ibyo wahisemo si byo. Ongera uhamagare.",
        "about": "Genzura isuzuma amatangazo y'akazi, buruse na viza byo hanze ngo wirinde uburiganya.",
        "no_flags": "Nta bimenyetso byabonetse",
        "ussd_result": "{verdict}\nImpamvu: {reason}\nHamagara RIB 166 ugenzure.",
        "sms_result": "Genzura: {verdict} Impamvu: {reason}. Hamagara RIB 166.",
        "verdict": {
            "high_risk": "IBYAGO BYINSHI: birashoboka ko ari uburiganya. Ntukishyure.",
            "suspicious": "IBYAGO BIRINGANIYE: witonde. Ntukishyure, ntutange ibyangombwa.",
            "low_risk": "IBYAGO BIKE: nta bimenyetso bikomeye. Banza ugenzure.",
        },
        "flags": {
            "upfront_fee": "Basaba kwishyura mbere",
            "guaranteed_outcome": "Bakwizeza ibitangaza 100%",
            "urgency_pressure": "Barakwihutisha",
            "free_email_contact": "Imeli rusange (nka gmail)",
            "chat_app_only": "WhatsApp/Telegram gusa",
            "sensitive_info_request": "Basaba pasiporo/ID/PIN",
            "blacklisted_entity": "Ikigo kizwiho uburiganya",
            "flagged_entity": "Ikigo gikekwaho uburiganya",
        },
    },
}


def _lang(language):
    return language if language in MESSAGES else "en"


def text(language, key):
    """A plain message, e.g. text("rw", "main_menu")."""
    return MESSAGES[_lang(language)][key]


def flag_label(language, flag_id):
    labels = MESSAGES[_lang(language)]["flags"]
    return labels.get(flag_id) or MESSAGES["en"]["flags"].get(flag_id) or flag_id.replace("_", " ")


def top_reason(language, flags):
    """Label of the first red flag, or 'no red flags found'."""
    return flag_label(language, flags[0]) if flags else text(language, "no_flags")


def ussd_result(language, result):
    """Final USSD screen for a result from rules.evaluate()."""
    m = MESSAGES[_lang(language)]
    return m["ussd_result"].format(
        verdict=m["verdict"][result["verdict"]], reason=top_reason(language, result["flags"])
    )


def sms_result(language, result):
    """One-SMS summary for a result from rules.evaluate()."""
    m = MESSAGES[_lang(language)]
    return m["sms_result"].format(
        verdict=m["verdict"][result["verdict"]], reason=top_reason(language, result["flags"])
    )


# GSM 03.38 basic character set (no extension table, which costs 2 characters each).
GSM7 = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)


def is_gsm7(s):
    return all(ch in GSM7 for ch in s)

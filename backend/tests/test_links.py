# OWNER: Chol (tests added by Kevin)
import pytest

from app.links import extract_domain, extract_urls, find_suspicious_links, link_flags
from app.rules import evaluate


@pytest.mark.parametrize("text", [
    "Apply at bit.ly/visa-rw now",                 # short link without http
    "Apply at https://tinyurl.com/abc",
    "Pay at http://jobs-abroad.com/pay",            # no encryption
    "Pay at https://canada-visa.xyz/pay",           # spam ending
    "Open https://192.168.1.10/login",              # raw IP address
    "See https://embassy-canada.com",               # pretends to be an embassy
    "Go to https://gov-canada.org/apply",           # pretends to be government
    "Visit https://xn--irembo-9ta.com",             # look-alike letters
    "Register at www.official-visa.online",
])
def test_suspicious_links_are_found(text):
    assert find_suspicious_links(text)


@pytest.mark.parametrize("text", [
    "Visit https://irembo.gov.rw to apply",
    "Official info: https://rw.usembassy.gov/visas",
    "Careers at https://www.unicef.org/careers",
    "Apply on https://www.canada.ca/en/immigration",
    "UK visas: https://www.gov.uk/browse/visas-immigration",
    "Mail hr@gmail.com to pay",                     # an email, not a link
    "We met in Kigali.Then we left",
    "Price 1.5 million, apply e.g. now",
])
def test_normal_text_and_real_sites_are_not_flagged(text):
    assert find_suspicious_links(text) == []


def test_urls_and_domains_are_extracted_cleanly():
    urls = extract_urls("See https://Bit.ly/x?y=1, and www.example.com/a.")
    assert urls == ["https://Bit.ly/x?y=1", "www.example.com/a"]
    assert extract_domain("https://user@Evil.com:8080/path") == "evil.com"


def test_link_flag_raises_the_score():
    assert link_flags("Apply at bit.ly/visa-rw") == [("suspicious_link", 20)]
    result = evaluate("Apply at bit.ly/visa-rw and pay the processing fee")
    assert result["flags"] == ["upfront_fee", "suspicious_link"]
    assert result["risk_score"] == 60
    assert result["verdict"] == "high_risk"


def test_flag_counts_once_for_many_links():
    result = evaluate("bit.ly/a and bit.ly/b and http://x.xyz")
    assert result["flags"].count("suspicious_link") == 1

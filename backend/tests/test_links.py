# OWNER: Chol
from app.links import find_suspicious_links


def test_url_shortener_flagged():
    assert find_suspicious_links("apply here: https://bit.ly/3xJob") != []


def test_raw_ip_flagged():
    assert find_suspicious_links("visit http://192.168.1.1/apply") != []


def test_plain_http_flagged():
    assert find_suspicious_links("go to http://example.com/job") != []


def test_spam_tld_flagged():
    assert find_suspicious_links("check https://jobs.xyz/offer") != []


def test_lookalike_flagged():
    assert find_suspicious_links("visit https://xn--gvt.com/apply") != []


def test_fake_gov_domain_flagged():
    assert find_suspicious_links("apply at https://embassy-jobs.com/visa") != []


def test_clean_https_not_flagged():
    assert find_suspicious_links("visit https://www.gov.rw/jobs") == []


def test_no_urls_returns_empty():
    assert find_suspicious_links("send your CV to our office") == []


def test_empty_text_returns_empty():
    assert find_suspicious_links("") == []

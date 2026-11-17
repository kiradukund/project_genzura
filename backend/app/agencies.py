from flask import Blueprint, jsonify, request

agencies_bp = Blueprint("agencies", __name__)

# OWNER: Didier - Licensed agency registry. Build: GET /api/agencies
#
# Rwanda has no licensed private recruitment agencies for jobs abroad yet.
# - New Times, 3 Aug 2026: Parliament's committee found the licensed agencies
#   planned under the National Labour Mobility Policy have not been established.
# - New Times, 30 Jul 2026: the committee chair said MIFOTRA has not yet issued
#   the ministerial order that would regulate them.
# So the registry is empty on purpose. When an official list is published,
# add the agencies to LICENSED_AGENCIES and update AS_OF.
# MIFOTRA contacts checked on mifotra.gov.rw on 2026-11-16.

AS_OF = "2026-11-16"

LICENSED_AGENCIES = []

VERIFY_WITH = [
    {
        "name": "Ministry of Public Service and Labour (MIFOTRA)",
        "phone": "0785569165",
        "email": "info@mifotra.gov.rw",
    },
    {"name": "Rwanda Investigation Bureau (RIB)", "phone": "166"},
]

SOURCES = [
    {
        "title": "Parliament flags seven gaps in labour mobility policy",
        "publisher": "The New Times",
        "date": "2026-08-03",
        "url": "https://www.newtimes.co.rw/article/37870/news/rwanda/parliament-flags-seven-gaps-in-labour-mobility-policy",
    },
    {
        "title": "Govt urged to take action against unregulated overseas recruiters",
        "publisher": "The New Times",
        "date": "2026-07-30",
        "url": "https://www.newtimes.co.rw/article/37796/news/rwanda/govt-urged-to-take-action-against-unregulated-overseas-recruiters",
    },
]


@agencies_bp.get("/api/agencies")
def list_agencies():
    name = (request.args.get("name") or "").strip()
    body = {
        "licensed_agencies": LICENSED_AGENCIES,
        "status": "no_licensed_agencies_yet" if not LICENSED_AGENCIES else "official_list",
        "as_of": AS_OF,
        "verify_with": VERIFY_WITH,
        "sources": SOURCES,
    }
    if name:
        found = any(a["name"].lower() == name.lower() for a in LICENSED_AGENCIES)
        body["query"] = name
        body["licensed"] = found
    return jsonify(body)

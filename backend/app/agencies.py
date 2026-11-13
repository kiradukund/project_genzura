from flask import Blueprint, jsonify, request

agencies_bp = Blueprint("agencies", __name__)

# OWNER: Didier - Licensed agency registry. Build: GET /api/agencies
#
# Rwanda has not licensed any overseas recruitment agencies yet: MIFOTRA has
# not issued the ministerial order that would allow it (Parliament, July 2026).
# So the registry is empty on purpose. When an official list is published,
# add the agencies to LICENSED_AGENCIES and update AS_OF.

AS_OF = "2026-11-13"

LICENSED_AGENCIES = []

VERIFY_WITH = [
    {"name": "Ministry of Public Service and Labour (MIFOTRA)", "email": "info@mifotra.gov.rw"},
    {"name": "Rwanda Investigation Bureau (RIB)", "phone": "166"},
]


@agencies_bp.get("/api/agencies")
def list_agencies():
    name = (request.args.get("name") or "").strip()
    body = {
        "licensed_agencies": LICENSED_AGENCIES,
        "status": "no_licensed_agencies_yet" if not LICENSED_AGENCIES else "official_list",
        "as_of": AS_OF,
        "verify_with": VERIFY_WITH,
    }
    if name:
        found = any(a["name"].lower() == name.lower() for a in LICENSED_AGENCIES)
        body["query"] = name
        body["licensed"] = found
    return jsonify(body)

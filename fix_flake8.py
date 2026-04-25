import re

files_to_fix = {
    'blueprints/api/v1/analysis.py': [
        (r"for field, value in data\.items\(\):", r"for field, value in request.get_json().items():"),
        (r"analyses_data = data\['analyses'\]", r"data = request.get_json()\n    analyses_data = data['analyses']"),
        (r"portfolio_id = data\.get\('portfolio_id'\)", r"portfolio_id = data.get('portfolio_id')")
    ],
    'blueprints/api/v1/crm.py': [
        (r"pagination = query\.paginate\(page=page, per_page=per_page, error_out=False\)", r"page = request.args.get('page', 1, type=int)\n    per_page = request.args.get('per_page', 20, type=int)\n    pagination = query.paginate(page=page, per_page=per_page, error_out=False)"),
        (r"page=page,", r"page=page,"),
        (r"per_page=per_page,", r"per_page=per_page,")
    ],
    'blueprints/crm_bp.py': [
        (r"team = CrmTeam\.query\.filter_by\(broker_id=current_user\.id\)\.first\(\)", r"from models.crm_models import CrmTeam\n    team = CrmTeam.query.filter_by(broker_id=current_user.id).first()"),
        (r"team = CrmTeam\(broker_id=current_user\.id, name=f\"\{current_user\.firma\} Ekibi\"\)", r"team = CrmTeam(broker_id=current_user.id, name=f\"{current_user.firma} Ekibi\")")
    ],
    'modules/analiz.py': [
        (r"altyapi = json\.loads\(altyapi\)", r"import json\n                 altyapi = json.loads(altyapi)")
    ]
}

print("Running manual fixes...")

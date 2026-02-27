"""
Exporta objeto compilado + layout em JSON estável e versionado.
"""
import json
def export_json(data, compiled, layout):
    obj = {
        'sff': data.get('sff', {}),
        'entry': data.get('entry', {}),
        'lanes': data.get('lanes', {}),
        'nodes': data.get('nodes', {}),
        'edges': data.get('edges', []),
        'compiled': compiled,
        'layout': layout,
        'export_version': '1.0'
    }
    return json.dumps(obj, indent=2, ensure_ascii=False)

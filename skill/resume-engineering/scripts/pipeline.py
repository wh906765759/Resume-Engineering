"""Fact-bound projections, incremental artifacts and explicit human-review gates."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone
from contracts import validate, allowed_for

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
USES = {'website': 'public_website', 'assistant': 'public_ai', 'resume': 'targeted_resume'}
SAFE_FIELDS = {'title', 'period', 'background', 'role', 'contribution_scope', 'responsibility', 'technical_approach', 'method', 'tools', 'result', 'metrics', 'applicable_roles', 'keywords'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.writing-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def facts_at(workspace):
    records = read(Path(workspace) / 'facts/facts.json')
    for fact in records:
        validate(fact, 'fact')
    result = {f['fact_id']: f for f in records}
    if len(result) != len(records):
        raise ValueError('Duplicate fact ID')
    return result


def initialize(workspace, fixture):
    workspace = Path(workspace).resolve()
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError('Initialization requires an empty workspace')
    data = read(fixture)
    if data['plan'].get('synthetic') is not True:
        raise ValueError('Demo initialization requires a synthetic fixture')
    for f in data['facts']:
        validate(f, 'fact')
    save(workspace / 'facts/facts.json', data['facts'])
    save(workspace / 'project/plan.json', data['plan'])
    save(workspace / 'project/build-manifest.json', {'artifacts': {}})
    save(workspace / 'project/run-state.json', {'schema_version': '1.0', 'last_operation': 'init', 'token_usage': None})
    return {'initialized': True, 'facts': len(data['facts']), 'synthetic': True}


def target_name(target, plan):
    if target in {'website', 'assistant'}:
        return target
    if target.startswith('resume:'):
        role = target.split(':', 1)[1]
        if role in plan['roles'] and role and all(c.isalnum() or c in '-_' for c in role):
            return 'resume-' + role
    raise ValueError('Unknown target or unsafe role name')


def resolve_view(plan, facts, use):
    provenance = {}
    def resolve(node, route):
        if isinstance(node, dict) and '$fact' in node:
            if set(node) != {'$fact', 'field'} or node['field'] not in SAFE_FIELDS:
                raise ValueError('Only explicit safe fact fields may be projected')
            fact = facts.get(node['$fact'])
            if fact is None:
                raise ValueError('Unknown fact binding')
            if not allowed_for(fact, use):
                raise ValueError('Fact not approved for requested use: ' + fact['fact_id'])
            field = node['field']
            # Every displayed field must have explicit supporting evidence.
            if not any(e['review_status'] == 'supports' and field in e['supports'] for e in fact['evidence']):
                raise ValueError('No field-level support: ' + fact['fact_id'])
            value = copy.deepcopy(fact[field])
            if field == 'metrics':
                value = [{k: m[k] for k in ('value', 'unit', 'context')} for m in value]
            provenance['.'.join(map(str, route))] = {'fact_id': fact['fact_id'], 'version': fact['version'], 'field': field}
            return value
        if isinstance(node, dict):
            return {k: resolve(v, route + [k]) for k, v in node.items()}
        if isinstance(node, list):
            return [resolve(v, route + [i]) for i, v in enumerate(node)]
        if isinstance(node, str):
            raise ValueError('Unbound text in presentation plan')
        return node
    view = resolve(plan['view'], [])
    view['synthetic'] = bool(plan.get('synthetic', False))
    view['approved_view'] = True
    return view, provenance


def template_hash(kind):
    directories = ['shared'] + (['resume-template'] if kind == 'resume' else ['website-template'])
    files = []
    for directory in directories:
        for file in sorted((ASSETS / directory).glob('*')):
            if file.is_file() and file.name not in {'demo-data.js', 'media-record.example.json'}:
                files.append((str(file.relative_to(ASSETS)), hashlib.sha256(file.read_bytes()).hexdigest()))
    return digest(files)


def references(node):
    if isinstance(node, dict):
        if '$fact' in node:
            return {node['$fact']}
        return set().union(*(references(v) for v in node.values())) if node else set()
    if isinstance(node, list):
        return set().union(*(references(v) for v in node)) if node else set()
    return set()


def view_plan(plan, kind):
    result = copy.deepcopy(plan)
    if kind == 'website':
        # Never pack unused resume-only sections into a public browser payload.
        keep = {'name', 'english', 'positioning', 'projects', 'work', 'education'}
        result['view'] = {k: v for k, v in plan['view'].items() if k in keep}
    return result


def fingerprint(plan, facts, target):
    kind = target.split(':')[0]
    selected = view_plan(plan, kind)
    ids = references(selected['view'])
    relevant_plan = selected['view']
    role = plan['roles'][target.split(':')[1]] if kind == 'resume' else None
    return digest({'facts': {i: facts.get(i) for i in sorted(ids)}, 'plan': relevant_plan,
                   'synthetic': plan.get('synthetic'), 'role': role, 'template': template_hash(kind)})


def knowledge(facts):
    result = []
    for fact in facts.values():
        if allowed_for(fact, 'public_ai'):
            fields = ['background', 'role', 'contribution_scope', 'responsibility', 'technical_approach', 'method', 'result']
            supported = {f for e in fact['evidence'] if e['review_status'] == 'supports' for f in e['supports']}
            content = {field: fact[field] for field in fields if field in supported and fact[field]}
            if content:
                result.append({'id': fact['fact_id'], 'version': fact['version'], 'content': content})
    return result


def isolate(workspace, key):
    if not key or Path(key).name != key or key in {'.', '..'} or '\\' in key or '/' in key:
        raise ValueError('Unsafe artifact key')
    directory = Path(workspace) / 'exports' / key
    if directory.exists():
        base = Path(workspace).resolve()
        if directory.is_symlink() or not directory.resolve().is_relative_to(base / 'exports'):
            raise ValueError('Unsafe export path')
        archive = Path(workspace) / 'private/quarantine'
        archive.mkdir(parents=True, exist_ok=True)
        destination = archive / (key + '-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f'))
        shutil.move(str(directory), str(destination))


def build(workspace, targets):
    workspace = Path(workspace).resolve()
    facts, plan = facts_at(workspace), read(workspace / 'project/plan.json')
    manifest = read(workspace / 'project/build-manifest.json')
    exports = workspace / 'exports'
    if exports.is_symlink() or (exports.exists() and exports.resolve() != exports):
        raise ValueError('Export root cannot be redirected')
    result = {'generated': [], 'reused': [], 'quarantined': [], 'blocked': {}}
    # Invalidate every previous artifact, even outside requested generation scope.
    for target, record in manifest['artifacts'].items():
        try:
            current = digest(knowledge(facts)) if target == 'assistant' else fingerprint(plan, facts, target)
        except (ValueError, KeyError):
            current = None
        if current != record['fingerprint']:
            isolate(workspace, record['key'])
            record['status'] = 'stale'
            result['quarantined'].append(target)
    for target in targets:
        key = target_name(target, plan)
        if (exports / key).is_symlink():
            raise ValueError('Export target cannot be a symlink')
        kind = target.split(':')[0]
        fp = digest(knowledge(facts)) if kind == 'assistant' else fingerprint(plan, facts, target)
        old = manifest['artifacts'].get(target)
        if old and old['fingerprint'] == fp and old['status'] == 'ready' and artifact_matches(workspace, old):
            result['reused'].append(target)
            continue
        # Never adopt unexpected files into the next approved manifest.
        if (exports / key).exists():
            isolate(workspace, key)
        try:
            if kind == 'assistant':
                data = knowledge(facts)
                save(workspace / 'exports' / key / 'knowledge.json', data)
                sources = [{'fact_id': x['id'], 'version': x['version']} for x in data]
            else:
                view, sources = resolve_view(view_plan(plan, kind), facts, USES[kind])
                if kind == 'resume':
                    strategy = plan['roles'][target.split(':')[1]]
                    for field, order in [('projects', strategy['project_order']), ('capabilities', strategy['capability_order'])]:
                        if sorted(order) != list(range(len(view[field]))):
                            raise ValueError('Role order must be a permutation; no invented content')
                        view[field] = [view[field][i] for i in order]
                destination = workspace / 'exports' / key
                destination.mkdir(parents=True, exist_ok=True)
                template = ASSETS / ('resume-template' if kind == 'resume' else 'website-template')
                for name in ['index.html', 'styles.css', 'render.js']:
                    text = (template / name).read_text(encoding='utf-8').replace('../shared/', 'shared/')
                    if name == 'index.html':
                        text = text.replace('../resume-template/index.html', '#assistant')
                        if not view['synthetic']:
                            text = text.replace('虚构', '').replace('演示', '').replace('未连接模型服务', '基于获准公开资料')
                    (destination / name).write_text(text, encoding='utf-8')
                shared = destination / 'shared'
                shared.mkdir(exist_ok=True)
                shutil.copyfile(ASSETS / 'shared/portrait-placeholder.svg', shared / 'portrait-placeholder.svg')
                (shared / 'demo-data.js').write_text('window.RESUME_DATA = ' + json.dumps(view, ensure_ascii=False).replace('<', '\\u003c') + ';\n', encoding='utf-8')
            directory = workspace / 'exports' / key
            files = {str(f.relative_to(directory)).replace('\\', '/'): hashlib.sha256(f.read_bytes()).hexdigest()
                     for f in directory.rglob('*') if f.is_file()}
            manifest['artifacts'][target] = {'key': key, 'fingerprint': fp, 'status': 'ready', 'sources': sources, 'files': files}
            result['generated'].append(target)
        except (ValueError, KeyError) as error:
            isolate(workspace, key)
            result['blocked'][target] = str(error)
    save(workspace / 'project/build-manifest.json', manifest)
    graph_nodes = [{'id': f['fact_id'], 'kind': 'fact', 'version': f['version'], 'status': 'ready' if f['status'] == 'verified' else 'draft'} for f in facts.values()]
    graph_edges = []
    for target, record in manifest['artifacts'].items():
        aid = 'artifact:' + target
        graph_nodes.append({'id': aid, 'kind': 'artifact', 'version': 1, 'status': record['status']})
        sources = record['sources'].values() if isinstance(record['sources'], dict) else record['sources']
        for ref in { (s['fact_id'], s['version']) for s in sources }:
            if ref[0] in facts:
                graph_edges.append({'from': ref[0], 'to': aid, 'source_version': ref[1]})
    graph = {'schema_version': '1.0', 'nodes': graph_nodes, 'edges': graph_edges}
    validate(graph, 'dependencies')
    save(workspace / 'project/dependencies.json', graph)
    save(workspace / 'project/run-state.json', {'schema_version': '1.0', 'last_operation': 'build', 'result': result, 'token_usage': None})
    return result


def artifact_matches(workspace, record):
    key = record['key']
    if not key or Path(key).name != key or key in {'.', '..'} or '\\' in key or '/' in key:
        return False
    directory = Path(workspace) / 'exports' / record['key']
    files = record.get('files', {})
    if not files or not directory.is_dir() or directory.is_symlink():
        return False
    if not directory.resolve().is_relative_to(Path(workspace).resolve() / 'exports'):
        return False
    entries = list(directory.rglob('*'))
    if any(f.is_symlink() for f in entries):
        return False
    actual = {f.relative_to(directory).as_posix() for f in entries if f.is_file()}
    if actual != set(files):
        return False
    for relative, expected in files.items():
        file = directory / relative
        if not file.resolve().is_relative_to(directory.resolve()) or not file.is_file():
            return False
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            return False
    return True


def propose(workspace, candidate):
    workspace = Path(workspace)
    facts = facts_at(workspace)
    incoming = read(candidate)
    validate(incoming, 'fact')
    old = facts.get(incoming['fact_id'])
    if old == incoming:
        return {'status': 'duplicate', 'changed_fields': []}
    changed = [k for k in incoming if not old or incoming[k] != old[k]]
    duplicates = [f['fact_id'] for f in facts.values() if f['fact_id'] != incoming['fact_id'] and
                  (f['title'], f['period'], f['role']) == (incoming['title'], incoming['period'], incoming['role'])]
    proposal = {'base_digest': digest(list(facts.values())), 'candidate': incoming, 'changed_fields': changed,
                'possible_duplicates': duplicates, 'status': 'requires_review'}
    save(workspace / 'private/merge-proposal.json', proposal)
    return {k: proposal[k] for k in ('status', 'changed_fields', 'possible_duplicates')}


def accept(workspace):
    workspace = Path(workspace)
    facts = facts_at(workspace)
    proposal = read(workspace / 'private/merge-proposal.json')
    if proposal['base_digest'] != digest(list(facts.values())):
        raise ValueError('Facts changed since proposal; regenerate and review')
    if proposal['possible_duplicates']:
        raise ValueError('Resolve possible duplicate identity before acceptance')
    candidate = proposal['candidate']
    old = facts.get(candidate['fact_id'])
    if old:
        previous = {e['evidence_id']: e for e in old['evidence']}
        for e in candidate['evidence']:
            if e['evidence_id'] in previous and previous[e['evidence_id']] != e:
                raise ValueError('Evidence is immutable; add a new evidence ID')
            previous[e['evidence_id']] = e
        candidate['evidence'] = list(previous.values())
    candidate['version'] = (old['version'] if old else 0) + 1
    candidate['status'] = 'pending_review'
    for permission in candidate['permissions'].values():
        permission.update(decision='deny', reason='Changed content requires fresh review', review=None)
    validate(candidate, 'fact')
    save(workspace / 'private/history' / (digest(list(facts.values())) + '.json'), list(facts.values()))
    facts[candidate['fact_id']] = candidate
    save(workspace / 'facts/facts.json', list(facts.values()))
    return build(workspace, [])


def approve(workspace, fact_id, use, evidence_id):
    facts = facts_at(workspace)
    fact = facts[fact_id]
    if use not in fact['permissions'] or fact['conflict_ids']:
        raise ValueError('Invalid use or unresolved conflict')
    if not any(e['evidence_id'] == evidence_id and e['review_status'] == 'supports' for e in fact['evidence']):
        raise ValueError('Supporting confirmation required')
    fact['status'] = 'verified'
    fact['permissions'][use] = {'decision': 'allow', 'reason': 'Explicit reviewer action', 'review': {
        'review_id': 'review-' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f'),
        'reviewed_at': datetime.now(timezone.utc).isoformat(), 'fact_version': fact['version'], 'evidence_ref': evidence_id}}
    validate(fact, 'fact')
    save(Path(workspace) / 'facts/facts.json', list(facts.values()))
    return {'approved': fact_id, 'use': use, 'version': fact['version']}


def revoke(workspace, fact_id, use):
    facts = facts_at(workspace)
    fact = facts[fact_id]
    if use not in fact['permissions']:
        raise ValueError('Unknown use')
    fact['permissions'][use].update(decision='revoked', reason='Explicit user revocation', review=None)
    validate(fact, 'fact')
    save(Path(workspace) / 'facts/facts.json', list(facts.values()))
    return build(workspace, [])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['init-demo', 'build', 'propose', 'accept', 'approve', 'revoke'])
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--fixture')
    parser.add_argument('--targets', nargs='*', default=['website', 'resume:process', 'assistant'])
    parser.add_argument('--candidate')
    parser.add_argument('--fact-id')
    parser.add_argument('--use')
    parser.add_argument('--evidence-id')
    args = parser.parse_args()
    result = {'init-demo': lambda: initialize(args.workspace, args.fixture), 'build': lambda: build(args.workspace, args.targets),
              'propose': lambda: propose(args.workspace, args.candidate), 'accept': lambda: accept(args.workspace),
              'approve': lambda: approve(args.workspace, args.fact_id, args.use, args.evidence_id),
              'revoke': lambda: revoke(args.workspace, args.fact_id, args.use)}[args.command]()
    print(json.dumps(result, ensure_ascii=False))

"""Framework contract helpers; no generation, network calls, or file mutations."""
from pathlib import Path
import json
from functools import lru_cache
from jsonschema import Draft202012Validator, FormatChecker

SCHEMAS = Path(__file__).resolve().parents[1] / 'assets' / 'schemas'


@lru_cache(maxsize=3)
def validator_for(kind):
    if kind not in {'fact', 'state', 'dependencies'}:
        raise ValueError('Unknown contract')
    schema = json.loads((SCHEMAS / f'{kind}.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(document, kind):
    validator_for(kind).validate(document)
    if kind == 'fact':
        ids = [e['evidence_id'] for e in document['evidence']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate evidence IDs')
        for metric in document['metrics']:
            if metric['source_ref'] not in ids:
                raise ValueError('Unknown metric evidence')
        for permission in document['permissions'].values():
            review = permission['review']
            if review and review['evidence_ref'] not in ids:
                raise ValueError('Unknown approval evidence')
    if kind == 'dependencies':
        ids = [n['id'] for n in document['nodes']]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate dependency nodes')
        adjacency = {i: [] for i in ids}
        for edge in document['edges']:
            if edge['from'] not in adjacency or edge['to'] not in adjacency:
                raise ValueError('Unknown dependency endpoint')
            adjacency[edge['from']].append(edge['to'])
        active, done = set(), set()

        def visit(node):
            if node in active:
                raise ValueError('Dependency cycle')
            if node in done:
                return
            active.add(node)
            for child in adjacency[node]:
                visit(child)
            active.remove(node)
            done.add(node)

        for node in adjacency:
            visit(node)


def allowed_for(fact, use):
    validate(fact, 'fact')
    if use not in fact['permissions']:
        return False
    permission = fact['permissions'][use]
    review = permission['review']
    # Private storage is not a claim that the content is verified.
    if use != 'private_storage' and (fact['status'] != 'verified' or fact['conflict_ids']):
        return False
    return bool(permission['decision'] == 'allow' and review and review['fact_version'] == fact['version'])


def impacted(graph, changed_ids):
    validate(graph, 'dependencies')
    ids = {n['id'] for n in graph['nodes']}
    if not set(changed_ids) <= ids:
        raise ValueError('Unknown change; expand module reference audit')
    result, pending = set(changed_ids), list(changed_ids)
    while pending:
        current = pending.pop()
        for edge in graph['edges']:
            if edge['from'] == current and edge['to'] not in result:
                result.add(edge['to'])
                pending.append(edge['to'])
    return sorted(result - set(changed_ids))


def stale_inputs(graph):
    validate(graph, 'dependencies')
    nodes = {n['id']: n for n in graph['nodes']}
    direct = {e['to'] for e in graph['edges'] if nodes[e['from']]['version'] != e['source_version']}
    direct |= {n['id'] for n in graph['nodes'] if n['status'] in {'stale', 'quarantined'}}
    return sorted(direct | set(impacted(graph, direct)))

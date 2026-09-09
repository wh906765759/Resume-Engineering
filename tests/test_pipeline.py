import copy
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skill/resume-engineering/scripts'))
import pipeline as p
import assistant_server as a


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ws = Path(self.temp.name)
        p.initialize(self.ws, ROOT / 'examples/synthetic-person/workflow.json')

    def tearDown(self):
        self.temp.cleanup()

    def test_generation_and_reuse(self):
        targets = ['website', 'resume:process', 'resume:npi', 'assistant']
        self.assertEqual(p.build(self.ws, targets)['generated'], targets)
        self.assertEqual(p.build(self.ws, targets)['reused'], targets)
        p.validate(p.read(self.ws / 'project/dependencies.json'), 'dependencies')
        public = (self.ws / 'exports/website/shared/demo-data.js').read_text(encoding='utf-8')
        self.assertNotIn('evidence_id', public)
        self.assertNotIn('permissions', public)
        self.assertNotIn('contact', public)

    def test_tamper_regenerates(self):
        p.build(self.ws, ['website'])
        (self.ws / 'exports/website/index.html').write_text('tampered')
        self.assertEqual(p.build(self.ws, ['website'])['generated'], ['website'])

    def test_extra_file_is_quarantined_not_adopted(self):
        p.build(self.ws, ['website'])
        extra = self.ws / 'exports/website/unapproved.txt'
        extra.write_text('private-test-marker')
        record = p.read(self.ws / 'project/build-manifest.json')['artifacts']['website']
        self.assertFalse(p.artifact_matches(self.ws, record))
        p.build(self.ws, ['website'])
        self.assertFalse(extra.exists())
        self.assertTrue(list((self.ws / 'private/quarantine').rglob('unapproved.txt')))

    def test_unsafe_artifact_key_rejected(self):
        for key in ['../private', '..', 'x/y', 'x\\y']:
            with self.assertRaises(ValueError): p.isolate(self.ws, key)
            self.assertFalse(p.artifact_matches(self.ws, {'key': key}))

    def test_explicit_revoke(self):
        p.build(self.ws, ['website'])
        fact_id = next(iter(p.facts_at(self.ws)))
        self.assertIn('website', p.revoke(self.ws, fact_id, 'public_website')['quarantined'])
        self.assertFalse(p.allowed_for(p.facts_at(self.ws)[fact_id], 'public_website'))

    def test_provider_redirect_and_false_citation(self):
        with self.assertRaises(ValueError):
            a.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.invalid/elsewhere')
        response = {'choices':[{'message':{'content':json.dumps({'answer':'Unsupported', 'citations':['K999']})}}]}
        config = {'provider':'openai-compatible','endpoint':'https://example.invalid/chat','key':'test-only','model':'test'}
        with self.assertRaises(ValueError):
            a.provider_answer('test', [{'ref':'K1','text':'test evidence'}], config, lambda _: json.dumps(response).encode())

    def test_revocation_quarantines_unrequested_target(self):
        p.build(self.ws, ['website', 'assistant'])
        facts = p.read(self.ws / 'facts/facts.json')
        facts[0]['permissions']['public_website'].update(decision='revoked', review=None)
        p.save(self.ws / 'facts/facts.json', facts)
        result = p.build(self.ws, ['assistant'])
        self.assertIn('website', result['quarantined'])
        self.assertFalse((self.ws / 'exports/website').exists())
        self.assertIn('website', p.build(self.ws, ['website'])['blocked'])

    def test_bindings_require_evidence_and_permissions(self):
        facts = p.facts_at(self.ws)
        plan = p.read(self.ws / 'project/plan.json')
        plan['view'] = {'name': {'$fact': next(iter(facts)), 'field': 'evidence'}}
        with self.assertRaises(ValueError): p.resolve_view(plan, facts, 'public_website')
        plan['view'] = {'name': 'Unverified literal'}
        with self.assertRaises(ValueError): p.resolve_view(plan, facts, 'public_website')

    def test_merge_requires_fresh_approval(self):
        candidate = copy.deepcopy(next(iter(p.facts_at(self.ws).values())))
        candidate['result'] = 'Synthetic revised identity'
        p.save(self.ws / 'candidate.json', candidate)
        self.assertEqual(p.propose(self.ws, self.ws / 'candidate.json')['status'], 'requires_review')
        p.accept(self.ws)
        current = p.facts_at(self.ws)[candidate['fact_id']]
        self.assertEqual(current['version'], 2)
        self.assertEqual(current['status'], 'pending_review')
        self.assertTrue(all(x['decision'] == 'deny' for x in current['permissions'].values()))
        self.assertEqual(current['evidence'], candidate['evidence'])

    def test_provider_contract(self):
        passages = [{'ref': 'K1', 'text': 'Synthetic process evidence'}]
        config = {'provider':'openai-compatible', 'endpoint':'https://example.invalid/chat', 'key':'test-only', 'model':'test'}
        def transport(request):
            body = json.loads(request.data)
            self.assertNotIn('evidence_id', str(body))
            return json.dumps({'choices':[{'message':{'content':json.dumps({'answer':'Supported response', 'citations':['K1']})}}]}).encode()
        self.assertEqual(a.provider_answer('process', passages, config, transport)['mode'], 'model')
        with self.assertRaises(ValueError):
            a.provider_answer('process', passages, {**config, 'endpoint':'http://example.invalid'}, transport)

    def test_http_and_current_permissions(self):
        p.build(self.ws, ['website'])
        server = a.make_server(self.ws)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        def post(origin):
            return urlopen(Request(base+'/api/ai/chat', data=json.dumps({'message':'工艺开发'}).encode(), headers={'Content-Type':'application/json','Origin':origin}), timeout=10)
        try:
            with urlopen(base, timeout=10) as response: self.assertEqual(response.status, 200)
            with post(base) as response: self.assertEqual(json.load(response)['mode'], 'mock')
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(base+'/api/ai/chat', data=b'{}', headers={'Content-Type':'application/json'}))
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            with patch.object(a, 'provider_answer', side_effect=TimeoutError('private-secret-marker')):
                with self.assertRaises(HTTPError) as error: post(base)
                self.assertEqual(error.exception.code, 503)
                self.assertNotIn('private-secret-marker', error.exception.read().decode())
                error.exception.close()
            with self.assertRaises(HTTPError) as error: post('https://example.invalid')
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            with self.assertRaises(HTTPError) as error: urlopen(base+'/facts/facts.json')
            self.assertEqual(error.exception.code, 404)
            error.exception.close()
            facts = p.read(self.ws / 'facts/facts.json')
            for fact in facts: fact['permissions']['public_ai'].update(decision='revoked', review=None)
            p.save(self.ws / 'facts/facts.json', facts)
            with post(base) as response: self.assertEqual(json.load(response)['status'], 'unsupported')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__': unittest.main()

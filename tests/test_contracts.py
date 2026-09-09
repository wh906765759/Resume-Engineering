import copy
import importlib.util
import json
from pathlib import Path
import unittest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contracts', ROOT / 'skill/resume-engineering/scripts/contracts.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        def load(name):
            return json.loads((ROOT / f'examples/synthetic-person/{name}.json').read_text(encoding='utf-8'))
        self.fact, self.state, self.graph = load('fact'), load('state'), load('dependencies')

    def test_examples_validate(self):
        for name, value in [('fact', self.fact), ('state', self.state), ('dependencies', self.graph)]:
            c.validate(value, name)

    def test_resume_permission_does_not_allow_website(self):
        self.assertTrue(c.allowed_for(self.fact, 'targeted_resume'))
        self.assertFalse(c.allowed_for(self.fact, 'public_website'))

    def test_restricted_fact_cannot_be_published(self):
        self.fact['privacy_level'] = 'restricted'
        with self.assertRaises(ValidationError):
            c.validate(self.fact, 'fact')

    def test_verified_requires_evidence(self):
        self.fact['evidence'] = []
        with self.assertRaises(ValidationError):
            c.validate(self.fact, 'fact')

    def test_conflict_prevents_verified_claim(self):
        self.fact['conflict_ids'] = ['conflict-1']
        with self.assertRaises(ValidationError):
            c.validate(self.fact, 'fact')

    def test_revision_invalidates_previous_approval(self):
        self.fact['version'] += 1
        self.assertFalse(c.allowed_for(self.fact, 'targeted_resume'))

    def test_revocation_disables_output(self):
        self.fact['permissions']['targeted_resume']['decision'] = 'revoked'
        self.assertFalse(c.allowed_for(self.fact, 'targeted_resume'))

    def test_unverified_fact_does_not_support_resume(self):
        self.fact['status'] = 'pending_review'
        self.assertFalse(c.allowed_for(self.fact, 'targeted_resume'))

    def test_metric_cannot_reference_missing_evidence(self):
        self.fact['metrics'] = [{'value': '2', 'unit': 'hours', 'context': 'synthetic', 'source_ref': 'missing'}]
        with self.assertRaises(ValueError):
            c.validate(self.fact, 'fact')

    def test_transitive_impact(self):
        self.assertEqual(c.impacted(self.graph, ['DEMO-FACT-001']), ['resume-content', 'resume-pdf'])

    def test_local_reorder_excludes_unrelated_website(self):
        self.assertEqual(c.impacted(self.graph, ['resume-content']), ['resume-pdf'])

    def test_changed_fact_version_invalidates_outputs(self):
        self.graph['nodes'][0]['version'] = 2
        self.assertEqual(c.stale_inputs(self.graph), ['resume-content', 'resume-pdf'])

    def test_quarantine_propagates(self):
        self.graph['nodes'][0]['status'] = 'quarantined'
        self.assertEqual(c.stale_inputs(self.graph), ['DEMO-FACT-001', 'resume-content', 'resume-pdf'])

    def test_unknown_input_is_not_treated_as_no_impact(self):
        with self.assertRaises(ValueError):
            c.impacted(self.graph, ['unknown'])

    def test_graph_rejects_cycle_and_unknown_endpoint(self):
        for edge in [{'from': 'resume-pdf', 'to': 'resume-content', 'source_version': 1},
                     {'from': 'unknown', 'to': 'resume-content', 'source_version': 1}]:
            g = copy.deepcopy(self.graph)
            g['edges'].append(edge)
            with self.assertRaises(ValueError):
                c.validate(g, 'dependencies')

    def test_ready_module_requires_artifact_and_check(self):
        self.state['modules']['planning']['status'] = 'ready'
        with self.assertRaises(ValidationError):
            c.validate(self.state, 'state')

    def test_blocked_module_requires_reason(self):
        self.state['modules']['planning']['status'] = 'blocked'
        with self.assertRaises(ValidationError):
            c.validate(self.state, 'state')


if __name__ == '__main__':
    unittest.main()

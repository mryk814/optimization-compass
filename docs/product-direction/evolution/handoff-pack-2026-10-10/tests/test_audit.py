from pathlib import Path
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest

def load(name):
    path=Path(__file__).resolve().parents[1]/'tools'/f'{name}.py'
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
A=load('audit_repository'); N=load('verify_numeric_examples')
class AuditTests(unittest.TestCase):
    def test_read_only_and_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); repo=root/'repo'; db=repo/'src/optimization_compass/resources/knowledge.sqlite'; db.parent.mkdir(parents=True)
            con=sqlite3.connect(db); con.execute('CREATE TABLE methods(method_id TEXT, name_ja TEXT, name_en TEXT)')
            con.execute('INSERT INTO methods VALUES (?,?,?)',('M_TEST','試験法','Test Method')); con.commit(); con.close()
            before=hashlib.sha256(db.read_bytes()).hexdigest()
            scope=root/'scope.json'; scope.write_text(json.dumps({'scope_version':'fixture','topics':[
                {'topic_id':'TOPIC_TEST','title_en':'Test Method','aliases':[]},
                {'topic_id':'TOPIC_UNKNOWN','title_en':'Unknown Method','aliases':[]}]}),encoding='utf-8')
            report=A.audit(repo,scope)
            self.assertEqual(before,hashlib.sha256(db.read_bytes()).hexdigest())
            self.assertEqual(report['database']['table_rows']['methods'],1)
            self.assertEqual(report['mapping_candidates'][0]['mapping_status'],'auto_exact_candidate')
            self.assertEqual(report['mapping_candidates'][1]['mapping_status'],'needs_semantic_review')
            self.assertIsNone(report['approved_scope_coverage'])
            self.assertFalse(report['modified_repository'])
    def test_ambiguous_not_approved(self):
        methods=[{'method_id':'M1','name_en':'Twin'},{'method_id':'M2','name_en':'Twin'}]
        rows=A.candidate_mapping([{'topic_id':'X','title_en':'Twin','aliases':[]}],methods)
        self.assertEqual(rows[0]['mapping_status'],'ambiguous')
        self.assertFalse(rows[0]['approved_coverage'])
    def test_unicode_matching(self):
        self.assertEqual(A.normalized('Ｌ－ＢＦＧＳ'),A.normalized('L-BFGS'))
    def test_numeric_fixtures(self):
        self.assertEqual(N.verify()['status'],'passed')
if __name__=='__main__': unittest.main()

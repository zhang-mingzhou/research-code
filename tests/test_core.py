import unittest,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'agent'))
from run_agent import validate
class AgentTests(unittest.TestCase):
    def setUp(self):
        pack=json.loads((ROOT/'agent/sources.json').read_text(encoding='utf8'))
        self.sources={s['id']:s for s in pack['sources']}
        self.brief=(ROOT/'agent/runs/max_steps_6/final-brief.md').read_text(encoding='utf8')
    def test_complete(self):self.assertTrue(validate(self.brief,{'S01','S02','S03'},self.sources)['pass'])
    def test_unread_source_rejected(self):self.assertFalse(validate(self.brief,{'S01','S02'},self.sources)['pass'])
    def test_fake_citation_rejected(self):self.assertFalse(validate(self.brief.replace('[S03:E01]','[S99:E01]'),{'S01','S02','S03'},self.sources)['pass'])
    def test_changed_claim_rejected(self):self.assertFalse(validate(self.brief.replace('無須重新訓練模型','已證明所有模型均有效'),{'S01','S02','S03'},self.sources)['pass'])
if __name__=='__main__':unittest.main()

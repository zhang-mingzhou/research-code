import unittest,sys,importlib.util
from pathlib import Path
HAS_ML=bool(importlib.util.find_spec('torch') and importlib.util.find_spec('transformers'))
@unittest.skipUnless(HAS_ML,'Model dependencies not installed')
class VCDTests(unittest.TestCase):
    def test_numeric_reference(self):
        import torch
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
        from run_vcd import contrast_logits
        clean=torch.tensor([3.,2.,0.]);noisy=torch.tensor([2.,0.,0.])
        scores=contrast_logits(clean,noisy,mode='vcd')
        self.assertTrue(torch.allclose(scores[:2],torch.tensor([4.,4.])))
        self.assertTrue(torch.isneginf(scores[2]))
        self.assertEqual(contrast_logits(clean,noisy,mode='apc_only').argmax(),clean.argmax())
    def test_answer_parser_does_not_guess(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
        from run_vcd import parse_answer
        self.assertEqual(parse_answer(' Yes.'),'yes')
        self.assertEqual(parse_answer('I cannot tell.'),'invalid')
if __name__=='__main__':unittest.main()

"""Verify saved evidence without loading a model or requiring network."""
import json,hashlib,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    rows=[json.loads(x) for x in (ROOT/'results/vcd/predictions.jsonl').read_text(encoding='utf8').splitlines()]
    assert len(rows)==432
    assert len({(r['sample_id'],r['method']) for r in rows})==432
    assert len({(r['image'],r['text']) for r in rows})==108
    assert all(r['correct']==(r['prediction']==r['label']) for r in rows)
    manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf8'))
    checked=0
    for image in manifest['images']:
        p=ROOT/'data/images'/image['filename']
        if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==image['sha256'];checked+=1
    summary=json.loads((ROOT/'results/vcd/summary.json').read_text(encoding='utf8'))
    assert hashlib.sha256((ROOT/'results/vcd/predictions.jsonl').read_bytes()).hexdigest()==summary['predictions_sha256']
    for budget in [3,6]:
        out=ROOT/f'agent/runs/max_steps_{budget}'
        prov=json.loads((out/'provenance.json').read_text(encoding='utf8'))
        assert not prov['teacher_fixture'] and not prov['model_used']
        assert hashlib.sha256((ROOT/'agent/sources.json').read_bytes()).hexdigest()==prov['source_pack_sha256']
        assert json.loads((out/'validation.json').read_text(encoding='utf8'))['pass']==(budget==6)
    print(f'PASS: 432 model records; 108 unique tasks; {checked}/12 local image hashes; Agent outcomes and provenance')
if __name__=='__main__':main()

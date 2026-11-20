import json,csv,random,statistics,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def metrics(rows):
    n=len(rows);tp=sum(r['prediction']=='yes' and r['label']=='yes' for r in rows);fp=sum(r['prediction']=='yes' and r['label']=='no' for r in rows)
    fn=sum(r['prediction']!='yes' and r['label']=='yes' for r in rows);tn=sum(r['prediction']=='no' and r['label']=='no' for r in rows)
    precision=tp/(tp+fp) if tp+fp else 0;recall=tp/(tp+fn) if tp+fn else 0
    return dict(n=n,accuracy=sum(r['correct'] for r in rows)/n,precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0,yes_ratio=sum(r['prediction']=='yes' for r in rows)/n,invalid=sum(r['prediction']=='invalid' for r in rows),tp=tp,fp=fp,fn=fn,tn=tn)
def main():
    out=ROOT/'results/vcd';rows=[json.loads(x) for x in (out/'predictions.jsonl').read_text(encoding='utf8').splitlines()]
    assert len(rows)==432,'Incomplete run'
    table=[];deltas=[];changes=[]
    for split in ['random','adversarial']:
        for method in ['regular','apc_only','vcd']:
            group=[r for r in rows if r['split']==split and r['method']==method]
            table.append(dict(split=split,method=method,**metrics(group)))
        indexed={(r['sample_id'],r['method']):r for r in rows if r['split']==split}
        image_deltas={}
        for sample_id in sorted({r['sample_id'] for r in rows if r['split']==split}):
            b=indexed[(sample_id,'regular')];v=indexed[(sample_id,'vcd')];a=indexed[(sample_id,'apc_only')]
            assert b['prediction']==a['prediction'],'Greedy APC should preserve argmax'
            image_deltas.setdefault(b['image'],[]).append(int(v['correct'])-int(b['correct']))
            if b['prediction']!=v['prediction']:changes.append({'split':split,'sample_id':sample_id,'image':b['image'],'question':b['text'],'label':b['label'],'regular':b['prediction'],'vcd':v['prediction'],'direction':'improved' if v['correct'] else 'worsened'})
        averages=[statistics.mean(x) for x in image_deltas.values()];rng=random.Random(20261120)
        boot=sorted(statistics.mean(rng.choices(averages,k=len(averages))) for _ in range(2000))
        deltas.append({'split':split,'delta_accuracy':statistics.mean(averages),'cluster_bootstrap_95_low':boot[49],'cluster_bootstrap_95_high':boot[1949],'clusters':len(averages),'replicates':2000,'interpretation':'Exploratory image-cluster interval; small sample and only one noise seed per image.'})
    for filename,data in [('metrics.csv',table),('paired_changes.csv',changes),('bootstrap.csv',deltas)]:
        with (out/filename).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0] if data else ['sample_id']);w.writeheader();w.writerows(data)
    summary={'metrics':table,'deltas':deltas,'changed_answers':changes,'corrected':sum(x['direction']=='improved' for x in changes),'damaged':sum(x['direction']=='worsened' for x in changes),'distinct_images':len({r['image'] for r in rows}),'predictions_sha256':hashlib.sha256((out/'predictions.jsonl').read_bytes()).hexdigest()}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

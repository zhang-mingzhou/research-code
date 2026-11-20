"""Download a predetermined image-cluster sample, without observing predictions."""
import argparse, json, random, urllib.request, hashlib,base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req,timeout=60) as r:path.write_bytes(r.read())
                break
            except Exception:
                if attempt==2:
                    if 'raw.githubusercontent.com/AoiDragon/POPE/' not in url:raise
                    suffix=url.split('/POPE/')[1];ref,relative=suffix.split('/',1)
                    api=f'https://api.github.com/repos/AoiDragon/POPE/contents/{relative}?ref={ref}'
                    payload=json.load(urllib.request.urlopen(api,timeout=60))
                    path.write_bytes(base64.b64decode(payload['content']))
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--images',type=int,default=12);parser.add_argument('--seed',type=int,default=20261120)
    args=parser.parse_args();out=ROOT/'data';out.mkdir(exist_ok=True)
    commit='08d957b917e5a378a2f99d35b6293c536a66298b';groups={};records=[];sources=[]
    for split in ['random','adversarial']:
        path=out/f'coco_pope_{split}.json'
        url=f'https://raw.githubusercontent.com/AoiDragon/POPE/{commit}/output/coco/coco_pope_{split}.json'
        digest=download(url,path)
        rows=[json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]
        groups[split]=rows;sources.append({'split':split,'url':url,'sha256':digest})
    common=sorted(set(r['image'] for r in groups['random']) & set(r['image'] for r in groups['adversarial']))
    selected=sorted(random.Random(args.seed).sample(common,args.images))
    for split,rows in groups.items():
        for row in rows:
            if row['image'] in selected:records.append(dict(row,split=split,sample_id=f"{split}-{row['question_id']}"))
    (out/'questions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf8')
    def get_image(name):
        url='https://s3.amazonaws.com/images.cocodataset.org/val2014/'+name
        digest=download(url,out/'images'/name)
        print('IMAGE',name,flush=True)
        return {'filename':name,'url':url,'sha256':digest}
    with ThreadPoolExecutor(4) as ex:images=list(ex.map(get_image,selected))
    manifest={'selection_seed':args.seed,'sampling_unit':'image','selected_before_inference':True,'image_count':len(selected),'question_count':len(records),'pope_commit':commit,'question_sources':sources,'images':images,'warning':'Small diagnostic subset; not the complete POPE benchmark. Images may overlap model pretraining.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print('DATA READY',len(selected),len(records),flush=True)
if __name__=='__main__':main()

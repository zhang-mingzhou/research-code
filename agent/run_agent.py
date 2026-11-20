"""Offline deterministic tool-loop prototype. Not an LLM or teacher fixture."""
from pathlib import Path
import argparse,json,hashlib,re,csv,datetime
ROOT=Path(__file__).resolve().parent
CONTRACT={'version':'student-contract-v1','task':'搜尋指定離線來源包，讀取三個相關來源，產出一頁含 citation 的研究簡報。','query':['視覺','幻覺','評估'],'required_sources':3,'max_characters':1200,'required_sections':['研究問題','證據整理','限制與下一步'],'network_allowed':False,'writes':'selected output directory only','teacher_approved':False}
SCHEMA={'search':{'query':'list[str]','returns':'ranked source metadata'},'read':{'source_id':'allowlisted source ID','returns':'complete source card'},'compose':{'returns':'brief built only from observed evidence'},'validate':{'returns':'final-state checks'}}
def save_json(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf8')
def validate(brief,read_ids,sources):
    refs=re.findall(r'\[(S\d+:E\d+)\]',brief)
    citations_ok=bool(refs)
    evidence_ok=True
    for ref in refs:
        sid,eid=ref.split(':')
        if sid not in read_ids or sid not in sources or eid not in sources[sid]['evidence']:citations_ok=False
    for line in brief.splitlines():
        if line.startswith('- '):
            m=re.fullmatch(r'- (.+) \[(S\d+):(E\d+)\]',line)
            if not m or m[2] not in sources or sources[m[2]]['evidence'].get(m[3])!=m[1]:evidence_ok=False
    checks={'brief_exists':bool(brief),'three_sources_read':len(read_ids)>=3,'three_sources_cited':len({r.split(':')[0] for r in refs})>=3,'citation_ids_valid_and_read':citations_ok,'claims_match_source_cards':evidence_ok and bool(refs),'length_within_limit':0<len(brief)<=CONTRACT['max_characters'],'sections_present':all(x in brief for x in CONTRACT['required_sections'])}
    return {'pass':all(checks.values()),'checks':checks,'read_count':len(read_ids),'citation_count':len(refs),'characters':len(brief),'scope':'Checks source-card consistency and final state; does not independently verify original papers or scientific truth.'}
def run(max_steps,out):
    out.mkdir(parents=True,exist_ok=True)
    pack=json.loads((ROOT/'sources.json').read_text(encoding='utf8'));sources={s['id']:s for s in pack['sources']}
    observed={};ranked=[];brief='';trace=[];results=[];state='search';validation=None
    for step in range(1,max_steps+1):
        if state=='search':
            name='search';args={'query':CONTRACT['query']}
            ranked=sorted([(len(set(s['tags'])&set(args['query'])),sid) for sid,s in sources.items()],key=lambda x:(-x[0],x[1]))
            ranked=[sid for score,sid in ranked if score>0][:3]
            result=[{'id':sid,'title':sources[sid]['title']} for sid in ranked];state='read'
        elif state=='read':
            name='read';sid=next(s for s in ranked if s not in observed);args={'source_id':sid};result=sources[sid];observed[sid]=result
            if len(observed)==3:state='compose'
        elif state=='compose':
            name='compose';args={}
            brief='# 視覺語言模型幻覺研究簡報\n\n## 研究問題\n如何區分評測分數變化與可由視覺證據支持的改善？\n\n## 證據整理\n'
            for sid,s in observed.items():brief+=f"- {s['evidence']['E01']} [{sid}:E01]\n"
            brief+='\n## 限制與下一步\n'
            for sid,s in observed.items():brief+=f"- {s['evidence']['E02']} [{sid}:E02]\n"
            brief+='\n來源：\n'+''.join(f"{sid}：{s['title']}；{s['url']}\n" for sid,s in observed.items())
            (out/'final-brief.md').write_text(brief,encoding='utf8');result={'path':'final-brief.md','characters':len(brief)};state='validate'
        else:
            name='validate';args={};validation=validate(brief,set(observed),sources);result=validation;state='done'
        trace.append({'step':step,'tool':name,'arguments':args,'observation_id':f'o{step}','state_after':state})
        results.append({'observation_id':f'o{step}','tool':name,'result':result})
        if state=='done':break
    # External scorer is identical across budgets and is not an agent tool call.
    assessment=validate(brief,set(observed),sources)
    if not brief:(out/'final-brief.md').write_text('',encoding='utf8')
    for name,rows in [('trajectory.jsonl',trace),('tool-results.jsonl',results)]:
        (out/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
    save_json(out/'task-contract.json',CONTRACT);save_json(out/'tool-schema.json',SCHEMA);save_json(out/'validation.json',assessment)
    prov={'generated_by':'student_authored_deterministic_tool_loop','model_used':False,'api_used':False,'network_used':False,'teacher_fixture':False,'teacher_approved':False,'max_steps':max_steps,'source_pack_sha256':hashlib.sha256((ROOT/'sources.json').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'validator_version':'student-validator-v1','brief_generation':'deterministic assembly of student-authored source-card paraphrases','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save_json(out/'provenance.json',prov)
    row={'max_steps':max_steps,'tool_calls':len(trace),'sources_read':len(observed),'citations':assessment['citation_count'],'final_state_pass':assessment['pass'],'in_loop_validation':validation is not None}
    with (out/'evaluation.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=row);w.writeheader();w.writerow(row)
    note=('三步預算在讀取第二個來源後耗盡，尚未讀完三個來源及生成簡報。' if not assessment['pass'] else '六步完成搜尋、三次讀取、生成簡報和校驗。')
    (out/'error-note.md').write_text('# 完成狀態與失敗分析\n\n'+note+'\n\n本結果來自固定規則控制器，並非真實 LLM Agent，也不是教師 fixture。六步為本工具拆分下的最短完整路徑；不能推論六步對其他任務最優。校驗器檢查引用 ID、讀取紀錄、來源卡片一致性與篇幅，不能保證原論文理解正確。下一步：取得教師來源包和 validator 後，用相同控制器與預算重跑，另測引用遺漏及錯誤來源。\n',encoding='utf8')
    return row
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='runs');args=p.parse_args()
    out=ROOT/args.output
    rows=[run(n,out/f'max_steps_{n}') for n in [3,6]]
    with (out/'comparison.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(json.dumps(rows,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

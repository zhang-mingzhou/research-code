"""Simplified VCD method reproduction on SmolVLM, with actual model inference.

The diffusion schedule and logit formula follow Leng et al. CVPR 2024.
Adaptations: smaller backbone; greedy decoding; 12-image POPE subset;
stop after an explicit yes/no answer. No training and no fabricated predictions.
"""
import argparse,json,time,hashlib,platform,re,math
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoProcessor,AutoModelForVision2Seq
import transformers

ROOT=Path(__file__).resolve().parents[1]
def contrast_logits(clean,noisy,alpha=1.0,beta=0.1,mode='vcd'):
    scores=(1+alpha)*clean-alpha*noisy if mode=='vcd' else clean.clone()
    if mode!='regular':scores=scores.masked_fill(clean < clean.max()+math.log(beta),-float('inf'))
    return scores

def noise_image(x,seed,step=500):
    betas=torch.sigmoid(torch.linspace(-6,6,1000,dtype=torch.float32))*(0.005-0.00001)+0.00001
    a=torch.cumprod(1-betas,dim=0)[step]
    noise=torch.randn(x.shape,generator=torch.Generator().manual_seed(seed),dtype=torch.float32)
    return (a.sqrt()*x.cpu().float()+(1-a).sqrt()*noise).to(device=x.device,dtype=x.dtype)

def parse_answer(text):
    match=re.match(r'^\s*(yes|no)\b',text,re.I)
    return match.group(1).lower() if match else 'invalid'

def main():
    a=argparse.ArgumentParser();a.add_argument('--model',default='HuggingFaceTB/SmolVLM-256M-Instruct');a.add_argument('--revision',default='d039ab0d4b9311b617e8ffec1d06c8464364aeb3');a.add_argument('--limit',type=int);a.add_argument('--output',default='results/vcd');args=a.parse_args()
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True)
    questions=[json.loads(s) for s in (ROOT/'data/questions.jsonl').read_text(encoding='utf8').splitlines()]
    if args.limit:questions=questions[:args.limit]
    device='cuda' if torch.cuda.is_available() else 'cpu';dtype=torch.float16 if device=='cuda' else torch.float32
    torch.manual_seed(20261120);torch.set_num_threads(4)
    processor=AutoProcessor.from_pretrained(args.model,revision=args.revision)
    model=AutoModelForVision2Seq.from_pretrained(args.model,revision=args.revision,torch_dtype=dtype,attn_implementation='eager').to(device).eval()
    started=time.time();predictions=[];cache={}
    with (out/'predictions.jsonl').open('w',encoding='utf8') as stream,torch.inference_mode():
        for idx,q in enumerate(questions):
            image=Image.open(ROOT/'data/images'/q['image']).convert('RGB')
            prompt=q['text']+' Answer yes or no.'
            messages=[{'role':'user','content':[{'type':'image'},{'type':'text','text':prompt}]}]
            text=processor.apply_chat_template(messages,add_generation_prompt=True)
            inputs=processor(text=text,images=[image],return_tensors='pt').to(device)
            inputs['pixel_values']=inputs['pixel_values'].to(dtype)
            image_seed=int(hashlib.sha256(q['image'].encode()).hexdigest()[:8],16)
            distorted=noise_image(inputs['pixel_values'],image_seed)
            for mode in ['regular','apc_only','vcd']:
                generated=[];token_records=[]
                for step in range(8):
                    key=(q['image'],prompt,tuple(generated))
                    if key not in cache:
                        extra=torch.tensor([generated],dtype=torch.long,device=device)
                        ids=torch.cat([inputs['input_ids'],extra],dim=1)
                        mask=torch.cat([inputs['attention_mask'],torch.ones_like(extra)],dim=1)
                        params={**inputs,'input_ids':ids,'attention_mask':mask,'use_cache':False}
                        clean=model(**params).logits[0,-1].float()
                        noisy=model(**{**params,'pixel_values':distorted}).logits[0,-1].float()
                        cache[key]=(clean.cpu(),noisy.cpu())
                    clean,noisy=cache[key]
                    scores=contrast_logits(clean,noisy,mode=mode)
                    token=int(scores.argmax());generated.append(token)
                    decoded=processor.tokenizer.decode(generated,skip_special_tokens=True)
                    token_records.append({'token_id':token,'text':processor.tokenizer.decode([token]),'clean_logit':float(clean[token]),'noisy_logit':float(noisy[token]),'selected_score':float(scores[token]),'retained_vocabulary':int((clean>=clean.max()+math.log(0.1)).sum()) if mode!='regular' else len(clean)})
                    if parse_answer(decoded)!='invalid' or token==processor.tokenizer.eos_token_id:break
                row={**q,'method':mode,'prompt':prompt,'raw_response':decoded,'prediction':parse_answer(decoded),'correct':parse_answer(decoded)==q['label'],'noise_seed':image_seed,'generated_tokens':token_records}
                predictions.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            if idx%6==0 or idx==len(questions)-1:print(f'PROGRESS {idx+1}/{len(questions)} elapsed={time.time()-started:.1f}s',flush=True)
    prov={'model_id':'HuggingFaceTB/SmolVLM-256M-Instruct','revision':args.revision,'model_used':True,'api_used':False,'teacher_fixture':False,'python':platform.python_version(),'torch':torch.__version__,'transformers':transformers.__version__,'device':device,'gpu':torch.cuda.get_device_name(0) if device=='cuda' else None,'dtype':str(dtype),'alpha':1.0,'beta':0.1,'noise_step':500,'decoding':'greedy; stop at leading yes/no or 8 tokens','question_count':len(questions),'elapsed_seconds':time.time()-started,'max_cuda_allocated_mb':torch.cuda.max_memory_allocated()/1024**2 if device=='cuda' else None,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'shared_forward_cache':True,'timing_caution':'Forward logits are cached across conditions; wall time is not a per-method speed benchmark.','scope':'Core algorithm port, not reproduction of original paper tables.'}
    (out/'provenance.json').write_text(json.dumps(prov,indent=2),encoding='utf8')
    print('RUN COMPLETE',len(predictions),flush=True)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""R10 fixed-code transfer to existing public yeast GPCA/MAPPIT masks and within-study human assay1.

NEVER claim prospective blinding, unpublished data, historical neural-tail restoration,
or proof of PPI unknown-edge generalization. Policy code from frozen R9 unchanged.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,importlib.util,json,collections,math,platform,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
R9P=ROOT/'analysis'/'source'/'r9_adaptive_pilot.py'
spec=importlib.util.spec_from_file_location('r9_frozen',R9P)
r9=importlib.util.module_from_spec(spec);sys.modules[spec.name]=r9;spec.loader.exec_module(r9)
r8=r9.r8
BUDGETS=(0,3,5,8,10,15,20,30)
STATIC=('random_informative','coverage','disagreement','dopt','fair_contrast')
FROZEN_ADAPTIVE=('adaptive_empirical','adaptive_sparse','adaptive_half')
NEW_COMPARATOR=('greedy_expected_cert',)
METHODS=STATIC+FROZEN_ADAPTIVE+NEW_COMPARATOR
PRIMARY='adaptive_empirical'; RANDOM='random_informative'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_yeast():
    path=ROOT/'input'/'YEAST_GPCA_MAPPIT_PINNED_DERIVED_MASKS.txt'
    assert sha(path)=='ce2338d66387b59c7321c3be5827efb180436054f2b96564910c363549df2396'
    out=[]
    for line in path.read_text().strip().splitlines():
        i,assay,bait,n,h,trip=line.split('|');n=int(n);h=int(h)
        bits=np.array([int(trip[j],36) for j in range(0,len(trip),2)],dtype=np.int16)
        y=np.array([int(trip[j+1]) for j in range(0,len(trip),2)],dtype=np.int16)
        X=np.column_stack([((bits>>j)&1).astype(np.int16) for j in range(5)])
        assert len(y)==len(bits)==n and int(y.sum())==h and (X.sum(axis=0)==10).all()
        out.append({'panel':f'Yeast_{i}_{assay}','source':'Yeast_2026_GPCA_MAPPIT',
                    'anchor':bait,'assay':assay,'X':X,'y':y,'n':n,'h':h})
    assert len(out)==74 and len({x['anchor'] for x in out})==47
    assert sum(x['h']>0 for x in out)==33
    return out


def load_human_v1():
    # Copy the eligibility and structural-scoring rules from the frozen R8 producer.
    # This is an assay-heldout retrospective comparison, not a new independent study.
    root=ROOT/'analysis'/'r8_reference'/'input'
    for name,pin in r8.PINS.items():
        assert r8.gitblob((root/name).read_bytes())==pin
    G=collections.defaultdict(set);edges=set()
    with (root/'HuRI.csv').open(newline='',encoding='utf-8-sig') as f:
        for z in csv.DictReader(f):
            a,b=z['source'],z['target'];q=tuple(sorted((a,b)))
            assert q not in edges;edges.add(q);G[a];G[b]
            if a!=b:G[a].add(b);G[b].add(a)
    assert len(edges)==52548 and len(G)==8272
    grouped=collections.defaultdict(list);seen=set();stat=collections.Counter()
    with (root/'PPI_prediction_validation_result_20210624.xls').open(newline='',encoding='utf-8-sig') as f:
        for z in csv.DictReader(f,delimiter='\t'):
            a,b=z['source'],z['target'];q=tuple(sorted((a,b)))
            assert q not in seen;seen.add(q);stat['raw']+=1
            if a==b or q in edges or a not in G or b not in G:continue
            v=z['score_assay1']
            if v not in ('Positive','Negative'):continue
            C=sorted(G[a]&G[b]);cn=len(C)
            sc=(math.fsum(1/math.log(len(G[w])) for w in C if len(G[w])>1),float(cn),
                math.fsum(1/len(G[w]) for w in C),cn/len(G[a]|G[b]) if G[a] or G[b] else 0.,
                float(len(G[a])*len(G[b])))
            grouped[a].append({'prey':b,'scores':sc,'y':int(v=='Positive')})
            stat['eligible']+=1
    assert stat['raw']==3276 and stat['eligible']==2355
    panels=[]
    for bait,rows in sorted(grouped.items()):
        if len(rows)<11:continue
        rr=sorted(rows,key=lambda q:q['prey'])
        orig={'id':f'{bait}_v1','bait':bait,'prey':[r['prey']for r in rr],
              'scores':np.array([r['scores'] for r in rr]),
              'y':np.array([r['y']for r in rr],dtype=np.int16)}
        X=r8.design(orig,0)
        panels.append({'panel':orig['id'],'source':'Human_withinstudy_assay1',
                       'anchor':bait,'assay':'v1','X':X,'y':orig['y'],
                       'n':len(rr),'h':int(orig['y'].sum())})
    assert panels and all(x['n']>=11 for x in panels)
    return panels


def one_step_order(X,y,seed,pid,maxB=30):
    # A stronger matched heuristic comparator introduced in this R10 protocol.
    # It cannot read unknown labels: only X, known indices, and their values enter selection.
    prior=r9.seed_permutation(len(y),seed,pid)
    ranking={j:k for k,j in enumerate(prior)}
    n,m=X.shape
    useful=np.flatnonzero((X.sum(axis=1)>0)&(X.sum(axis=1)<m))
    reps=[g[0] for g in r8.action_groups(X)]
    known=[];values=[];order=[]
    for _ in range(min(len(useful),maxB)):
        obs=np.zeros(n,bool);obs[known]=True
        U=np.array([i for i in prior if not obs[i] and 0<X[i].sum()<m],dtype=int)
        if not len(U):break
        if len(reps)<2:
            selected=int(U[0])
        else:
            low=r9.exact_low(X,known,values)[np.ix_(reps,reps)]
            A=X[U][:,reps]
            D=A[:,:,None]-A[:,None,:]
            neg=np.minimum(D,0)
            lo0=low[None,:,:]-neg
            lo1=low[None,:,:]+D-neg
            off=np.eye(len(reps),dtype=bool)[None,:,:]
            def objective(LL):
                win=np.all((LL>0)|off,axis=2).any(axis=1).astype(float)
                i,j=np.triu_indices(len(reps),1)
                pairs=np.sum((LL[:,i,j]>0)|(LL[:,j,i]>0),axis=1).astype(float)
                return win,pairs
            w0,p0=objective(lo0);w1,p1=objective(lo1)
            p=(1+sum(values))/(2+len(values))
            # Lexicographic expected strict action certificate then pair knowledge.
            ww=(1-p)*w0+p*w1
            pp=(1-p)*p0+p*p1
            t=np.max(ww)
            best=np.flatnonzero(ww>=t-1e-12)
            if len(best)>1:
                pp_best=pp[best];best=best[pp_best>=pp_best.max()-1e-12]
            selected=min([int(U[i]) for i in best],key=lambda i:ranking[i])
        assert selected not in known
        known.append(selected);values.append(int(y[selected]));order.append(selected)
    return order


def get_order(board,method,seed,maxB=30):
    X=board['X'];y=board['y'];pid=board['panel'];n=len(y)
    inf=int(np.sum((X.sum(axis=1)>0)&(X.sum(axis=1)<5)))
    cap=min(maxB,inf)
    if method=='greedy_expected_cert':return one_step_order(X,y,seed,pid,maxB=cap)
    if method in STATIC:return r8.order_static(X,method,seed,pid,cap)
    # Frozen R9 choose_next; only stop early to avoid computing unused >cap labels.
    priority=r9.seed_permutation(n,seed,pid);known=[];values=[]
    for _ in range(cap):
        i=r9.choose_next(X,known,values,priority,method)
        assert i is not None and i not in known
        known.append(i);values.append(int(y[i]))
    return known


def score_order_prefix(X,y,order):
    groups=r8.action_groups(X);reps=[g[0] for g in groups];full=(X.T@y)
    tm=int(np.sum(full==np.max(full))==1)
    cls=full[reps];ta=int(len(reps)>1 and np.sum(cls==np.max(cls))==1)
    low=np.minimum(X[:,:,None]-X[:,None,:],0).sum(axis=0).astype(int)
    off=~np.eye(X.shape[1],dtype=bool);offa=~np.eye(len(reps),dtype=bool)
    out={};model_stop=None;action_stop=None
    for t in range(len(order)+1):
        sm=int(np.any(np.all((low>0)|~off,axis=1)))
        sa=int(len(reps)>1 and np.any(np.all((low[np.ix_(reps,reps)]>0)|~offa,axis=1)))
        assert sm<=tm and sa<=ta
        if sm and model_stop is None:model_stop=t
        if sa and action_stop is None:action_stop=t
        if t in BUDGETS:out[t]=(sm,sa)
        if t==len(order):break
        i=order[t];diff=X[i,:,None]-X[i,None,:]
        low+=diff*y[i]-np.minimum(diff,0)
    for b in BUDGETS:
        if b not in out:out[b]=(sm,sa)
    return out,model_stop,action_stop,tm,ta


def check_oracle_masks(board,order,rr,maxB=30):
    X=board['X'];y=board['y'];full=X.T@y
    groups=r8.action_groups(X);reps=[g[0] for g in groups]
    tmod=int((full==max(full)).sum()==1)
    tact=int(len(reps)>1 and (full[reps]==max(full[reps])).sum()==1)
    assert tmod==rr[3] and tact==rr[4]
    inf=sum(0<X[i].sum()<5 for i in range(len(y)))
    assert len(order)==len(set(order))==min(inf,maxB)
    c=r8.certify(X,{int(i):int(y[i]) for i in order})
    assert int(bool(c['strict_model']))==rr[0][maxB][0]
    assert int(bool(c['strict_action']))==rr[0][maxB][1]
    return tmod,tact

def run(panels,source,seeds,out,seed_start=0):
    rows=[];started=time.monotonic()
    raw=out/f'{source}_per_seed.csv.gz'
    with gzip.open(raw,'wt',newline='') as f:
        fields=['source','panel','anchor','assay','n','h','informative','true_model_winner','true_action_winner',
                'method','seed','budget','cost','certified_model','certified_action','model_stop','action_stop']
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for pidx,p in enumerate(panels):
            X=p['X'];y=p['y'];n=len(y);inf=int(sum(0<X[i].sum()<5 for i in range(n)))
            for seed in range(seed_start,seed_start+seeds):
                for method in METHODS:
                    order=get_order(p,method,seed)
                    outputs,ms,as_,tm,ta=score_order_prefix(X,y,order)
                    check_oracle_masks(p,order,(outputs,ms,as_,tm,ta))
                    for b in BUDGETS:
                        mod,act=outputs[b]
                        z={'source':source,'panel':p['panel'],'anchor':p['anchor'],
                           'assay':p['assay'],'n':n,'h':p['h'],'informative':inf,
                           'true_model_winner':tm,'true_action_winner':ta,
                           'method':method,'seed':seed,'budget':b,'cost':min(b,inf),
                           'certified_model':mod,'certified_action':act,
                           'model_stop':ms if ms is not None else -1,
                           'action_stop':as_ if as_ is not None else -1}
                        w.writerow(z)
                        if b in (5,8,10,15,20):rows.append(z)
            if pidx%15==0: print(source,pidx+1,'/',len(panels),'seconds',round(time.monotonic()-started,2),flush=True)
    df=pd.DataFrame(rows)
    df.to_csv(out/f'{source}_budget_subset.csv',index=False)
    s=df.groupby(['budget','method'],as_index=False).agg(
        mean_certified_action=('certified_action','sum'),mean_certified_model=('certified_model','sum'),
        actual_cost=('cost','sum'))
    s['mean_certified_action']/=seeds;s['mean_certified_model']/=seeds;s['actual_cost']/=seeds
    s['n_panels']=len(panels);s['n_anchor']=len({x['anchor']for x in panels});s['seeds']=seeds
    s['true_action_winners']=sum(int(len(r8.action_groups(p['X']))>1 and
        np.sum((p['X'].T@p['y'])[[g[0] for g in r8.action_groups(p['X'])]]==
        np.max((p['X'].T@p['y'])[[g[0] for g in r8.action_groups(p['X'])]]))==1) for p in panels)
    s.to_csv(out/f'{source}_summary.csv',index=False)
    return df,s,{'panels':len(panels),'anchors':len({p['anchor']for p in panels}),
                 'zero_hc':sum(p['h']==0 for p in panels),'all_positive':sum(p['h']>0 for p in panels),
                 'unique_candidate_assay_anchor_memberships':sum(p['n'] for p in panels),
                 'informative_total':sum(sum(0<p['X'][i].sum()<5 for i in range(p['n'])) for p in panels),
                 'runtime_seconds':time.monotonic()-started,'raw_file':raw.name,
                 'sha256_gz':sha(raw)}


def analyze_primary(df,source,B=10,boots=5000):
    sub=df[df.budget==B].copy()
    per=sub.groupby(['anchor','panel','assay','method'],as_index=False).agg(
        certified_action=('certified_action','mean'), certified_model=('certified_model','mean'),
        true_action_winner=('true_action_winner','first'),
        informative=('informative','first'),h=('h','first'))
    pv=per.pivot_table(index=['anchor','panel','assay'],columns='method',values='certified_action').reset_index()
    dat=[]
    for base in [RANDOM,'coverage','disagreement','dopt','fair_contrast','greedy_expected_cert','adaptive_sparse','adaptive_half']:
        g=pv[[PRIMARY,base,'anchor']].copy()
        g['difference']=g[PRIMARY]-g[base]
        dsum=g.groupby('anchor')['difference'].sum()
        rng=np.random.default_rng(20261112)
        vals=dsum.to_numpy();K=len(vals)
        samples=rng.integers(0,K,size=(boots,K))
        totals=vals[samples].sum(axis=1)
        dat.append({'source':source,'cap':B,'a':PRIMARY,'b':base,
                    'mean_difference_panel_count':float(np.sum(vals)),
                    'cluster_bootstrap_95_low':float(np.quantile(totals,.025)),
                    'cluster_bootstrap_95_high':float(np.quantile(totals,.975)),
                    'anchor_clusters':K,'n_pos_diff_panels':int(np.sum(g.difference>1e-12)),
                    'n_neg_diff_panels':int(np.sum(g.difference<-1e-12)),
                    'n_neutral_panels':int(np.sum(abs(g.difference)<=1e-12))})
    out=pd.DataFrame(dat)
    return per,pv,out


def self_test():
    tests=r9.self_tests();assert tests==1425
    rng=np.random.default_rng(405)
    for n in (11,18,31):
        for _ in range(10):
            X=rng.integers(0,2,size=(n,5),dtype=np.int16)
            y=rng.integers(0,2,size=n,dtype=np.int16)
            seq=one_step_order(X,y,3,f'test_{n}')
            assert len(seq)==len(set(seq))==min(30,sum(0<X[i].sum()<5 for i in range(n)))
            # Test model permutation invariance of action certificates and greedy order.
            q=np.array([3,1,0,4,2]);assert seq==one_step_order(X[:,q],y,3,f'test_{n}')
            score_order_prefix(X,y,seq)
    return {'frozen_r9_self_tests':tests,'new_greedy_tests':30,'method_count':len(METHODS)}


def main():
    pa=argparse.ArgumentParser();pa.add_argument('--seeds',type=int,default=100);pa.add_argument('--seed-start',type=int,default=0);pa.add_argument('--only',choices=['yeast','human','both'],default='both')
    a=pa.parse_args();out=ROOT/'results'/'chunks'/f'{a.only}_{a.seed_start:03d}_{a.seed_start+a.seeds:03d}';out.mkdir(parents=True,exist_ok=True)
    t=self_test();audit={'phase':'R10_FIXED_CODE_TRANSFER','tests':t,'pre_execution_protocol_sha256':sha(ROOT/'R10_PROTOCOL_FROZEN_BEFORE_EXECUTION.md'),
          'source_masks_sha256':sha(ROOT/'input'/'YEAST_GPCA_MAPPIT_PINNED_DERIVED_MASKS.txt'),
          'frozen_policy_sha256':sha(R9P),
          'python':platform.python_version(), 'numpy':np.__version__, 'pandas':pd.__version__,
          'actual_seeds':a.seeds,'seed_start':a.seed_start,'prior_data_exposure':'YES: retrospective code-frozen transfer, NOT prospective registration'}
    for kind in ['yeast','human']:
        if a.only!='both' and kind!=a.only:continue
        pp=load_yeast() if kind=='yeast' else load_human_v1()
        dat,s,rec=run(pp,kind,a.seeds,out,a.seed_start)
        per,pv,compar=analyze_primary(dat,kind,10)
        per.to_csv(out/f'{kind}_per_panel_means.csv',index=False)
        pv.to_csv(out/f'{kind}_paired_pivot.csv',index=False)
        compar.to_csv(out/f'{kind}_paired_bootstrap.csv',index=False)
        audit[kind]=rec
        print('RESULTS',kind,'\n',s[s.budget==10].to_string(index=False),flush=True)
        print('CONTRASTS',kind,'\n',compar.to_string(index=False),flush=True)
    (out/'R10_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else float(x) if isinstance(x,np.floating) else str(x))+'\n')
    print('PASS',json.dumps(audit,ensure_ascii=False,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else float(x) if isinstance(x,np.floating) else str(x)))

if __name__=='__main__':main()

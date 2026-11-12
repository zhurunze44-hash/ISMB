#!/usr/bin/env python3
"""R9 exploratory adaptive label acquisition on the pinned R8 human Y2H panels.
No hidden outcome is accepted by choose_next; fixed certification endpoint is R8.
This is a retrospective pilot, not independent blind validation.
"""
from __future__ import annotations
import argparse,csv,hashlib,importlib.util,json,time,collections
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent.parent/'r8_reference'
P=BASE/'reanalyze_strict_winners.py'
spec=importlib.util.spec_from_file_location('r8public',P)
r8=importlib.util.module_from_spec(spec);spec.loader.exec_module(r8)
BUDGETS=(0,3,5,8,10,15,20,30)
ADAPTIVE=('adaptive_half','adaptive_sparse','adaptive_empirical')
STATIC=('random_informative','coverage','disagreement')
METHODS=STATIC+ADAPTIVE

def exact_low(X,known,vals):
 obs=np.zeros(X.shape[0],dtype=bool);v=np.zeros(X.shape[0],dtype=int)
 for i,y in zip(known,vals):obs[i]=True;v[i]=int(y)
 ks=X[obs].T@v[obs];D=X[~obs,:,None]-X[~obs,None,:]
 return ks[:,None]-ks[None,:]+np.minimum(D,0).sum(axis=0)

def choose_next(X,known,values,perm_order,method):
 """Only model nominations, revealed values and frozen tie-break order are passed."""
 n,m=X.shape;d=X.sum(axis=1);useful=(d>0)&(d<m)
 obs=np.zeros(n,bool);obs[known]=True
 remaining=[i for i in perm_order if useful[i] and not obs[i]]
 if not remaining:return None
 if method=='adaptive_half':p=.5
 elif method=='adaptive_sparse':p=.1
 elif method=='adaptive_empirical':p=(1+sum(values))/(2+len(values))
 else:raise ValueError(method)
 reps=[g[0] for g in r8.action_groups(X)]
 if len(reps)<2:return remaining[0]
 L=exact_low(X,known,values);Xr=X[:,reps]
 score_known=Xr[known].T@np.array(values,dtype=int) if known else np.zeros(len(reps))
 nom_remaining=np.sum(Xr[~obs],axis=0)
 expected=score_known+p*nom_remaining
 # Candidate fingerprint depends on frozen candidate priority, not model column/name.
 priority_index={i:j for j,i in enumerate(perm_order)}
 action_fingerprint=lambda k:tuple(sorted(priority_index[i] for i in np.flatnonzero(Xr[:,k])))
 candidate_leaders=sorted(range(len(reps)),key=lambda k:(-round(float(expected[k]),12),action_fingerprint(k)))[:min(2,len(reps))]
 w=reps[candidate_leaders[0]];J=[j for j in reps if j!=w]
 requirements=np.maximum(1,1-L[w,J]);priority={i:j for j,i in enumerate(perm_order)}
 idx=np.asarray(remaining,dtype=int)
 D=(X[idx,w,None]-X[np.ix_(idx,J)]).astype(float)
 gain=np.where(D>0,p,np.where(D<0,1-p,0.0))
 s=np.sum(gain/requirements[None,:],axis=1)
 if np.max(s)<1e-12:
  dd=d[idx];s=dd*(m-dd)/max(1,m*m)
 mx=float(np.max(s));choice=min((i for i,v in zip(remaining,s) if v>=mx-1e-12),key=lambda i:priority[i])
 return int(choice)

def seed_permutation(n,seed,panel_id):
 rng=np.random.default_rng(seed+r8.fnv(panel_id));return [int(i) for i in rng.permutation(n)]

def compute_order(X,y,method,seed,pid):
 n=len(y)
 if method in STATIC:return r8.order_static(X,method,seed,pid,n)
 priority=seed_permutation(n,seed,pid);known=[];values=[];out=[]
 inf=int(np.sum((X.sum(axis=1)>0)&(X.sum(axis=1)<X.shape[1])))
 for _ in range(inf):
  idx=choose_next(X,known,values,priority,method)
  assert idx is not None and idx not in known
  known.append(idx);values.append(int(y[idx]));out.append(idx) # AFTER choosing.
 return out

def score_order(X,y,order):
 groups=r8.action_groups(X);reps=[g[0] for g in groups]; full=(X.T@y)
 tm=int(np.sum(full==max(full))==1)
 cls=full[reps];ta=int(len(reps)>1 and np.sum(cls==max(cls))==1)
 low=np.minimum(X[:,:,None]-X[:,None,:],0).sum(axis=0).astype(int)
 out={};model_stop=None;action_stop=None
 off=~np.eye(X.shape[1],dtype=bool);offa=~np.eye(len(reps),dtype=bool)
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
  if b>len(order):out[b]=(sm,sa)
 assert (model_stop is not None)==bool(tm)
 assert (action_stop is not None)==bool(ta)
 return out,model_stop,action_stop,tm,ta

def self_tests():
 rng=np.random.default_rng(391);tests=0
 for n in range(1,8):
  for ii in range(18):
   X=rng.integers(0,2,size=(n,5),dtype=np.int16);y=rng.integers(0,2,size=n,dtype=np.int16)
   perm=seed_permutation(n,ii,'synthetic')
   for method in ADAPTIVE:
    known=[];values=[]
    for t in range(n):
     a=exact_low(X,known,values);b=r8.certify(X,dict(zip(known,values)))['low']
     assert np.array_equal(a,b)
     i2=choose_next(X,known,values,perm,method)
     if i2 is None:break
     assert i2 not in known
     for permutation in ([3,0,4,2,1],[4,3,2,1,0]):
      assert i2==choose_next(X[:,permutation],known,values,perm,method),(method,'model permutation')
     rowperm=np.arange(n)[::-1];inv=np.argsort(rowperm)
     assert int(inv[i2])==choose_next(X[rowperm],[int(inv[j]) for j in known],values,[int(inv[j]) for j in perm],method),(method,'row permutation')
     known.append(i2);values.append(int(y[i2]));tests+=1
 return tests

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--tie-seeds',default='0');ap.add_argument('--acq-seeds',type=int,default=100)
 ap.add_argument('--seed-start',type=int,default=0);ap.add_argument('--output',default=str(Path(__file__).resolve().parents[2]/'runs'/'R9_trial'))
 args=ap.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 panels,receipt=r8.read_native();tests=self_tests();rows=[];start=time.monotonic()
 for ts in [int(k) for k in args.tie_seeds.split(',')]:
  for panel in panels:
   X=r8.design(panel,ts);y=panel['y'];n=len(y)
   for method in METHODS:
    for seed in range(args.seed_start,args.seed_start+args.acq_seeds):
     order=compute_order(X,y,method,seed,panel['id'])
     inf=int(np.sum((X.sum(axis=1)>0)&(X.sum(axis=1)<5)))
     assert len(order)==len(set(order))==inf
     values,ms,ac,tm,ta=score_order(X,y,order)
     for budget in BUDGETS:
      model,action=values[budget]
      rows.append({'tie_seed':ts,'panel':panel['id'],'bait':panel['bait'],'assay':panel['assay'],'method':method,'seed':seed,'budget':budget,
           'n':n,'HC':int(sum(y)),'informative':inf,'cost':min(budget,inf),
           'true_model_winner':tm,'true_action_winner':ta,'certified_model':model,'certified_action':action,
           'model_stop':ms if ms is not None else -1,'action_stop':ac if ac is not None else -1})
  print('Completed tie seed',ts,round(time.monotonic()-start,2),'s',flush=True)
 path=out/'R9_SEED_PANEL_RESULTS.csv'
 with path.open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
 groups=collections.defaultdict(list)
 for row in rows:groups[(row['tie_seed'],row['budget'],row['method'])].append(row)
 summary=[]
 for (ts,b,m),g in sorted(groups.items()):
  A=np.array([x['certified_action'] for x in g]);M=np.array([x['certified_model'] for x in g])
  summary.append({'tie_seed':ts,'budget':b,'method':m,'panels':71,'seeds':args.acq_seeds,
       'expected_strict_actions':len(A)*np.mean(A)/args.acq_seeds,'expected_strict_models':len(M)*np.mean(M)/args.acq_seeds,
       'total_cost':sum(x['cost'] for x in g)/args.acq_seeds,
       'mean_stop_on_true_strict_action':np.mean([x['action_stop'] for x in g if x['true_action_winner']])})
 with (out/'R9_SUMMARY.csv').open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(summary[0]));wr.writeheader();wr.writerows(summary)
 audit={'status':'PASS_EXPLORATORY_RETROSPECTIVE','baseline_R8_source_git_blobs':receipt['inputs'],
        'panels':len(panels),'baits':len({p['bait'] for p in panels}),
        'zero_hc_panels':sum(sum(p['y'])==0 for p in panels),
        'ties':[int(k) for k in args.tie_seeds.split(',')],
        'acquisition_seeds':args.acq_seeds,'seed_start':args.seed_start,'tests':tests,
        'methods':METHODS,'same_informative_pool':True,'no_false_certificates':True,
        'outcome_blind_code_contract':'choose_next has no hidden outcome argument',
        'full_score_truth_is_retrospective':True,'no_prospective_wet_lab_or_historical_neural_tails':True,
        'elapsed_seconds':time.monotonic()-start,'result_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 (out/'R9_RECEIPT.json').write_text(json.dumps(audit,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n')
 print(json.dumps(audit,indent=2,default=str))
if __name__=='__main__':main()

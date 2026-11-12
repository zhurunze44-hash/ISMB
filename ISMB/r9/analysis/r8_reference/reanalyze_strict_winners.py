#!/usr/bin/env python3
"""Pinned public human Y2H audit; retrospective, not original neural tail recovery.

All 71 outcome-independent eligible panels are retained, including zero-HC panels.
The acquisition engine receives frozen nomination designs and disclosed labels only.
One query costs one distinct assay/bait/prey measurement, reused across all models.
Exact contrast intervals are shared by all policies; action classes are identical
Top-10 candidate sets, not model names. No method claims algorithmic novelty.
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,itertools,json,math,time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
MODELS=('AA','CN','RA','Jaccard','DegreeProduct')
PINS={'HuRI.csv':'46fec1d9554d07f165312313f1e5f9b6156e8aa3',
 'PPI_prediction_validation_result_20210624.xls':'7fb2a36b96b87e47cf8178544286d9db3c0e7e3e'}
METHODS=('disagreement','dopt','fair_contrast','coverage','random_informative')
BUDGETS=(0,3,5,8,10,15,20,30)
PAIRS=list(itertools.combinations(range(5),2))

def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def fnv(s):
 h=2166136261
 for c in s:h=((h^ord(c))*16777619)&0xffffffff
 return h
def read_native():
 receipts={}
 for name,pin in PINS.items():
  p=ROOT/'input'/name;b=p.read_bytes();assert gitblob(b)==pin,(name,gitblob(b))
  receipts[name]={'git_blob_sha1':pin,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 G=collections.defaultdict(set);edges=set()
 with (ROOT/'input'/'HuRI.csv').open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f):
   a,b=r['source'],r['target'];key=tuple(sorted((a,b)));assert key not in edges;edges.add(key)
   G[a];G[b]
   if a!=b:G[a].add(b);G[b].add(a)
 assert len(edges)==52548 and len(G)==8272
 grouped=collections.defaultdict(list);seen=set();meta=collections.Counter()
 with (ROOT/'input'/'PPI_prediction_validation_result_20210624.xls').open(newline='',encoding='utf-8-sig') as f:
  for r in csv.DictReader(f,delimiter='\t'):
   meta['raw_candidate_rows']+=1;a,b=r['source'],r['target'];key=tuple(sorted((a,b)))
   assert key not in seen;seen.add(key)
   if a==b:meta['self']+=1;continue
   if key in edges:meta['known_source_edge']+=1;continue
   if a not in G or b not in G:meta['outside_graph']+=1;continue
   vals=[r[f'score_assay{i}'] for i in (1,2,3)]
   labels=[1 if v=='Positive' else 0 if v=='Negative' else None for v in vals]
   if all(x is not None for x in labels):meta['all_three_measured']+=1
   if labels[0] is None:meta['v1_unmeasured']+=1;continue
   meta['qualified_v1_candidates']+=1
   C=sorted(G[a]&G[b]);cn=len(C)
   sc=(math.fsum(1/math.log(len(G[z])) for z in C if len(G[z])>1),float(cn),
       math.fsum(1/len(G[z]) for z in C),cn/len(G[a]|G[b]) if G[a] or G[b] else 0.,float(len(G[a])*len(G[b])))
   grouped[a].append({'prey':b,'labels':labels,'scores':sc})
 assert meta['raw_candidate_rows']==3276 and meta['qualified_v1_candidates']==2355 and meta['all_three_measured']==1751
 panels=[]
 for bait,rows in sorted(grouped.items()):
  if len(rows)<11:continue
  for t in (1,2):
   rr=sorted((r for r in rows if r['labels'][t] is not None),key=lambda r:r['prey'])
   if len(rr)<11:continue
   panels.append({'id':f'{bait}_v{t+1}','bait':bait,'assay':f'v{t+1}','prey':[r['prey'] for r in rr],
                  'scores':np.array([r['scores'] for r in rr]),'y':np.array([r['labels'][t] for r in rr],dtype=np.int16)})
 assert len(panels)==71 and len({p['bait'] for p in panels})==39 and sum(sum(p['y'])==0 for p in panels)==30
 keys=[(p['assay'],p['bait'],v) for p in panels for v in p['prey']]
 assert len(keys)==len(set(keys))
 return panels,{'inputs':receipts,'eligibility':dict(meta),'panels':71,'baits':39,'zero_hc_panels':30,
                'measured_candidate_keys':len(keys),'unique_measurement_keys':len(set(keys)),
                'score_accumulation':'sorted common neighbors, math.fsum, binary64',
                'source_commit':'5e2f7beb596987de7b97a0cf48900915a64aad99'}

def design(panel,tie_seed):
 n=len(panel['y']);X=np.zeros((n,5),dtype=np.int16)
 for j in range(5):
  order=sorted(range(n),key=lambda i:(-panel['scores'][i,j],fnv(f'{tie_seed}|{panel["bait"]}|{panel["prey"][i]}'),panel['prey'][i]))
  X[order[:10],j]=1
 assert np.all(X.sum(axis=0)==10)
 return X

def action_groups(X):
 groups=[];where={}
 for j in range(X.shape[1]):
  k=tuple(X[:,j]);
  if k not in where:where[k]=len(groups);groups.append([])
  groups[where[k]].append(j)
 return groups

def certify(X,observed):
 """Exact independent binary unknown-label bounds, using shared differences."""
 n,m=X.shape;known=np.zeros(n,bool);z=np.zeros(n,dtype=np.int16)
 for i,v in observed.items():known[i]=True;z[i]=v
 fixed=X[known].T@z[known]
 D=X[~known,:,None]-X[~known,None,:]
 low=fixed[:,None]-fixed[None,:]+np.minimum(D,0).sum(axis=0)
 up=fixed[:,None]-fixed[None,:]+np.maximum(D,0).sum(axis=0)
 off=~np.eye(m,dtype=bool)
 weak=np.all((low>=0)|~off,axis=1)
 strict=np.all((low>0)|~off,axis=1)
 groups=action_groups(X);reps=[g[0] for g in groups];l=low[np.ix_(reps,reps)]
 class_strict=[]
 if len(groups)>=2:
  class_strict=[j for j in range(len(groups)) if np.all(np.delete(l[j],j)>0)]
 # Exact top-set certification requires one guaranteed weak maximizer, with every
 # other model either forced equal or forced below it; {0,+} is insufficient.
 exact_best=None
 for j in np.flatnonzero(weak):
  equal=(low[j]==0)&(up[j]==0)
  if np.all(equal|(low[j]>0)):
   exact_best=tuple(np.flatnonzero(equal));break
 pair_low=np.array([low[i,j] for i,j in PAIRS]);pair_up=np.array([up[i,j] for i,j in PAIRS])
 return {'strict_model':tuple(np.flatnonzero(strict)),'strict_action':tuple(class_strict),
         'weak_models':tuple(np.flatnonzero(weak)),'exact_best':exact_best,
         'strict_pairs':int(np.sum((pair_low>0)|(pair_up<0))),
         'fixed_pair_ties':int(np.sum((pair_low==0)&(pair_up==0))),
         'low':low,'up':up,'groups':groups}

def truth_metrics(X,y):
 yy=X.T@y;best=tuple(np.flatnonzero(yy==max(yy)));gg=action_groups(X)
 cy=np.array([yy[g[0]] for g in gg]);abest=tuple(np.flatnonzero(cy==max(cy)))
 return {'values':yy,'best_models':best,'best_actions':abest,'groups':gg}

def metric(X,y,observed):
 c=certify(X,observed);t=truth_metrics(X,y)
 assert not c['strict_model'] or (len(c['strict_model'])==1 and c['strict_model']==t['best_models'])
 assert not c['strict_action'] or (len(c['strict_action'])==1 and c['strict_action']==t['best_actions'])
 assert set(c['weak_models']).issubset(t['best_models'])
 assert c['exact_best'] is None or c['exact_best']==t['best_models']
 nclass=len(t['groups']);exact=c['exact_best']
 return {'strict_model':int(bool(c['strict_model'])),'strict_action':int(bool(c['strict_action'])),
         'weak_model':int(bool(c['weak_models'])),'exact_best_set':int(exact is not None),
         'exact_best_tie_models':int(exact is not None and len(exact)>1),
         'exact_best_tie_actions':int(exact is not None and len(t['best_actions'])>1),
         'unresolved_best_set':int(exact is None),'strict_pairs':c['strict_pairs'],'fixed_pair_ties':c['fixed_pair_ties'],
         'trivial_one_action':int(nclass==1),'error_certificates':0,'cost':len(observed)}

def order_static(X,method,seed,panel_id,maxB):
 """No label or total H argument. Tie priorities independent of model names."""
 n,m=X.shape;rng=np.random.default_rng(seed+fnv(panel_id));perm=rng.permutation(n);tie=np.empty(n,int);tie[perm]=np.arange(n)
 degree=X.sum(axis=1);useful=[i for i in range(n) if 0<degree[i]<m]
 if method=='random_informative':return [int(i) for i in perm if i in useful][:maxB]
 D=np.column_stack([X[:,i]-X[:,j] for i,j in PAIRS]).astype(float)
 d=X.sum(axis=1);w=d*(m-d)
 if method=='disagreement':return sorted(useful,key=lambda i:(-w[i],tie[i]))[:maxB]
 if method=='coverage':return sorted(useful,key=lambda i:(-d[i],tie[i]))[:maxB]
 selected=[];remaining=useful.copy();inv=np.eye(len(PAIRS));counts=np.zeros(len(PAIRS))
 for _ in range(min(len(useful),maxB)):
  A=D[remaining]
  if method=='dopt':gain=np.einsum('ij,ij->i',A@inv,A)
  elif method=='fair_contrast':gain=np.sum(np.sqrt(counts[None,:]+(A!=0))-np.sqrt(counts)[None,:],axis=1)
  else:raise ValueError(method)
  mx=float(np.max(gain));best=min((remaining[i] for i,v in enumerate(gain) if v>=mx-1e-9),key=lambda i:tie[i])
  selected.append(best);remaining.remove(best)
  if method=='dopt':
   v=inv@D[best];inv-=np.outer(v,v)/(1+D[best]@v);inv=(inv+inv.T)/2
  else:counts+=D[best]!=0
 return selected

def strict_stopping_costs(X,y,order):
 D=X[:,:,None]-X[:,None,:]
 low0=np.minimum(D,0).sum(axis=0)
 gains=D[np.array(order,dtype=int)]*y[np.array(order,dtype=int),None,None]-np.minimum(D[np.array(order,dtype=int)],0)
 trajectory=np.concatenate((low0[None,:,:],low0[None,:,:]+np.cumsum(gains,axis=0)))
 off=~np.eye(5,dtype=bool)
 strict=np.all((trajectory>0)|~off,axis=2).any(axis=1)
 idx=np.flatnonzero(strict);model_stop=int(idx[0]) if len(idx) else -1
 reps=[g[0] for g in action_groups(X)];action_stop=-1
 if len(reps)>=2:
  a=trajectory[:,reps][:,:,reps];offa=~np.eye(len(reps),dtype=bool)
  idx=np.flatnonzero(np.all((a>0)|~offa,axis=2).any(axis=1));action_stop=int(idx[0]) if len(idx) else -1
 return model_stop,action_stop

def offline_cover_oracle(X,y):
 """Exact post-outcome certificate size, never supplied to an acquisition policy."""
 from scipy.optimize import milp,Bounds,LinearConstraint
 t=truth_metrics(X,y);groups=t['groups'];reps=[g[0] for g in groups]
 if len(reps)<2 or len(t['best_actions'])!=1:return -1,[]
 win=reps[t['best_actions'][0]];others=[j for j in reps if j!=win]
 D=X[:,win,None]-X[:,others];q=np.sum(D==-1,axis=0)
 cover=(D*y[:,None]-np.minimum(D,0)).T.astype(float)
 useful=np.flatnonzero(np.any(cover,axis=0));A=cover[:,useful]
 sol=milp(c=np.ones(len(useful)),integrality=np.ones(len(useful)),bounds=Bounds(0,1),
          constraints=LinearConstraint(A,q+1,np.full(len(q),np.inf)),options={'time_limit':30.0,'mip_rel_gap':0.0})
 assert sol.success and sol.status==0 and abs(sol.mip_gap)<1e-8,(sol.message,sol)
 selected=[int(useful[i]) for i,v in enumerate(sol.x) if v>0.5];value=int(round(sol.fun));assert len(selected)==value
 c=certify(X,{i:int(y[i]) for i in selected});assert c['strict_action']==t['best_actions']
 if len(t['best_models'])==1:assert c['strict_model']==t['best_models']
 return value,selected

def complete_tie_bounds(panel):
 lows=[];ups=[]
 for j in range(5):
  s=panel['scores'][:,j];cut=np.sort(s)[-10];fixed=s>cut;ties=s==cut;r=10-int(sum(fixed));h=int(sum(panel['y'][ties]));n=int(sum(ties));base=int(sum(panel['y'][fixed]));
  lows.append(base+max(0,r-(n-h)));ups.append(base+min(r,h))
 robust=[j for j in range(5) if all(lows[j]>ups[k] for k in range(5) if k!=j)]
 return lows,ups,robust

def write_csv(path,rows):
 if not rows:return
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def independent_checks():
 # Enumerate every completion on small, nontrivial designs, checking endpoints,
 # strict identities, model-permutation equivariance and exact best-set certificates.
 rng=np.random.default_rng(417);checks=0
 for n in range(1,8):
  for repeat in range(12):
   X=rng.integers(0,2,size=(n,5),dtype=np.int16);y=rng.integers(0,2,size=n,dtype=np.int16)
   k=repeat%(n+1);obs={i:int(y[i]) for i in range(k)};c=certify(X,obs)
   vals=[]
   for tail in itertools.product((0,1),repeat=n-k):
    yy=np.r_[y[:k],tail];v=X.T@yy;vals.append(v[:,None]-v[None,:])
   arr=np.stack(vals);assert np.array_equal(arr.min(axis=0),c['low']);assert np.array_equal(arr.max(axis=0),c['up'])
   for yy in itertools.product((0,1),repeat=n-k):metric(X,np.r_[y[:k],yy],obs)
   perm=np.array([3,0,4,2,1]);cc=certify(X[:,perm],obs)
   assert np.array_equal(c['low'][np.ix_(perm,perm)],cc['low'])
   checks+=1
 return {'independent_completion_cases':checks,'false_certificate_failures':0,'model_permutation_equivariance':'PASS'}

def run(tie_seeds,acq_seeds):
 out=ROOT/'results';out.mkdir(exist_ok=True)
 panels,receipt=read_native();checks=independent_checks();summaries=[];panelmeans=[];truthrows=[];aggstore={};stoppingrows=[]
 panel_cache=[];started=time.monotonic()
 for ts in tie_seeds:
  for p in panels:
   X=design(p,ts);y=p['y'];n=len(y);tr=truth_metrics(X,y);gg=tr['groups'];lo,hi,robust=complete_tie_bounds(p)
   oracle,oracle_keys=offline_cover_oracle(X,y)
   informative=int(np.sum((X.sum(axis=1)>0)&(X.sum(axis=1)<5)))
   assert metric(X,y,{i:int(v) for i,v in enumerate(y)})['exact_best_set']==1
   truthrows.append({'tie_seed':ts,'panel':p['id'],'bait':p['bait'],'assay':p['assay'],'n':n,'HC':int(sum(y)),
    'distinct_actions':len(gg),'informative_candidates':informative,'oracle_minimal_strict_certificate':oracle,'oracle_candidate_indices':'|'.join(map(str,oracle_keys)),
    'true_unique_model':int(len(tr['best_models'])==1),
    'true_unique_action_nontrivial':int(len(gg)>=2 and len(tr['best_actions'])==1),
    'true_top_model_count':len(tr['best_models']),'true_top_action_count':len(tr['best_actions']),
    'robust_strict_model_all_independent_ties':len(robust),'best_models':'|'.join(MODELS[j] for j in tr['best_models']),
    'full_utilities':'|'.join(map(str,tr['values'])),'action_partition':'/'.join(','.join(MODELS[j] for j in g) for g in gg),
    'tie_utility_lower':'|'.join(map(str,lo)),'tie_utility_upper':'|'.join(map(str,hi))})
   if ts==tie_seeds[0]:
    panel_cache.append({'panel':p['id'],'bait':p['bait'],'assay':p['assay'],'prey':p['prey'],'scores':p['scores'].tolist(),'labels':y.tolist(),'top10_design':X.tolist()})
   for method in METHODS:
    metrics={b:[] for b in BUDGETS}
    stopcosts=[]
    for seed in range(acq_seeds):
     order=order_static(X,method,seed,p['id'],n);assert len(order)==len(set(order))==informative
     ms,acs=strict_stopping_costs(X,y,order)
     assert (ms>=0)==(len(tr['best_models'])==1)
     assert (acs>=0)==(len(gg)>=2 and len(tr['best_actions'])==1)
     if acs>=0:assert acs>=oracle
     assert metric(X,y,{i:int(y[i]) for i in order})['exact_best_set']==1
     stopcosts.append((ms,acs))
     for b in BUDGETS:
      seen=order[:min(b,n)];obs={i:int(y[i]) for i in seen};mm=metric(X,y,obs);metrics[b].append(mm)
      key=(ts,b,method,seed)
      if key not in aggstore:aggstore[key]={k:0 for k in mm}
      for k,v in mm.items():aggstore[key][k]+=v
    stoppingrows.append({'tie_seed':ts,'method':method,'panel':p['id'],'bait':p['bait'],'informative_candidates':informative,
      'oracle_cost':oracle,'strict_model_stop_mean':float(np.mean([s[0] for s in stopcosts])),
      'strict_action_stop_mean':float(np.mean([s[1] for s in stopcosts])),
      'strict_action_stop_min':min(s[1] for s in stopcosts),'strict_action_stop_max':max(s[1] for s in stopcosts)})
    for b,records in metrics.items():
     row={'tie_seed':ts,'budget':b,'method':method,'panel':p['id'],'bait':p['bait'],'assay':p['assay'],'n':n,'HC':int(sum(y))}
     row.update({k:float(np.mean([r[k] for r in records])) for k in records[0]});panelmeans.append(row)
  print(json.dumps({'tie_seed_complete':ts,'elapsed_seconds':round(time.monotonic()-started,1)}),flush=True)
 # Aggregate with seeds kept separate; means are computational repetitions only.
 keys=list(metrics[0][0])
 agg=[]
 for key,values in sorted(aggstore.items()):
  ts,b,method,seed=key
  agg.append({'tie_seed':ts,'budget':b,'method':method,'acq_seed':seed,**values})
 gg=collections.defaultdict(list)
 for r in agg:gg[(r['tie_seed'],r['budget'],r['method'])].append(r)
 for key,rr in sorted(gg.items()):
  ts,b,method=key;row={'tie_seed':ts,'budget':b,'method':method,'seeds':len(rr),'panels':len(panels)}
  for k in keys:row[k+'_mean']=float(np.mean([r[k] for r in rr]));row[k+'_min']=min(r[k] for r in rr);row[k+'_max']=max(r[k] for r in rr)
  summaries.append(row)
 write_csv(out/'SUMMARY.csv',summaries);write_csv(out/'PANEL_MEANS.csv',panelmeans);write_csv(out/'COMPLETE_TRUTH.csv',truthrows);write_csv(out/'SEED_TOTALS.csv',agg);write_csv(out/'STOPPING_COSTS.csv',stoppingrows)
 (out/'NATIVE_COMPLETE_SCORE_PANELS.json').write_text(json.dumps(panel_cache,separators=(',',':'))+'\n')
 receipt.update({'tie_seeds':tie_seeds,'acquisition_seeds':acq_seeds,'methods':METHODS,'budgets_per_panel':BUDGETS,'validation':checks,
                 'all_complete_budget_best_sets_exact':True,'all_observed_false_certificates':0,
                 'acquisition_domain':'All structurally informative rows only (0 < model nomination count < 5), shared by every strategy; uninformed random is not used as the sole baseline.',
                 'budget_cost':'Unique assay/bait/prey label, shared across models; per-panel budget cap, no duplication across selected panels.',
                 'oracle_scope':'Post-outcome exact minimum certificate via covering MILP, not a policy and never used by policies.',
                 'science_scope':'Retrospective real public human structural scores, fixed candidate qualification. No historical neural scores; no new wet experiment; no prospective claim.',
                 'runtime_seconds':time.monotonic()-started})
 (out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--tie-seeds',default='0,1,2,3,4,5');ap.add_argument('--acquisition-seeds',type=int,default=100);a=ap.parse_args()
 run([int(s) for s in a.tie_seeds.split(',')],a.acquisition_seeds)

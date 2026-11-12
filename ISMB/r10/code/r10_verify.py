#!/usr/bin/env python3
"""Independent R10 endpoint/seed/policy-prefix QC against frozen R8/R9."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import r10_transfer as r10
ROOT=Path(__file__).resolve().parents[1]
R=r10.r8;P=r10.r9
out={'status':'START','exact_certificate_checks':0,'frozen_r9_policy_prefix_checks':0,
     'model_permutation_checks':0,'issues':[]}
for source,boards in [('yeast',r10.load_yeast()),('human',r10.load_human_v1())]:
  sample=boards[:5]+boards[-5:]
  for b in sample:
    X=b['X'];y=b['y'];n=len(y)
    for seed in (0,17,93):
      for meth in r10.METHODS:
        order=r10.get_order(b,meth,seed)
        r,_,_,truth_model,truth_action=r10.score_order_prefix(X,y,order)
        for budget in r10.BUDGETS:
          seen=order[:min(len(order),budget)]
          c=R.certify(X,{int(i):int(y[i]) for i in seen})
          assert int(bool(c['strict_model']))==r[budget][0]
          assert int(bool(c['strict_action']))==r[budget][1]
          assert int(bool(c['strict_model']))<=truth_model and int(bool(c['strict_action']))<=truth_action
          out['exact_certificate_checks']+=1
        if meth in ('adaptive_empirical','adaptive_sparse','adaptive_half'):
          # R10 asks for a prefix ONLY; test byte-for-byte identical choices.
          full=P.compute_order(X,y,meth,seed,b['panel'])
          assert order==full[:len(order)]
          out['frozen_r9_policy_prefix_checks']+=1
  # No outcome has been used for candidate qualification beyond measured vs unmeasured.
  gold=pd.read_csv(ROOT/'results'/f'{source}_complete_truth.csv')
  assert gold.panel.nunique()==len(boards)
  assert (gold.true_action_winner<=1).all() and (gold.true_model_winner<=1).all()
  z=pd.read_csv(ROOT/'results'/f'{source}_all100_summary.csv')
  assert (z.groupby('budget').mean_panel_membership_cost.nunique()==1).all()
  out[source]={'panels':len(boards),'zero_hc':int((gold.h==0).sum()),
      'certified_truth_actions':int(gold.true_action_winner.sum()),'raw_gzip_sha256':r10.sha(ROOT/'results'/f'{source}_all_seed_panel_budget.csv.gz')}
# Explicit real-input permutation checks with controlled priority across names, not seed RNG labels.
for b in r10.load_yeast()[:5]+r10.load_human_v1()[:5]:
  X=b['X'];y=b['y'];prior=P.seed_permutation(len(y),4,b['panel']);known=[];vals=[]
  for _ in range(min(8,len(prior))):
    for meth in ('adaptive_empirical','adaptive_half','adaptive_sparse'):
      choice=P.choose_next(X,known,vals,prior,meth)
      pi=[2,4,0,1,3]
      assert choice==P.choose_next(X[:,pi],known,vals,prior,meth)
      out['model_permutation_checks']+=1
    i=P.choose_next(X,known,vals,prior,'adaptive_empirical')
    if i is None:break
    known.append(i);vals.append(int(y[i]))
out['status']='PASS_EXACT_CERTIFICATES__FROZEN_R9_PREFIX_EQUIVALENT'
(ROOT/'checks'/'R10_VERIFY.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(out,indent=2,ensure_ascii=False))

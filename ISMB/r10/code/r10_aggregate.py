#!/usr/bin/env python3
"""Recombine disjoint seed chunks from R10. Validate all 100 exact seeds per board and budget."""
from __future__ import annotations
from pathlib import Path
import sys, gzip, json, hashlib
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import r10_transfer as study
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
BUDGETS=(5,8,10,15,20)

def sha(x):return hashlib.sha256(Path(x).read_bytes()).hexdigest()
report={}
for kind,expect_panels in [('yeast',74),('human',44)]:
    paths=[OUT/'chunks'/f'{kind}_{start:03d}_{start+20:03d}'/f'{kind}_budget_subset.csv' for start in range(0,100,20)]
    for path in paths: assert path.exists(),path
    parts=[pd.read_csv(p) for p in paths]
    df=pd.concat(parts,ignore_index=True)
    expect=len(study.METHODS)*100*expect_panels*len(BUDGETS)
    assert len(df)==expect,(len(df),expect)
    assert sorted(df.seed.unique().tolist())==list(range(100))
    assert df.panel.nunique()==expect_panels
    assert not df.duplicated(['panel','seed','budget','method']).any()
    assert not ((df.certified_action>df.true_action_winner)|(df.certified_model>df.true_model_winner)).any()
    assert (df.groupby(['budget','method'])['cost'].sum().unstack().nunique(axis=1)==1).all()
    # Exact paired seed design across methods; all panels have same seed sets.
    assert (df.groupby(['panel','budget','method'])['seed'].nunique()==100).all()
    raw=OUT/f'{kind}_all_seed_panel_budget.csv.gz'
    with gzip.open(raw,'wt',newline='') as f:df.to_csv(f,index=False)
    s=df.groupby(['budget','method'],as_index=False).agg(
         mean_certified_action=('certified_action','mean'),mean_certified_model=('certified_model','mean'),
         cost_per_panel=('cost','mean'))
    s['expected_certified_actions']=s['mean_certified_action']*expect_panels
    s['expected_certified_models']=s['mean_certified_model']*expect_panels
    s['mean_panel_membership_cost']=s['cost_per_panel']*expect_panels
    s['n_panels']=expect_panels;s['seeds']=100
    s.to_csv(OUT/f'{kind}_all100_summary.csv',index=False)
    per,pv,contra=study.analyze_primary(df,kind,10,boots=5000)
    per.to_csv(OUT/f'{kind}_all100_per_panel.csv',index=False)
    pv.to_csv(OUT/f'{kind}_all100_paired_pivot.csv',index=False)
    contra.to_csv(OUT/f'{kind}_all100_cluster_bootstrap.csv',index=False)
    assay=df[df.budget==10].groupby(['assay','method'],as_index=False).agg(
        certified_actions=('certified_action','sum'), certified_models=('certified_model','sum'),
        panel_cost=('cost','sum'),n_rows=('panel','size'))
    assay['mean_certified_actions']=assay['certified_actions']/100
    assay['mean_certified_models']=assay['certified_models']/100
    assay['mean_panel_cost']=assay['panel_cost']/100
    assay['n_panels']=assay['n_rows']/100
    assay.to_csv(OUT/f'{kind}_assay_stratified.csv',index=False)
    gold=df[['panel','anchor','assay','h','n','true_model_winner','true_action_winner','informative']].drop_duplicates().sort_values('panel')
    gold.to_csv(OUT/f'{kind}_complete_truth.csv',index=False)
    true_action=int(gold.true_action_winner.sum());true_model=int(gold.true_model_winner.sum());zero_hc=int((gold.h==0).sum())
    assert (df[df.budget==30].groupby(['method','panel'])['certified_action'].mean()<=df[['panel','true_action_winner']].drop_duplicates().set_index('panel').loc[df[df.budget==30].groupby(['method','panel'])['certified_action'].mean().index.get_level_values('panel'),'true_action_winner'].values).all()
    report[kind]={'rows':len(df),'seeds':100,'panels':expect_panels,'baits':gold.anchor.nunique(),'zero_hc':zero_hc,
        'true_unique_actions':true_action,'true_unique_model_ids':true_model,
        'subset_cost_is_not_global_deduplicated':kind=='yeast',
        'all_seed_csv_sha256':sha(raw),
        'primary_cap10':s[s.budget==10][['method','expected_certified_actions','expected_certified_models','mean_panel_membership_cost']].to_dict('records'),
        'primary_pairs':contra.to_dict('records'),
        'by_assay_cap10':assay.to_dict('records')}
    print('\n',kind,'full truth: strict action',true_action,'strict model',true_model,'zero HC',zero_hc)
    print(s[s.budget==10][['method','expected_certified_actions','expected_certified_models','mean_panel_membership_cost']].to_string(index=False))
    print(contra[['b','mean_difference_panel_count','cluster_bootstrap_95_low','cluster_bootstrap_95_high','n_pos_diff_panels','n_neg_diff_panels']].to_string(index=False))
(OUT/'R10_FINAL_RESULTS.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('AGGREGATE_100_SEEDS_PASS',json.dumps({k:{'rows':v['rows'],'actions':v['true_unique_actions'],'sha256':v['all_seed_csv_sha256']} for k,v in report.items()},indent=2))

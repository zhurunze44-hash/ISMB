#!/usr/bin/env python3
"""Recompute frozen public structural results on CPU; smoke not a full R11 neural replay."""
from pathlib import Path
import subprocess,sys,csv,gzip,json,hashlib
R=Path(__file__).resolve().parents[1]
LOG=R/'smoke_logs';LOG.mkdir(exist_ok=True)

def run(args,cwd,label):
 p=subprocess.run([sys.executable,*args],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (LOG/f'{label}.log').write_text(p.stdout)
 if p.returncode:raise RuntimeError(f'{label} FAILED: '+p.stdout[-1500:])
 print(label,'EXECUTED_PASS')

def csvrows(path):
 f=gzip.open(path,'rt') if path.suffix=='.gz' else path.open('r')
 with f:return list(csv.DictReader(f))

def check(name,a,b):
 x=csvrows(a);y=csvrows(b)
 if x!=y:
  from itertools import zip_longest
  bad=[(i,q,z) for i,(q,z) in enumerate(zip_longest(x,y)) if q!=z]
  raise RuntimeError(f'{name} row differences: '+str(bad[:2]))
 print(name,'ROW_PARITY_PASS',len(x));return len(x)

def main():
 r8=R/'r8/analysis/strict_winner_experiment'
 r9=R/'r9'
 r10=R/'r10'
 for d in [r8/'input',r9/'analysis/r8_reference/input',r10/'analysis/r8_reference/input']:
  if not all((d/f).exists() for f in ('HuRI.csv','PPI_prediction_validation_result_20210624.xls')):
   raise RuntimeError('MISSING_PUBLIC_INPUT: run tools/prepare_inputs.py --download or --from-dir first')
 run(['reanalyze_strict_winners.py','--tie-seeds','0','--acquisition-seeds','2'],r8,'r8')
 run(['analysis/source/r9_adaptive_pilot.py','--tie-seeds','0','--acq-seeds','1','--seed-start','0','--output',str(r9/'smoke')],r9,'r9')
 run(['code/r10_transfer.py','--only','both','--seeds','1','--seed-start','0'],r10,'r10')
 counts={}
 counts['r8_aggregation']=check('R8_SEEDS',r8/'results/SEED_TOTALS.csv',R/'expected/r8_tie0_seeds01.csv')
 counts['r8_truth']=check('R8_TRUTH',r8/'results/COMPLETE_TRUTH.csv',R/'expected/r8_truth_tie0.csv')
 counts['r9_one_seed']=check('R9_ONE_SEED',r9/'smoke/R9_SEED_PANEL_RESULTS.csv',R/'expected/r9_tie0_seed0.csv.gz')
 for k in ('yeast','human'):
  counts['r10_'+k+'_one_seed']=check('R10_'+k.upper(),r10/'results/chunks/both_000_001'/f'{k}_per_seed.csv.gz',R/f'expected/r10_{k}_seed0.csv.gz')
 res={'status':'PASS_CLEANROOM_DERIVED_SMOKE_ONLY','counts':counts,'scope':'R8 2 seeds; R9/R10 1 seed. Does not certify raw-to-yeast masks, historical neural score producer or pretarget experiment.'}
 (LOG/'SMOKE_RECEIPT.json').write_text(json.dumps(res,indent=2)+'\n')
 print(json.dumps(res,indent=2))
if __name__=='__main__':main()

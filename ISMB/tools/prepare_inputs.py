#!/usr/bin/env python3
"""Get and verify only upstream public human inputs. No private Paper3 assets."""
from pathlib import Path
import argparse,hashlib,urllib.request,urllib.parse,shutil,json,sys
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'provenance/public_input_manifest.json').read_text())
TARGETS=[ROOT/'r8/analysis/strict_winner_experiment/input',ROOT/'r9/analysis/r8_reference/input',ROOT/'r10/analysis/r8_reference/input',ROOT/'r10/input']

def gitblob(data):
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def check(name,data):
 exp=P['original_files'][name]
 a=hashlib.sha256(data).hexdigest()
 b=gitblob(data)
 if a!=exp['sha256'] or b!=exp['git_blob_sha1']:
  raise RuntimeError(f'WRONG_INPUT {name}: sha256={a}, blob={b}, expected={exp}')

def main():
 parser=argparse.ArgumentParser(); g=parser.add_mutually_exclusive_group(required=True)
 g.add_argument('--from-dir',type=Path,help='Offline directory with the two exact upstream files')
 g.add_argument('--download',action='store_true',help='Download pinned public GitHub files; internet access required')
 args=parser.parse_args()
 for name,meta in P['original_files'].items():
  if args.from_dir:
   data=(args.from_dir/name).read_bytes()
  else:
   u='https://raw.githubusercontent.com/'+P['human_git_repo']+'/'+P['human_commit']+'/'+urllib.parse.quote(meta['github_path'])
   with urllib.request.urlopen(u,timeout=45) as r: data=r.read()
  check(name,data)
  for target in TARGETS[:3]:
   target.mkdir(parents=True,exist_ok=True)
   (target/name).write_bytes(data)
  print('PINNED_SOURCE_PASS',name,len(data),meta['git_blob_sha1'])
 print('YEAST_SCOPE: candidate-only derived 74 masks included; upstream raw-table-to-mask lineage is NOT established.')
if __name__=='__main__':main()

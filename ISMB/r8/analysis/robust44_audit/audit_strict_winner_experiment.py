#!/usr/bin/env python3
"""Independent input/truth reconstruction and targeted checks of new experiment.

Reconstruct native graph, labels, structural scores and tie actions without using
the experiment's read_native/design/truth functions. Call the implementation under
test only for certification, permutation invariance and static acquisition checks.
"""
import csv
import hashlib
import importlib.util
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1] / 'strict_winner_experiment'
OUT = Path(__file__).resolve().parent


def independent_hash(s):
    value = 0x811c9dc5
    for byte in s.encode('ascii'):
        value = ((value ^ byte) * 0x01000193) % (2**32)
    return value


def independent_reconstruct(reverse=False):
    with (ROOT/'input/HuRI.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    if reverse:
        rows.reverse()
    graph = defaultdict(set)
    for row in rows:
        a, b = row['source'], row['target']
        graph[a]; graph[b]
        if a != b:
            graph[a].add(b); graph[b].add(a)
    with (ROOT/'input/PPI_prediction_validation_result_20210624.xls').open(newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    if reverse:
        rows.reverse()
    bybait = defaultdict(list)
    for row in rows:
        a, b = row['source'], row['target']
        if a == b or a not in graph or b not in graph or b in graph[a]:
            continue
        if row['score_assay1'] not in ['Positive', 'Negative']:
            continue
        bybait[a].append(row)
    panels = {}
    for bait, source in bybait.items():
        if len(source) < 11:
            continue
        for assay in [2, 3]:
            retained = sorted((r for r in source if r[f'score_assay{assay}'] in ['Positive', 'Negative']),
                              key=lambda r: r['target'])
            if len(retained) < 11:
                continue
            candidates, y, scores = [], [], []
            for row in retained:
                prey = row['target']
                common = sorted(graph[bait].intersection(graph[prey]))
                numerator = len(common)
                denom = len(graph[bait]) + len(graph[prey]) - numerator
                # Independently assembled score vector, with graph degree identities.
                aa = math.fsum(math.log(len(graph[c]))**(-1) for c in common if len(graph[c]) > 1)
                ra = math.fsum(len(graph[c])**(-1) for c in common)
                scores.append([aa, numerator, ra, numerator/denom if denom else 0,
                               len(graph[bait])*len(graph[prey])])
                candidates.append(prey)
                y.append(int(row[f'score_assay{assay}']=='Positive'))
            panels[f'{bait}_v{assay}'] = (bait, candidates, np.array(scores), np.array(y))
    return panels


def independent_action(panel):
    bait, candidates, scores, y = panel
    x = np.zeros((len(candidates), 5), dtype=int)
    for m in range(5):
        ordered = sorted(range(len(candidates)), key=lambda i: (
            -scores[i,m], independent_hash(f'0|{bait}|{candidates[i]}'), candidates[i]))
        x[ordered[:10], m] = 1
    return x


def main():
    spec = importlib.util.spec_from_file_location('experiment_under_test', ROOT/'reanalyze_strict_winners.py')
    code = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(code)
    native = independent_reconstruct()
    reversed_native = independent_reconstruct(reverse=True)
    assert set(native) == set(reversed_native)
    cache = json.loads((ROOT/'results/NATIVE_COMPLETE_SCORE_PANELS.json').read_text())
    assert len(cache) == 71 and len(native) == 71
    checks = defaultdict(int)
    truth_counts = defaultdict(int)
    score_discrepancies = []
    permutation = np.array([4, 2, 0, 3, 1])
    for record in cache:
        pid = record['panel']; panel = native[pid]
        bait, candidates, scores, y = panel
        assert candidates == record['prey']
        assert np.array_equal(y, record['labels'])
        # exponent(-1) vs division can differ by a last bit; inspect both exactness
        # and action equality rather than calling a tolerance score provenance.
        archived_scores = np.array(record['scores'])
        if not np.array_equal(scores, archived_scores):
            diffs = np.abs(scores-archived_scores)
            assert np.max(diffs) <= 1e-12
            score_discrepancies.append({'panel':pid, 'max_abs':float(np.max(diffs)),
                                        'nonidentical_cells':int(np.sum(diffs>0))})
        checks['native_candidate_labels_matched'] += len(y)
        checks['native_structural_score_cells_checked'] += scores.size
        x = independent_action(panel)
        assert np.array_equal(x, record['top10_design'])
        assert np.array_equal(x, independent_action(reversed_native[pid]))
        checks['native_shared_tie_actions_matched'] += 5
        checks['native_row_order_invariance_panels'] += 1
        values = x.T@y
        best = tuple(np.flatnonzero(values==values.max()))
        classes = list(dict.fromkeys(tuple(x[:,m]) for m in range(5)))
        class_values = [np.dot(cl,y) for cl in classes]
        class_best = [j for j, v in enumerate(class_values) if v==max(class_values)]
        truth_counts['strict_model'] += int(len(best)==1)
        truth_counts['strict_action_nontrivial'] += int(len(classes)>=2 and len(class_best)==1)
        truth_counts['trivial_one_action'] += int(len(classes)==1)
        truth_counts['zero_HC_panels'] += int(sum(y)==0)
        # All candidates except up to 6 informative candidates are observed.
        # Exhausting the remaining outcomes is an independent real-board test.
        informative = np.flatnonzero((x.sum(axis=1)>0)&(x.sum(axis=1)<5))
        hidden = informative[:6].tolist()
        obs = {i:int(y[i]) for i in range(len(y)) if i not in hidden}
        reported = code.certify(x,obs)
        full_differences=[]; best_sets=[]
        for bits in itertools.product([0,1], repeat=len(hidden)):
            possible=y.copy();possible[hidden]=bits
            v=x.T@possible
            full_differences.append(v[:,None]-v[None,:])
            best_sets.append(tuple(np.flatnonzero(v==v.max())))
            checks['real_board_completions_enumerated'] += 1
        differences=np.array(full_differences)
        assert np.array_equal(differences.min(axis=0),reported['low'])
        assert np.array_equal(differences.max(axis=0),reported['up'])
        if reported['strict_model']:
            assert all(s==reported['strict_model'] and len(s)==1 for s in best_sets)
        if reported['exact_best'] is not None:
            assert all(s==reported['exact_best'] for s in best_sets)
        if len(set(best_sets))==1:
            assert reported['exact_best']==best_sets[0]
        checks['real_panel_complete_identification_checks'] += 1
        # Model naming/permutation cannot change information choices.
        other=code.certify(x[:,permutation],obs)
        assert np.array_equal(reported['low'][np.ix_(permutation,permutation)],other['low'])
        for method in code.METHODS:
            first=code.order_static(x,method,17,pid,len(y))
            permuted=code.order_static(x[:,permutation],method,17,pid,len(y))
            assert first==permuted,(pid,method)
            checks['static_order_model_permutation_checks'] += 1
        # Row permutations preserve candidate identity ranking when tie state is
        # expressed through the true candidate key; the native producer sorts prey.
        assert np.array_equal(code.design({'y':1-y,'scores':archived_scores,'bait':bait,'prey':candidates},0),x)
        checks['target_label_complement_design_invariance_checks'] += 1
    receipt={
        'status':'PASS_TARGETED_INDEPENDENT_SCIENTIFIC_AUDIT',
        'experiment_script_sha256':hashlib.sha256((ROOT/'reanalyze_strict_winners.py').read_bytes()).hexdigest(),
        'native_cache_sha256':hashlib.sha256((ROOT/'results/NATIVE_COMPLETE_SCORE_PANELS.json').read_bytes()).hexdigest(),
        'checks':dict(checks),
        'complete_primary_tie_seed_0_truth':dict(truth_counts),
        'independent_arithmetic_score_roundoff':score_discrepancies,
        'acquisition_code_review':{
            'policy_function_arguments':'X, method, seed, panel_id, maxB; no labels or positive totals',
            'static_only':True,
            'offline_full_label_oracle_never_used_by_policies':True,
            'coverage_label':'Current coverage implementation is nomination-count priority, not submodular set coverage',
            'fair_contrast_label':'Concave pair-contrast coverage greedy (square-root objective)',
            'measured_pool_boundary':'Eligibility uses known measurement presence, not positive value; this is retrospective fixed-pool evaluation',
            'active_testing_or_model_selector_implemented':False},
        'independence_scope':'Independent native input reconstruction and truth/finite-completion arithmetic, plus target-policy code inspection; not a second wet experiment or historical neural producer replay.'}
    (OUT/'STRICT_WINNER_INDEPENDENT_AUDIT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()

"""Pure synthetic research, never a model-weight writer or engine qualifier.

Four slots reproduce the already-qualified source profile. Eight slots are a
SOURCE-DERIVED PREDICTION until actual pinned-engine GLTF readback is measured.
"""
import itertools
import json
import math
import random
import struct


def f32(v):
    return struct.unpack('<f', struct.pack('<f', v))[0]


def sequential_sum(row):
    result = 0.
    for value in row:
        result = f32(result + value)
    return result


def packed(value, total):
    normalized = f32(value / total) if total > 0. else value
    return int(max(0., min(65535., f32(normalized * 65535.))))


def profile(row):
    if len(row) not in (4, 8) or any(type(v) not in (int, float) or
            not math.isfinite(v) or not 0 <= v <= 1 or f32(v) != v for v in row):
        raise ValueError('finite_exact_f32_four_or_eight_required')
    total = sequential_sum(row)
    ints = [packed(v, total) for v in row]
    return dict(total=total, packed=ints,
                readback=[f32(v / 65535.) for v in ints])


def lattice(weight):
    bits = struct.unpack('<I', struct.pack('<f', weight))[0]
    exponent = (bits >> 23) & 255
    return ((bits & 0x7fffff) | (0x800000 if exponent else 0),
            exponent - 150 if exponent else -149)


def lower_bound(count, predicate):
    lo, hi = 0, count + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if predicate(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def candidates(weight, fraction, total, target):
    """Intersect two exact monotone UNORM bins on the source's f32 lattice.

    Search only five nearby packed allocations and bin edge/nearest points.
    Every returned pair sums EXACTLY to the original source float, has exact
    source-normalized aggregate uint16 target, and retains source slot order.
    """
    count, exponent = lattice(weight)
    desired = round(count * fraction)
    def raw(n):
        return math.ldexp(n, exponent)
    def interval(integer):
        lo = lower_bound(count, lambda n: packed(raw(n), total) >= integer)
        hi = lower_bound(count, lambda n: packed(raw(n), total) >= integer + 1) - 1
        return lo, hi
    result = set()
    center = round(target * fraction)
    for right in range(max(0, center - 2), min(target, center + 2) + 1):
        lb, ub = interval(right)
        la, ua = interval(target - right)
        lo, hi = max(lb, count - ua), min(ub, count - la)
        if lo > hi:
            continue
        closest = max(lo, min(hi, desired))
        for n in (lo, hi, closest, max(lo, closest - 1), min(hi, closest + 1)):
            a, b = raw(count - n), raw(n)
            if a + b != weight or f32(a) != a or f32(b) != b:
                raise AssertionError('partition_not_exact')
            if packed(a, total) + packed(b, total) != target:
                raise AssertionError('bin_intersection_not_exact')
            result.add((a, b))
    return sorted(result, key=lambda p: abs(p[1] - weight * fraction))


def solve(source, fraction, beam_limit=128, mass_deviation_limit=2 / 65535):
    """Bounded feasibility candidate; refusal is NOT a proof of impossibility."""
    original = profile(source)
    if len(source) != 4 or original['total'] <= 0 or type(fraction) not in (int, float) or not math.isfinite(fraction) or not 0 <= fraction <= 1:
        return dict(status='REFUSED', reason='positive_four_slot_and_fraction_profile_required')
    pools = [candidates(w, fraction, original['total'], q)
             for w, q in zip(source, original['packed'])]
    if any(not p for p in pools):
        return dict(status='REFUSED', reason='no_nearby_bin_partition')
    # Keep one best path per actual sequential f32 accumulator state. This
    # explicitly respects adjacent [old/left, guide/right] slot ordering.
    states = {0.: (0., [])}
    truncated = False
    for weight, pool in zip(source, pools):
        following = {}
        for total, (cost, row) in states.items():
            for a, b in pool:
                new_total = f32(f32(total + a) + b)
                new_cost = cost + abs(b - weight * fraction)
                if new_total not in following or new_cost < following[new_total][0]:
                    following[new_total] = (new_cost, row + [a, b])
        if len(following) > beam_limit:
            truncated = True
            following = dict(sorted(following.items(), key=lambda x: x[1][0])[:beam_limit])
        states = following
    solution = states.get(original['total'])
    if solution is None:
        return dict(status='REFUSED', reason='bounded_candidates_do_not_retain_original_f32_sum', beam_truncated=truncated)
    cost, row = solution
    if cost > mass_deviation_limit:
        return dict(status='REFUSED', reason='requested_transfer_deviation_budget', deviation=cost)
    prediction = profile(row)
    aggregate = [sum(prediction['packed'][2*i:2*i+2]) for i in range(4)]
    if aggregate != original['packed'] or prediction['total'] != original['total'] or any(row[2*i] + row[2*i+1] != source[i] for i in range(4)):
        raise AssertionError('independent_final_gate')
    return dict(status='PREDICTED_FEASIBLE', source=source, fraction=fraction,
                source_profile=original, candidate=row, predicted_profile=prediction,
                aggregate_packed=aggregate, transfer_mass_deviation=cost,
                readback_pair_sum_equal=[sum(prediction['readback'][2*i:2*i+2]) == original['readback'][i] for i in range(4)],
                beam_truncated=truncated, engine_eight_slot_readback_measured=False,
                shader_or_pixel_equivalence=False)


def ordinary_split(source, fraction):
    row = []
    for weight in source:
        count, exponent = lattice(weight)
        n = round(count * fraction)
        row.extend([math.ldexp(count - n, exponent), math.ldexp(n, exponent)])
    return row


def research():
    rows = [[1., 0., 0., 0.], [f32(.1), f32(.8), f32(.1), 0.],
            [f32(.2), f32(.3), f32(.4), f32(.1)],
            [f32(1/3)] * 3 + [0.], [f32(.99999), f32(.00001), 0., 0.]]
    rng = random.Random(20261121)
    for _ in range(100):
        values = [rng.random() for _ in range(4)]
        rows.append([f32(v / sum(values)) for v in values])
    cases = []; ordinary_loss = sum_drift = readback_sum_mismatch = 0
    for source, fraction in itertools.product(rows, (0., .13, .5, .87, 1.)):
        old = profile(source)
        naive = profile(ordinary_split(source, fraction))
        groups = [sum(naive['packed'][2*i:2*i+2]) for i in range(4)]
        ordinary_loss += groups != old['packed']
        sum_drift += naive['total'] != old['total']
        value = solve(source, fraction)
        if value['status'] == 'PREDICTED_FEASIBLE':
            readback_sum_mismatch += not all(value['readback_pair_sum_equal'])
        cases.append(value)
    first = profile([1., 0., 0., 0.]); half = profile([.5, .5, 0., 0., 0., 0., 0., 0.])
    assert first['packed'][0] == 65535 and sum(half['packed']) == 65534
    assert solve([1., 0., 0., 0.], .5)['status'] == 'PREDICTED_FEASIBLE'
    scalar = dict(cases=len(cases), predicted_feasible=sum(v['status']=='PREDICTED_FEASIBLE' for v in cases),
                  bounded_refusals=sum(v['status']=='REFUSED' for v in cases),
                  naive_aggregate_packed_mismatch_cases=ordinary_loss,
                  naive_sequential_f32_normalizer_drift_cases=sum_drift,
                  solved_exact_readback_pair_sum_mismatch_cases=readback_sum_mismatch,
                  actual_engine_eight_slot_measurements=0, private_assets_read=0,
                  model_weights_written=0, profile='source_derived_eight_not_runtime_qualified')
    return dict(scalars=scalar, counterexample_one_to_two_half=dict(original=first, split=half),
                solved_one_to_two_half=solve([1.,0.,0.,0.], .5),
                first_normalizer_drift=next((dict(source=s, fraction=f, original=profile(s), split=profile(ordinary_split(s,f))) for s,f in itertools.product(rows,(.13,.5,.87)) if profile(s)['total']!=profile(ordinary_split(s,f))['total']),None),
                refusal_reasons=sorted({v['reason'] for v in cases if v['status']=='REFUSED'}))


if __name__ == '__main__':
    print(json.dumps(research(), indent=2, allow_nan=False))

"""Volume-target packing with an explicit per-pallet stopping rule.

Reuse the existing beam search and all PalletPacker output gates. Deliberately
do not run cross-pallet rescue afterwards: it would fill a closed target pallet.
"""
import time

from src.geometry.flat_top import (
    check_flat_top_full_perimeter, flat_top_group_required,
    flat_top_seam_tolerance, trim_items_to_tail,
)
from src.utils.helpers import repack_ready_item


def pack_fill_rate_group(owner, pallet_type, order, boxes, target, loading_mode):
    start = time.time()
    dims = boxes[0]['pallet_dims']
    remaining = list(boxes)
    plans = []
    stop = loading_mode == 'stop_at_target'
    flat_required = flat_top_group_required(owner._cfg, pallet_type, boxes)
    seam = flat_top_seam_tolerance(owner._cfg)
    while remaining:
        packer = owner._CustomPacker(
            dims, support_ratio_threshold=owner._support_ratio,
            max_candidate_points=120, max_points_per_layer=30,
            constraint_config=owner._cfg,
        )
        packed, _ = packer.pack(
            remaining, num_restarts=4, beam_width=2, candidate_limit=8,
            random_seed=len(plans)+1,
            target_mpm=target if stop else None,
            stop_when_target_met=stop, allow_skip_items=True,
        )
        used = {b['id'] for b in packed}
        rest = [b for b in remaining if b['id'] not in used]
        packed, rest = owner._repair_packed_before_output(packed, rest, dims)
        fallback = False
        if not packed:
            # Single-box fallback has the same safety gates and overweight
            # handling as the historical conservation path; never drop a box.
            packed = owner._build_centered_single_box(
                [remaining[0]], dims, xy_tolerance=owner._xy_tolerance,
                z_tolerance=owner._z_tolerance,
                support_ratio_threshold=owner._support_ratio,
                constraint_config=owner._cfg,
            )
            if not packed:
                raise RuntimeError(f"箱体无法合法放入托盘：box_id={remaining[0].get('id')}")
            used = {b['id'] for b in packed}
            rest = [b for b in remaining if b['id'] not in used]
            fallback = True
        total = sum(float(b.get('min_pack_multiple') or 0) for b in packed)
        if (flat_required and total+1e-12 >= target and
                not check_flat_top_full_perimeter(packed,seam_tolerance_mm=seam)['is_valid']):
            kept, removed = trim_items_to_tail(packed, target, seam)
            packed, rest = owner._repair_packed_before_output(
                kept, [repack_ready_item(b) for b in removed]+rest, dims)
        if not packed:
            raise RuntimeError("当前装箱率与形状约束下无法生成合法托盘，请检查数据和约束设置")
        owner._append_solution(
            plans, packed, pallet_type, order, dims, target, len(plans)+1,
            conservation_fallback=fallback, single_box_fallback=fallback,
        )
        if len(rest) >= len(remaining):
            raise RuntimeError("装箱未取得进展，已停止以防止重复装箱")
        remaining = rest
    return plans, {'packing':time.time()-start,'retry':0.,'topup':0.}, {
        'loading_mode':loading_mode,'target_mpm':target,
    }

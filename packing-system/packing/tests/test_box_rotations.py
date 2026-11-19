from itertools import permutations

import pytest

from run_packing import build_workflow
from src.config import ConstraintConfig
from src.packing import BeamSearchPacker, build_centered_single_box_solution


AXES = ("length", "width", "height")
INPUT_SIZE = (40, 60, 100)


def _box():
    return dict(zip(AXES, INPUT_SIZE), id="box-1", weight=1.0,
                min_pack_multiple=1.0)


@pytest.mark.parametrize("size", list(permutations(INPUT_SIZE)))
def test_beam_and_single_box_fallback_consider_every_orientation(size):
    pallet = dict(zip(AXES, (size[0] + 2, size[1] + 2, size[2])))
    box = _box()
    config = ConstraintConfig(
        allow_box_rotation_3d=True, suction_reachability_enabled=False,
    )
    packer = BeamSearchPacker(pallet, constraint_config=config)
    packed, rest = packer.pack([box], num_restarts=1, random_seed=42)
    centered = build_centered_single_box_solution([box], pallet, constraint_config=config)

    assert rest == []
    for placement in (packed[0], centered[0]):
        assert tuple(placement[f"raw_{axis}"] for axis in AXES) == size
        assert tuple(placement[axis] for axis in AXES) == (
            size[0] + 2, size[1] + 2, size[2],
        )
    assert tuple(box[axis] for axis in AXES) == INPUT_SIZE


def test_rotation_disabled_keeps_fixed_beam_orientation():
    pallet = {"length": 102, "width": 62, "height": 40}
    box = _box()
    config = ConstraintConfig(suction_reachability_enabled=False)
    packed, rest = BeamSearchPacker(pallet, constraint_config=config).pack([box])
    assert packed == []
    assert rest == [box]


def test_workflow_outputs_side_placement_with_original_configured_main_packer():
    pallet = {"length": 102, "width": 62, "height": 40}
    box = dict(_box(), pallet_type="TEST", sales_order_no="ORDER", pallet_dims=pallet)
    config = ConstraintConfig(
        main_packer="gcp", allow_box_rotation_3d=True,
        suction_reachability_enabled=False, shape_polish_enabled=False,
    )
    workflow = build_workflow(constraint_config=config)
    workflow._report_persister = None
    report = workflow.run_with_boxes([box])
    items = [item for plan in report["pallets"] for item in plan["packed_items"]]
    assert [item["id"] for item in items] == [box["id"]]
    assert tuple(items[0][f"raw_{axis}"] for axis in AXES) == (100, 60, 40)
    assert tuple(items[0][axis] for axis in AXES) == (102, 62, 40)


def test_narrow_beam_keeps_first_box_orientations():
    pallet = dict(zip(AXES, (120, 100, 100)))
    boxes = [dict(zip(AXES, (100, 80, 60)), id=f"box-{i}", weight=1.0)
             for i in range(2)]
    config = ConstraintConfig(
        allow_box_rotation_3d=True, suction_reachability_enabled=False,
        xy_tolerance=0,
    )
    packed, rest = BeamSearchPacker(pallet, constraint_config=config).pack(
        boxes, num_restarts=1, beam_width=1, candidate_limit=1, random_seed=42,
    )
    assert rest == []
    assert len(packed) == 2


def test_rotating_a_box_does_not_bypass_heavier_below_constraint():
    from src.geometry.constraint_validator import validate_pallet_constraints
    from src.packing.incremental_gate import incremental_pallet_ok

    pallet = dict(zip(AXES, (100, 100, 200)))
    light = dict(zip(AXES, (100, 90, 100)), id="light", weight=1.0,
                 position={"x": 0, "y": 0, "z": 0})
    heavy = dict(zip(AXES, (100, 100, 90)), id="heavy", weight=2.0,
                 position={"x": 0, "y": 0, "z": 100})
    config = ConstraintConfig(
        allow_box_rotation_3d=True, suction_reachability_enabled=False,
        xy_tolerance=0,
    )
    result = validate_pallet_constraints(
        {"packed_items": [light, heavy]}, pallet, constraint_config=config,
    )
    assert any(v["type"] == "same_size_heavier_below" for v in result["violations"])
    assert not incremental_pallet_ok(heavy, [light], pallet, constraint_config=config)


def test_incremental_repacking_does_not_add_tolerance_twice():
    from src.incremental.service import run_incremental_packing

    pallet = {"length": 102, "width": 62, "height": 40}
    box = dict(_box(), pallet_type="MH423C", sales_order_no="ORDER", pallet_dims=pallet)
    config = ConstraintConfig(
        allow_box_rotation_3d=True, suction_reachability_enabled=False,
        shape_polish_enabled=False,
    )

    def workflow_factory():
        workflow = build_workflow(constraint_config=config)
        workflow._report_persister = None
        return workflow

    result = run_incremental_packing([box], [], workflow_factory)
    assert result.initial_repack_box_count == 1
    (item,) = [item for plan in result.report["pallets"] for item in plan["packed_items"]]
    assert tuple(item[axis] for axis in AXES) == (102, 62, 40)

from collections import Counter
import math
import pytest
from src.main.success_target import SuccessTarget


@pytest.mark.parametrize('value',[0.0001,0.7317,0.95,1.0])
def test_custom_fill_target(value):
    target=SuccessTarget.from_mapping({'mode':'fill_rate','threshold':value,'loading_mode':'stop_at_target'})
    assert target.threshold==value
    assert target.loading_mode=='stop_at_target'
    assert target.to_dict()['loading_mode']=='stop_at_target'


@pytest.mark.parametrize('value',[0,-0.1,1.01,70,math.nan,math.inf,-math.inf])
def test_invalid_fill_target(value):
    with pytest.raises(ValueError,match='装载率目标'):
        SuccessTarget.from_mapping({'mode':'fill_rate','threshold':value})


def make_workflow(threshold,mode):
    from run_packing import build_workflow
    from src.config.constraint_config import ConstraintConfig
    cfg=ConstraintConfig(main_packer='beam',suction_reachability_enabled=False,
        xy_tolerance=0,center_of_mass_tolerance=1.0,flat_top_full_perimeter_enabled=False,
        shape_polish_enabled=False,dual_path_enabled=False)
    target=SuccessTarget.from_mapping({'mode':'fill_rate','threshold':threshold,'loading_mode':mode})
    wf=build_workflow(constraint_config=cfg,success_target=target)
    wf._report_persister=None
    return wf


def boxes(count=8,order='A'):
    dims={'length':100.0,'width':100.0,'height':400.0}
    return [dict(id=f'{order}-{i}',type='cube',length=100.,width=100.,height=100.,
        raw_length=100.,raw_width=100.,raw_height=100.,weight=1.,min_pack_multiple=12.,
        pallet_type='MH423C',sales_order_no=order,pallet_dims=dims.copy()) for i in range(count)]


@pytest.mark.parametrize('mode,expected',[('stop_at_target',[2,2,2,2]),('maximize',[4,4])])
def test_real_packing_stops_or_continues_on_same_input(mode,expected):
    data=boxes()
    report=make_workflow(.5,mode).run_with_boxes(data)
    pallets=report['pallets']
    assert [len(p['packed_items']) for p in pallets]==expected
    ids=[b['id'] for p in pallets for b in p['packed_items']]
    assert Counter(ids)==Counter(b['id'] for b in data)
    assert all(b['min_pack_multiple']==12. for p in pallets for b in p['packed_items'])
    assert report['success_target']['loading_mode']==mode


def test_non_divisible_target_and_tail_preserve_boxes():
    report=make_workflow(.7317,'stop_at_target').run_with_boxes(boxes())
    assert [len(p['packed_items']) for p in report['pallets']]==[3,3,2]
    assert [p['final_status'] for p in report['pallets']]==['SUCCESS','SUCCESS','FAILED']
    assert all(len(p['packed_items'][:-1])*.25 < .7317 for p in report['pallets'])


def test_stop_mode_keeps_orders_separate():
    report=make_workflow(.5,'stop_at_target').run_with_boxes(boxes(3,'A')+boxes(3,'B'))
    assert len(report['pallets'])==4
    assert all(len({b['id'].split('-')[0] for b in p['packed_items']})==1 for p in report['pallets'])

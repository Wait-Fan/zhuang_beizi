import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import yaml
from PyQt5 import QtWidgets
import realtime_dashboard_v3_clean as dashboard


def test_custom_percentage_controls_round_trip(tmp_path,monkeypatch):
    monkeypatch.setattr(dashboard,'_start_local_wcs_receiver',lambda *_:None)
    app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window=dashboard.IndustrialPackingWorkbenchClean(tmp_path)
    try:
        window.cmb_success_target.setCurrentIndex(1)
        window.sp_fill_rate.setValue(73.17)
        window.cmb_loading_mode.setCurrentIndex(window.cmb_loading_mode.findData('stop_at_target'))
        assert window.current_success_target()=={'mode':'fill_rate','threshold':.7317,'loading_mode':'stop_at_target'}
        window.cmb_loading_mode.setCurrentIndex(window.cmb_loading_mode.findData('maximize'))
        assert window.current_success_target()['loading_mode']=='maximize'
        window.sp_fill_rate.lineEdit().setText('77.23 %')
        assert window.current_success_target()['threshold']==77.23/100
        window.cmb_success_target.setCurrentIndex(0)
        assert window.current_success_target()=={'mode':'index','threshold':192.}
        assert window.sp_fill_rate.isHidden()
    finally:
        window.close();app.processEvents()


def test_both_config_routes_keep_custom_rate_and_loading_mode(tmp_path):
    project=tmp_path/'packing-system';project.mkdir()
    base=project/'config.yaml';base.write_text('run_mode: normal\ndatabase:\n  host: localhost\n  user: test\n  database: test\n',encoding='utf8')
    excel=tmp_path/'packing-workspace/data/input.xlsx';excel.parent.mkdir(parents=True)
    excel.write_bytes(b'placeholder')
    target={'mode':'fill_rate','threshold':.7317,'loading_mode':'stop_at_target'}
    for output in [dashboard._write_ui_config(project,base,excel,'normal',success_target=target),
                   dashboard._write_ui_config_api_only(project,base,200,success_target=target)]:
        config=yaml.safe_load(output.read_text(encoding='utf8'))
        assert config['success_target']==target

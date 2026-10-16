"""Focused regression checks for Mado Sallom's HarborFlow Tasks 4 and 8."""
import csv
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import operations
import data_access
import main


def test_task4_profile_aggregation_and_destinations():
    shipments = {
        's1': {'customer':'  Acme AB  ', 'weight_kg':2.25,'priority':'EXPRESS','destination':'OSL'},
        's2': {'customer':'acme ab','weight_kg':3.5,'priority':'standard','destination':'CPH'},
        's3': {'customer':'ACME AB','weight_kg':4,'priority':'express','destination':'OSL'},
        's4': {'customer':'Else','weight_kg':100,'priority':'EXPRESS','destination':'GOT'},
    }
    profile=operations.build_customer_profile(shipments,' acme ab ')
    assert profile == {'customer':'  Acme AB  ','shipment_count':3,'total_weight_kg':'9.75','express_count':2,'destinations':'CPH|OSL'}
    assert operations.build_customer_profile(shipments,'missing') is None


def test_task4_save_upserts_case_insensitively(tmp_path):
    path=tmp_path/'exports'/'profiles.csv'
    first={'customer':'Acme AB','shipment_count':1,'total_weight_kg':'1.00','express_count':0,'destinations':'GOT'}
    second={**first,'customer':'acme ab','shipment_count':2,'total_weight_kg':'3.00'}
    data_access.save_customer_profile(first,path)
    data_access.save_customer_profile(second,path)
    with path.open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==1
    assert rows[0]['shipment_count']=='2'
    assert rows[0]['total_weight_kg']=='3.00'


def test_task8_recommendation_thresholds_and_order():
    assert operations.weather_recommendations(44,7.9,2.4)==['Normal operating plan.']
    assert operations.weather_recommendations(45,0,0)==['Suspend crane operations.']
    assert operations.weather_recommendations(0,0,2.5)==['Arrange tug assistance.']
    assert operations.weather_recommendations(44,8,0)==['Prepare covered handling.']
    assert operations.weather_recommendations(45,8,2.5)==['Suspend crane operations.','Arrange tug assistance.']
    assert operations.weather_recommendations(44,8,2.5)==['Arrange tug assistance.','Prepare covered handling.']


def test_task8_invalid_date_reprompts_only_date(capsys):
    inputs=iter(['Nordic Relay','bad','2026-02-30','2026-10-14'])
    with patch('builtins.input',side_effect=lambda prompt: next(inputs)) as mock_input, \
         patch.object(data_access,'load_vessels',return_value=({},[])), \
         patch.object(data_access,'load_port_calls',return_value=([],[])), \
         patch.object(data_access,'load_weather',return_value=([],[])):
        main.run_weather_risk()
    assert [c.args[0] for c in mock_input.call_args_list] == [
        'Vessel name: ', 'Reference date (YYYY-MM-DD): ',
        'Reference date (YYYY-MM-DD): ', 'Reference date (YYYY-MM-DD): '
    ]
    output=capsys.readouterr().out
    assert output.count('Error - Date must use YYYY-MM-DD.')==2
    assert 'Vessel not found.' in output


def test_task8_missing_forecast_exact_message_and_continues(capsys):
    calls=[{'call_id':'A','port_code':'GOT','arrival_date':'2026-10-14'},
           {'call_id':'B','port_code':'OSL','arrival_date':'2026-10-15'}]
    report={'status':'ok','reports':[
        {'call':calls[0],'forecast':None,'recommendations':[]},
        {'call':calls[1],'forecast':{'wind_kmh':10,'precipitation_mm':0,'wave_height_m':0},'recommendations':['Normal operating plan.']} ]}
    with patch('builtins.input',side_effect=['Nordic Relay','2026-10-14']), \
         patch.object(data_access,'load_vessels',return_value=({},[])), \
         patch.object(data_access,'load_port_calls',return_value=([],[])), \
         patch.object(data_access,'load_weather',return_value=([],[])), \
         patch.object(operations,'assess_weather_risk',return_value=report):
        main.run_weather_risk()
    output=capsys.readouterr().out
    assert 'Forecast unavailable.' in output
    assert 'Weather forecast unavailable.' not in output
    assert 'Nordic Relay | OSL | 15 October 2026' in output

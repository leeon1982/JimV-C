#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Blueprint
import json
import jimit as ji

from api.base import Base
from models import CPUMemory, Traffic, DiskIO, Utils, Rules


__author__ = 'James Iter'
__date__ = '2017/7/2'
__contact__ = 'james.iter.cn@gmail.com'
__copyright__ = '(c) 2017 by James Iter.'


blueprint = Blueprint(
    'api_performance',
    __name__,
    url_prefix='/api/performance'
)

blueprints = Blueprint(
    'api_performances',
    __name__,
    url_prefix='/api/performances'
)


cpu_memory = Base(the_class=CPUMemory, the_blueprint=blueprint, the_blueprints=blueprints)
traffic = Base(the_class=Traffic, the_blueprint=blueprint, the_blueprints=blueprints)
disk_io = Base(the_class=DiskIO, the_blueprint=blueprint, the_blueprints=blueprints)


@Utils.dumps2response
def r_cpu_memory_get_by_filter():
    return cpu_memory.get_by_filter()


@Utils.dumps2response
def r_traffic_get_by_filter():
    return traffic.get_by_filter()


@Utils.dumps2response
def r_disk_io_get_by_filter():
    return disk_io.get_by_filter()


def get_performance_data(uuid, uuid_field, the_class=None, granularity='hour'):

    args_rules = [
        Rules.UUID.value,
    ]

    try:
        ji.Check.previewing(args_rules, {'uuid': uuid})
        uuids_str = ':'.join([uuid_field, 'in', uuid])

        ret = dict()
        ret['state'] = ji.Common.exchange_state(20000)
        ret['data'] = list()

        max_limit = 10080
        ts = ji.Common.ts()
        _boundary = ts - 60 * 60
        if granularity == 'hour':
            _boundary = ts - 60 * 60

        elif granularity == 'six_hours':
            _boundary = ts - 60 * 60 * 6

        elif granularity == 'day':
            _boundary = ts - 60 * 60 * 24

        elif granularity == 'seven_days':
            _boundary = ts - 60 * 60 * 24 * 7

        else:
            pass

        filter_str = ';'.join([uuids_str, 'timestamp:gt:' + _boundary.__str__()])

        _rows, _rows_count = the_class.get_by_filter(
            offset=0, limit=max_limit, order_by='id', order='asc', filter_str=filter_str)

        def smooth_data(boundary=0, interval=60, now_ts=ji.Common.ts(), rows=None):
            needs = list()
            data = list()

            for t in range(boundary + interval, now_ts, interval):
                needs.append(t - t % interval)

            for row in rows:
                if row['timestamp'] % interval != 0:
                    continue

                if needs.__len__() > 0:
                    t = needs.pop(0)
                else:
                    t = now_ts

                while t < row['timestamp']:
                    data.append({
                        'timestamp': t,
                        'cpu_load': None,
                        'memory_available': None,
                        'memory_unused': None,
                        'rx_packets': None,
                        'rx_bytes': None,
                        'tx_packets': None,
                        'tx_bytes': None,
                        'rd_req': None,
                        'rd_bytes': None,
                        'wr_req': None,
                        'wr_bytes': None
                    })

                    if needs.__len__() > 0:
                        t = needs.pop(0)
                    else:
                        t = now_ts

                data.append(row)

            return data

        if granularity == 'day':
            ret['data'] = smooth_data(boundary=_boundary, interval=600, now_ts=ts, rows=_rows)

        if granularity == 'seven_days':
            ret['data'] = smooth_data(boundary=_boundary, interval=600, now_ts=ts, rows=_rows)

        else:
            ret['data'] = smooth_data(boundary=_boundary, interval=60, now_ts=ts, rows=_rows)

        return ret

    except ji.PreviewingError, e:
        return json.loads(e.message)


@Utils.dumps2response
def r_cpu_memory_last_hour(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=CPUMemory, granularity='hour')


@Utils.dumps2response
def r_cpu_memory_last_six_hours(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=CPUMemory, granularity='six_hours')


@Utils.dumps2response
def r_cpu_memory_last_day(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=CPUMemory, granularity='day')


@Utils.dumps2response
def r_cpu_memory_last_seven_days(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=CPUMemory, granularity='seven_days')


@Utils.dumps2response
def r_traffic_last_hour(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=Traffic, granularity='hour')


@Utils.dumps2response
def r_traffic_last_six_hours(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=Traffic, granularity='six_hours')


@Utils.dumps2response
def r_traffic_last_day(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=Traffic, granularity='day')


@Utils.dumps2response
def r_traffic_last_seven_days(uuid):
    return get_performance_data(uuid=uuid, uuid_field='guest_uuid', the_class=Traffic, granularity='seven_days')


@Utils.dumps2response
def r_disk_io_last_hour(uuid):
    return get_performance_data(uuid=uuid, uuid_field='disk_uuid', the_class=DiskIO, granularity='hour')


@Utils.dumps2response
def r_disk_io_last_six_hours(uuid):
    return get_performance_data(uuid=uuid, uuid_field='disk_uuid', the_class=DiskIO, granularity='six_hours')


@Utils.dumps2response
def r_disk_io_last_day(uuid):
    return get_performance_data(uuid=uuid, uuid_field='disk_uuid', the_class=DiskIO, granularity='day')


@Utils.dumps2response
def r_disk_io_last_seven_days(uuid):
    return get_performance_data(uuid=uuid, uuid_field='disk_uuid', the_class=DiskIO, granularity='seven_days')


@Utils.dumps2response
def r_current_top_10():

    # JimV 设计的 Guests 容量为 4000 个
    volume = 4000
    limit = volume
    end_ts = ji.Common.ts() - 60
    start_ts = end_ts - 60

    # 避免落在时间边界上，导致过滤条件的范围落空
    if start_ts % 60 == 0:
        start_ts -= 1

    ret = dict()
    ret['state'] = ji.Common.exchange_state(20000)
    ret['data'] = {
        'cpu_load': list(),
        'rw_bytes': list(),
        'rw_req': list(),
        'rt_bytes': list(),
        'rt_packets': list()
    }

    filter_str = ';'.join([':'.join(['timestamp', 'gt', start_ts.__str__()]),
                           ':'.join(['timestamp', 'lt', end_ts.__str__()])])

    rows, _ = CPUMemory.get_by_filter(limit=limit, filter_str=filter_str)
    rows.sort(key=lambda k: k['cpu_load'], reverse=True)

    ret['data']['cpu_load'] = rows[0:10]

    rows, _ = DiskIO.get_by_filter(limit=limit, filter_str=filter_str)
    for i in range(rows.__len__()):
        rows[i]['rw_bytes'] = rows[i]['rd_bytes'] + rows[i]['wr_bytes']
        rows[i]['rw_req'] = rows[i]['rd_req'] + rows[i]['wr_req']

    rows.sort(key=lambda k: k['rw_bytes'], reverse=True)
    ret['data']['rw_bytes'] = rows[0:10]

    rows.sort(key=lambda k: k['rw_req'], reverse=True)
    ret['data']['rw_req'] = rows[0:10]

    rows, _ = Traffic.get_by_filter(limit=limit, filter_str=filter_str)
    for i in range(rows.__len__()):
        rows[i]['rt_bytes'] = rows[i]['rx_bytes'] + rows[i]['tx_bytes']
        rows[i]['rt_packets'] = rows[i]['rx_packets'] + rows[i]['tx_packets']

    rows.sort(key=lambda k: k['rt_bytes'], reverse=True)
    ret['data']['rt_bytes'] = rows[0:10]

    rows.sort(key=lambda k: k['rt_packets'], reverse=True)
    ret['data']['rt_packets'] = rows[0:10]

    return ret


@Utils.dumps2response
def r_last_10_minutes_top_10():

    _range = 10
    volume = 4000
    limit = volume * _range
    end_ts = ji.Common.ts() - 60
    start_ts = end_ts - 60 * _range

    # 避免落在时间边界上，导致过滤条件的范围落空
    if start_ts % 60 == 0:
        start_ts -= 1

    ret = dict()
    ret['state'] = ji.Common.exchange_state(20000)
    ret['data'] = {
        'cpu_load': list(),
        'rw_bytes': list(),
        'rw_req': list(),
        'rt_bytes': list(),
        'rt_packets': list()
    }

    filter_str = ';'.join([':'.join(['timestamp', 'gt', start_ts.__str__()]),
                           ':'.join(['timestamp', 'lt', end_ts.__str__()])])

    # cpu 负载
    guests_uuid_mapping = dict()
    rows, _ = CPUMemory.get_by_filter(limit=limit, filter_str=filter_str)
    for row in rows:
        if row['guest_uuid'] not in guests_uuid_mapping:
            guests_uuid_mapping[row['guest_uuid']] = {'cpu_load': 0, 'count': 0}

        guests_uuid_mapping[row['guest_uuid']]['cpu_load'] += row['cpu_load']
        guests_uuid_mapping[row['guest_uuid']]['count'] += 1

    rows = list()
    for k, v in guests_uuid_mapping.items():

        # 忽略除数为 0 的情况
        if v['cpu_load'] == 0:
            continue

        rows.append({'guest_uuid': k, 'cpu_load': v['cpu_load'] / v['count']})

    rows.sort(key=lambda _k: _k['cpu_load'], reverse=True)

    ret['data']['cpu_load'] = rows[0:10]

    # 磁盘使用统计
    guests_uuid_mapping.clear()
    rows, _ = DiskIO.get_by_filter(limit=limit, filter_str=filter_str)
    for row in rows:
        if row['disk_uuid'] not in guests_uuid_mapping:
            guests_uuid_mapping[row['disk_uuid']] = {'rw_bytes': 0, 'rw_req': 0}

        guests_uuid_mapping[row['disk_uuid']]['rw_bytes'] += row['rd_bytes'] + row['wr_bytes']
        guests_uuid_mapping[row['disk_uuid']]['rw_req'] += row['rd_req'] + row['wr_req']

    rows = list()
    for k, v in guests_uuid_mapping.items():
        rows.append({'disk_uuid': k, 'rw_bytes': v['rw_bytes'] * 60 * _range, 'rw_req': v['rw_req'] * 60 * _range})

    rows.sort(key=lambda _k: _k['rw_bytes'], reverse=True)
    ret['data']['rw_bytes'] = rows[0:10]

    rows.sort(key=lambda _k: _k['rw_req'], reverse=True)
    ret['data']['rw_req'] = rows[0:10]

    # 网络流量
    guests_uuid_mapping.clear()
    rows, _ = Traffic.get_by_filter(limit=limit, filter_str=filter_str)
    for row in rows:
        if row['guest_uuid'] not in guests_uuid_mapping:
            guests_uuid_mapping[row['guest_uuid']] = {'rt_bytes': 0, 'rt_packets': 0}

        guests_uuid_mapping[row['guest_uuid']]['rt_bytes'] += row['rx_bytes'] + row['tx_bytes']
        guests_uuid_mapping[row['guest_uuid']]['rt_packets'] += row['rx_packets'] + row['tx_packets']

    rows = list()
    for k, v in guests_uuid_mapping.items():
        rows.append({'guest_uuid': k, 'rt_bytes': v['rt_bytes'] * 60 * _range,
                     'rt_packets': v['rt_packets'] * 60 * _range})

    rows.sort(key=lambda _k: _k['rt_bytes'], reverse=True)
    ret['data']['rt_bytes'] = rows[0:10]

    rows.sort(key=lambda _k: _k['rt_packets'], reverse=True)
    ret['data']['rt_packets'] = rows[0:10]

    return ret




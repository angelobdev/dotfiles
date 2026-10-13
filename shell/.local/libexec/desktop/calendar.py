#!/usr/bin/env python3
"""Read calendar occurrences from existing Evolution Data Server/Online Accounts."""
from i18n import tr
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import sys
import gi
gi.require_version('ECal', '2.0')
gi.require_version('EDataServer', '1.2')
gi.require_version('ICalGLib', '3.0')
from gi.repository import ECal, EDataServer, ICalGLib


def timezone():
    name = os.environ.get('TZ', '')
    if not name:
        target = str(Path('/etc/localtime').resolve())
        name = target.split('/zoneinfo/', 1)[-1] if '/zoneinfo/' in target else 'UTC'
    return ICalGLib.Timezone.get_builtin_timezone(name) or ICalGLib.Timezone.get_utc_timezone()


def occurrence(component, start, end, zone, source_uid):
    if component.get_status() == ICalGLib.PropertyStatus.CANCELLED:
        return None
    all_day = start.is_date()
    def timestamp(value):
        if all_day:
            return int(dt.datetime(value.get_year(), value.get_month(), value.get_day()).timestamp() * 1000)
        return value.as_timet_with_zone(value.get_timezone() or zone) * 1000
    begin, finish = timestamp(start), timestamp(end)
    return dict(id=f'{source_uid}:{component.get_uid()}:{begin}', source=source_uid,
                title=component.get_summary() or tr('Senza titolo'),
                location=component.get_location() or '', start=begin, end=finish,
                allDay=all_day)


def read_source(source, start, end, zone):
    uid = source.get_uid()
    row = dict(uid=uid, name=source.get_display_name(), color=source.get_extension('Calendar').get_color() or '#d4d6dc', error='')
    events = []
    try:
        client = ECal.Client.connect_sync(source, ECal.ClientSourceType.EVENTS, 1, None)
        client.set_default_timezone(zone)
        def collect(component, instance_start, instance_end, *_):
            event = occurrence(component, instance_start, instance_end, zone, uid)
            if event:
                events.append(event)
            return True
        client.generate_instances_sync(start, end, None, collect, None)
    except Exception as error:
        row['error'] = str(error)
    return row, events


def read(start, end, wanted):
    registry = EDataServer.SourceRegistry.new_sync(None)
    sources = [s for s in registry.list_enabled('Calendar') if not wanted or s.get_uid() in wanted]
    zone = timezone()
    rows, events = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(read_source, source, start, end, zone) for source in sources]
        for result in concurrent.futures.as_completed(futures):
            source, found = result.result()
            rows.append(source)
            events.extend(found)
    events.sort(key=lambda e: (e['start'], e['title']))
    rows.sort(key=lambda s: s['name'].casefold())
    return dict(sources=rows, events=events)


def main():
    try:
        start, end = int(sys.argv[1]), int(sys.argv[2])
        wanted = json.loads(sys.argv[3])
        if not 0 <= start < end or end - start > 63 * 86400 or not isinstance(wanted, list) or not all(isinstance(s, str) for s in wanted):
            raise ValueError(tr('Intervallo o calendari non validi.'))
        print(json.dumps(read(start, end, wanted), ensure_ascii=False))
        return 0
    except Exception as error:
        print(json.dumps(dict(error=str(error)), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())

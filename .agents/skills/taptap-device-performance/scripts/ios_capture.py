#!/usr/bin/env python3
"""Bounded USB WebInspector collection for this Cocos/TapTap project.
Requires pymobiledevice3 11.55.0 (isolated host dependency, not shipped in game).
"""
import argparse
import asyncio
import contextlib
import datetime
import json
import logging
from pathlib import Path
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


async def run(args):
    from pymobiledevice3.lockdown import create_using_usbmux
    from pymobiledevice3.services.webinspector import WebinspectorService
    from pymobiledevice3.usbmux import list_devices
    devices = [d for d in await asyncio.wait_for(list_devices(), 5) if d.connection_type == 'USB']
    if args.udid:
        devices = [d for d in devices if d.matches_udid(args.udid)]
    if len(devices) != 1:
        raise RuntimeError('Expected one USB device; use --udid to select: ' + ', '.join(d.serial for d in devices))
    out = Path(args.out).resolve() if args.out else None
    if out:
        # Never overwrite an earlier baseline or mix two recordings.
        out.mkdir(parents=True, exist_ok=False)
    ld = await asyncio.wait_for(create_using_usbmux(serial=args.udid, autopair=False, connection_type='USB'), 15)
    wi = WebinspectorService(ld)
    session = None
    active = []
    events = []
    dropped = 0
    key = '__taptapPerf_' + uuid.uuid4().hex
    meta = {'startedUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'profile': args.profile,
            'device': {k: ld.all_values.get(k) for k in ('ProductType', 'ProductVersion')}, 'warnings': []}
    collector = (HERE / 'collect.js').read_text()

    async def command(method, params=None):
        value = await asyncio.wait_for(session.send_and_receive({'method': method, 'params': params or {}}), 15)
        if session.target_id is not None:
            value = json.loads(value['params']['message'])
        if 'error' in value:
            raise RuntimeError(f'{method}: {value["error"]}')
        return value.get('result', {})

    async def evaluate(operation):
        value = await command('Runtime.evaluate', {'expression': '(' + collector + ')(' + json.dumps(
            {'key': key, 'seconds': args.seconds, 'label': args.label, 'operation': operation}) + ')',
            'returnByValue': True, 'doNotPauseOnExceptionsAndMuteConsole': True})
        if value.get('wasThrown'):
            raise RuntimeError(str(value.get('result')))
        return json.loads(value['result']['value'])

    def receive(event):
        nonlocal dropped
        if len(events) < 20000:
            events.append({'hostMonotonic': time.monotonic(), **event})
        else:
            dropped += 1

    try:
        await asyncio.wait_for(wi.connect(), 30)
        pages = await asyncio.wait_for(wi.get_open_application_pages(timeout=5), 10)
        # Applications can arrive after the initial listing; request their pages once more.
        if not any(x.application.bundle == args.bundle for x in pages):
            await asyncio.wait_for(wi.get_open_pages(), 5)
            pages = await asyncio.wait_for(wi.get_open_application_pages(timeout=2), 5)
            meta['targetListingRefreshed'] = True
        rows = [x for x in pages if x.application.bundle == args.bundle]
        meta['targets'] = [{'application': x.application.id_, 'page': x.page.id_, 'type': x.page.type_.value,
                            'url': x.page.web_url, 'attached': bool(x.page.web_connection_id)} for x in rows]
        if args.mode == 'list':
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            return
        candidates = [x for x in rows if not x.page.web_connection_id and
                      (str(x.page.id_) == args.page if args.page else x.page.web_url.startswith('tjapp://game-runtime'))]
        if args.application:
            candidates = [x for x in candidates if x.application.id_ == args.application]
        if len(candidates) != 1:
            raise RuntimeError('Expected one unattached TapTap game target; use list and --page/--application. '
                               'Keep the phone unlocked and game in foreground with debugging enabled.')
        target = candidates[0]
        meta['selected'] = {'application': target.application.id_, 'page': target.page.id_, 'url': target.page.web_url}
        session = await asyncio.wait_for(wi.inspector_session(target.application, target.page), 15)
        for domain in ('ScriptProfiler', 'CPUProfiler', 'Memory'):
            for suffix in ('trackingStart', 'trackingUpdate', 'trackingComplete'):
                session.response_methods[f'{domain}.{suffix}'] = receive
        for name in ('Debugger.scriptParsed', 'Debugger.paused', 'Debugger.resumed', 'Heap.garbageCollected'):
            session.response_methods[name] = receive
        if args.mode == 'snapshot':
            meta['snapshot'] = await evaluate('snapshot')
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            return
        if args.profile:
            try:
                await command('Debugger.enable')
                meta['debuggerEnabled'] = True
            except Exception as exc:
                meta['warnings'].append(str(exc))
            for domain in ('CPUProfiler', 'Memory', 'ScriptProfiler'):
                try:
                    await command(domain + '.startTracking', {'includeSamples': True} if domain == 'ScriptProfiler' else {})
                    active.append(domain)
                except Exception as exc:
                    meta['warnings'].append(str(exc))
        meta['hostCaptureStart'] = time.monotonic()
        meta['start'] = await evaluate('start')
        print(json.dumps({'captureStarted': str(out), 'seconds': args.seconds, 'version': meta['start']['baseline']['version']}), flush=True)
        await asyncio.sleep(args.seconds + .3)
        capture = await evaluate('take')
        meta['hostCaptureEnd'] = time.monotonic()
        dump(out / 'frames.json', capture)
        for domain in reversed(active[:]):
            await command(domain + '.stopTracking')
            active.remove(domain)
        # WebKit delivers trackingComplete asynchronously after the stop response.
        if args.profile:
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and not any(e['method'] == 'ScriptProfiler.trackingComplete' for e in events):
                await asyncio.sleep(.1)
        if args.sources:
            source_dir = out / 'sources'
            source_dir.mkdir()
            scripts = {str(e['params']['scriptId']): e['params'] for e in events if e['method'] == 'Debugger.scriptParsed'}
            index = []
            for sid, info in scripts.items():
                # Source reads stay within the selected TapTap runtime, including blank generated scripts.
                url = info.get('url', '')
                if url and not url.startswith('tjapp://'):
                    continue
                try:
                    result = await command('Debugger.getScriptSource', {'scriptId': sid})
                    filename = f'script-{len(index)}.js'
                    (source_dir / filename).write_text(result['scriptSource'])
                    index.append({'file': filename, **info})
                except Exception as exc:
                    meta['warnings'].append(str(exc))
            dump(source_dir / 'index.json', index)
    except BaseException as exc:
        meta['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        if session:
            for domain in reversed(active):
                try:
                    await command(domain + '.stopTracking')
                except Exception as exc:
                    meta['warnings'].append('Stop: ' + str(exc))
            try:
                meta['cleanup'] = await evaluate('cleanup')
            except Exception as exc:
                meta['warnings'].append('Cleanup not confirmed; collector watchdog expires after capture + 20s: ' + str(exc))
            if meta.get('debuggerEnabled'):
                with contextlib.suppress(Exception):
                    await command('Debugger.disable')
            # This library version exposes no public InspectorSession.close().
            session._receive_task.cancel()
            await asyncio.gather(session._receive_task, return_exceptions=True)
        for close in (wi.close, ld.close):
            try:
                await asyncio.wait_for(close(), 5)
            except Exception as exc:
                meta['warnings'].append('Disconnect: ' + str(exc))
        if out:
            meta['eventsDropped'] = dropped
            dump(out / 'metadata.json', meta)
            dump(out / 'events.json', events)
            print(json.dumps({'saved': str(out), 'cleanup': meta.get('cleanup'), 'warnings': meta['warnings']}, ensure_ascii=False), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['list', 'snapshot', 'capture'])
    p.add_argument('--bundle', default='com.easyplay.taptap.now')
    p.add_argument('--udid', help='Select a paired USB device when more than one is connected')
    p.add_argument('--page', help='Page ID from list, never assume it is stable')
    p.add_argument('--application', help='Application ID from list, when page IDs are ambiguous')
    p.add_argument('--out', help='New output directory (required for capture)')
    p.add_argument('--seconds', type=float, default=20)
    p.add_argument('--label', default='standing-baseline')
    p.add_argument('--profile', action='store_true', help='Separate, instrumented CPU/JS/memory diagnostic run')
    p.add_argument('--sources', action='store_true', help='Save selected target JS sources for stack mapping; requires --profile')
    args = p.parse_args()
    if not 1 <= args.seconds <= 60 or (args.mode == 'capture' and not args.out) or (args.sources and not args.profile):
        p.error('Use 1–60 seconds, --out for capture, and --profile with --sources')
    logging.basicConfig(level=logging.CRITICAL)
    try:
        asyncio.run(run(args))
    except (Exception, KeyboardInterrupt) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

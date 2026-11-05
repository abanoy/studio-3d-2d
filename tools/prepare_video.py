"""Local video -> bounded, editable RGBA holds. Never modifies a scene or source."""
from pathlib import Path
from fractions import Fraction
import argparse
import json
import math
import os
import re
import subprocess
import time

try:
    from . import prepare_krita as raster
except ImportError:
    import prepare_krita as raster

SUFFIXES = {'.mp4', '.mov', '.mkv', '.webm', '.avi'}
DEMUXERS = 'mov,matroska,webm,avi'


def run(args, folder, cancel, timeout=60, frames=None):
    raster.check_cancel(cancel)
    log = folder / 'video-converter.log'
    with log.open('ab') as stream:
        child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=stream,
                                 stderr=stream, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        started = time.monotonic()
        try:
            while child.poll() is None:
                raster.check_cancel(cancel)
                if time.monotonic() - started > timeout:
                    raise ValueError('Video conversion exceeded its time limit')
                if log.stat().st_size > 2 * 1024**2:
                    raise ValueError('Video converter produced excessive diagnostics')
                if frames:
                    files = list(frames.glob('*.png'))
                    if len(files) > 240 or sum(p.stat().st_size for p in files) > raster.MAX_NORMALIZED_BYTES:
                        raise ValueError('Video exceeds its frame/disk budget')
                time.sleep(.025)
            raster.check_cancel(cancel)
            if child.returncode:
                raise ValueError('Video conversion failed; see ' + str(log))
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=3)


def source_path(value):
    text = str(value)
    if text.startswith(('//', '\\\\')) or '://' in text:
        raise ValueError('Choose a local video file')
    path = Path(text).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in SUFFIXES:
        raise ValueError('Choose MP4, MOV, MKV, WebM or AVI video')
    if not 1 <= path.stat().st_size <= raster.MAX_SOURCE:
        raise ValueError('Video source must fit the 192MiB limit')
    return path


def inspect(source, ffmpeg, folder, cancel):
    path = source_path(source)
    identity = raster.sha(path)
    probe = Path(ffmpeg).with_name('ffprobe.exe' if os.name == 'nt' else 'ffprobe')
    if not Path(ffmpeg).is_file() or not probe.is_file():
        raise ValueError('Installed FFmpeg and neighboring FFprobe are required')
    result = folder / 'probe.json'
    # File-only protocols and explicit container admission exclude network playlists.
    args = [str(probe), '-v', 'error', '-max_alloc', '268435456',
            '-protocol_whitelist', 'file', '-format_whitelist', DEMUXERS,
            '-select_streams', 'v:0', '-show_streams', '-show_format', '-of', 'json', str(path)]
    # stdout is bounded independently of diagnostic output; ffprobe only reports
    # stream/format metadata, never per-frame payloads.
    with result.open('xb') as out, (folder / 'probe.log').open('wb') as log:
        child = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=log,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        started = time.monotonic()
        try:
            while child.poll() is None:
                raster.check_cancel(cancel)
                if time.monotonic() - started > 15 or result.stat().st_size > 1024**2 or (folder / 'probe.log').stat().st_size > 1024**2:
                    raise ValueError('Video inspection exceeded its resource limit')
                time.sleep(.025)
            if child.returncode:
                raise ValueError('Cannot inspect this video container')
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)
    if result.stat().st_size > 1024**2:
        raise ValueError('Video metadata exceeds its limit')
    data = json.loads(result.read_bytes())
    streams = data.get('streams', [])
    if len(streams) != 1 or streams[0].get('disposition', {}).get('attached_pic'):
        raise ValueError('Video needs an ordinary picture stream')
    stream = streams[0]
    width = raster.number(stream.get('width'), 'video width', 1, 32768)
    height = raster.number(stream.get('height'), 'video height', 1, 32768)
    if width * height > raster.MAX_PIXELS:
        raise ValueError('Video exceeds16million pixels')
    # Rotated and non-square-pixel sources need an explicit preparation policy.
    if stream.get('sample_aspect_ratio', '1:1') not in ('1:1', 'N/A') or any(row.get('rotation', 0) for row in stream.get('side_data_list', [])):
        raise ValueError('Convert rotated or non-square-pixel video before importing')
    try:
        rate = Fraction(stream['avg_frame_rate'])
        if stream.get('duration_ts') and stream.get('time_base'):
            duration = Fraction(stream['duration_ts']) * Fraction(stream['time_base'])
        elif stream.get('duration'):
            duration = Fraction(stream['duration'])
        else:
            # Matroska/WebM often puts per-stream duration in a tag. Container
            # duration can include a longer ignored audio track; do not invent
            # extra picture holds just because that audio continues.
            tag = stream.get('tags', {}).get('DURATION', '')
            if re.fullmatch(r'[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?', tag):
                hours, minutes, seconds = tag.split(':')
                duration = int(hours)*3600 + int(minutes)*60 + Fraction(seconds)
            elif stream.get('nb_frames') and rate > 0:
                duration = Fraction(stream['nb_frames']) / rate
            else:
                raise ValueError('Video stream has no usable duration')
    except (KeyError, ValueError, ZeroDivisionError):
        raise ValueError('Video has no usable timing') from None
    if not 0 < rate <= 240 or max(rate.numerator, rate.denominator) > 1_000_000_000 or not 0 < duration <= 60 or max(duration.numerator, duration.denominator) > 1_000_000_000:
        raise ValueError('Video timing exceeds the supported 60second/240fps bounds')
    raster.check_cancel(cancel)
    if raster.sha(path) != identity:
        raise ValueError('Video changed during inspection')
    return dict(source=str(path), source_sha256=identity, width=width, height=height,
                source_rate=[rate.numerator, rate.denominator],
                source_duration=[duration.numerator, duration.denominator],
                render_supported=True)


def key_settings(value):
    if not isinstance(value, dict) or set(value) != {'enabled', 'color', 'similarity', 'blend'}:
        raise ValueError('Invalid chroma settings')
    if type(value['enabled']) is not bool or value['color'] not in ('00ff00', '0000ff'):
        raise ValueError('Choose green or blue chroma color')
    for name, low, high in [('similarity', .01, 1), ('blend', 0, 1)]:
        number = value[name]
        if type(number) not in (int, float) or not math.isfinite(number) or not low <= number <= high:
            raise ValueError('Invalid chroma ' + name)
    return dict(value)


def prepare(request):
    if not isinstance(request, dict):
        raise ValueError('Invalid video request')
    source = source_path(request['source'])
    cancel = Path(request['cancel'])
    raster.check_cancel(cancel)
    identity = raster.sha(source)
    if identity != request['source_sha256']:
        raise ValueError('Video changed since review')
    output = Path(request['output']).resolve()
    if output.exists():
        raise ValueError('Video preparation needs a fresh output directory')
    output.mkdir(parents=True)
    try:
        info = inspect(source, request['ffmpeg'], output, cancel)
        num = raster.number(request['fps_num'], 'project numerator', 1, 120000)
        den = raster.number(request['fps_den'], 'project denominator', 1, 1001)
        rate = Fraction(num, den)
        if rate > 120:
            raise ValueError('Project frame rate exceeds120')
        count = math.ceil(Fraction(*info['source_duration']) * rate)
        remaining = raster.number(request['available_frames'], 'remaining frames', 1, 240)
        if not 1 <= count <= remaining:
            raise ValueError('Video exceeds remaining scene frames; shorten it externally or extend the scene')
        maximum = raster.number(request['max_cels'], 'available drawings', 1, 32)
        width = raster.number(request.get('width', 1920), 'output width', 1, 1920)
        height = raster.number(request.get('height', 1080), 'output height', 1, 1080)
        chroma = key_settings(request['chroma'])
        w, h, x, y = raster.fit(info['width'], info['height'], width, height)
        images = output / 'images'
        images.mkdir()
        raster.write_json(output / 'progress.json', {'stage': 'decode-video'})
        # VP8/VP9's native decoder can discard WebM alpha. Select libvpx explicitly.
        decoder = []
        if source.suffix.lower() == '.webm':
            probe = json.loads((output / 'probe.json').read_bytes())['streams'][0]
            if probe.get('codec_name') in ('vp8', 'vp9'):
                decoder = ['-c:v', 'libvpx-vp9' if probe['codec_name'] == 'vp9' else 'libvpx']
        filters = f'setpts=PTS-STARTPTS,fps={num}/{den}:start_time=0:round=up'
        key_filter = None
        if chroma['enabled']:
            # colorkey replaces alpha: multiply its matte by the original alpha
            # before scaling so translucent source artwork remains translucent.
            key_filter = (f"[0:v:0]{filters},format=rgba,split=2[original][keyinput];"
                          f"[original]alphaextract[originalalpha];"
                          f"[keyinput]colorkey=0x{chroma['color']}:{chroma['similarity']}:{chroma['blend']},split=2[color][matte];"
                          "[matte]alphaextract[keyalpha];"
                          "[originalalpha][keyalpha]blend=all_mode=multiply[alpha];"
                          "[color][alpha]alphamerge,")
            filters = "despill=type=" + ('green' if chroma['color']=='00ff00' else 'blue') + ":mix=0.5:expand=0:brightness=0:alpha=0"
        filters += f',format=gbrapf32le,premultiply=inplace=1:planes=7,scale={w}:{h}:flags=lanczos,unpremultiply=inplace=1:planes=7,format=rgba,pad={width}:{height}:{x}:{y}:color=black@0,setsar=1,tpad=stop_mode=clone:stop_duration=1'
        graph = (['-filter_complex_threads', '1', '-filter_complex', key_filter + filters + '[out]', '-map', '[out]']
                 if key_filter else ['-map', '0:v:0', '-filter_threads', '1', '-vf', filters])
        args = [str(request['ffmpeg']), '-nostdin', '-hide_banner', '-v', 'error', '-xerror', '-n',
                '-max_alloc', '268435456', '-protocol_whitelist', 'file', '-format_whitelist', DEMUXERS,
                *decoder, '-noautorotate', '-i', str(source), *graph, '-an', '-sn', '-dn',
                '-map_metadata', '-1', '-frames:v', str(count),
                '-c:v', 'png', '-threads', '1', str(images / 'frame-%04d.png')]
        run(args, output, cancel, frames=images)
        files = sorted(images.glob('frame-*.png'))
        if len(files) != count or sum(p.stat().st_size for p in files) > raster.MAX_NORMALIZED_BYTES:
            raise ValueError('Video did not decode the complete bounded range')
        holds = []
        for i, path in enumerate(files):
            raster.check_cancel(cancel)
            if path.name != f'frame-{i+1:04d}.png' or raster.png(path) != (width, height, 8, 6):
                raise ValueError('Video produced an invalid picture sequence')
            digest = raster.sha(path)
            target = images / (digest + '.png')
            if target.exists():
                path.unlink()
            else:
                path.rename(target)
            if holds and holds[-1]['sha256'] == digest:
                holds[-1]['duration'] += 1
            else:
                holds.append(dict(start=i, duration=1, path='images/' + target.name,
                                  sha256=digest, bytes=target.stat().st_size))
            if len(holds) > maximum:
                raise ValueError('Video exceeds available editable drawing holds; no frames were omitted')
        raster.check_cancel(cancel)
        if raster.sha(source) != identity:
            raise ValueError('Video changed during preparation')
        packet = dict(format='studio_raster_clip_2', source=dict(path=str(source), sha256=identity, kind='video',
                      width=info['width'], height=info['height'], source_rate=info['source_rate'],
                      source_duration=info['source_duration'], chroma=chroma), width=width, height=height,
                      fps_num=num, fps_den=den, duration_frames=count,
                      fit=dict(width=w, height=h, x=x, y=y), holds=holds, native_audio_imported=False)
        raster.write_json(output / 'clip.json', packet)
        raster.write_json(output / 'progress.json', {'stage': 'ready', 'holds': len(holds)})
        return packet
    except Exception as error:
        raster.write_json(output / 'progress.json', {'stage': 'cancelled' if isinstance(error, raster.Cancelled) else 'error', 'error': str(error)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', nargs='?')
    parser.add_argument('--inspect')
    parser.add_argument('--ffmpeg')
    parser.add_argument('--result')
    parser.add_argument('--cancel-file')
    args = parser.parse_args()
    response = None
    try:
        if args.inspect:
            response = raster.response_path(args.result)
            if response is None:
                raise ValueError('Inspection needs a fresh result path')
            result = dict(ok=True, inventory=inspect(args.inspect, args.ffmpeg, response.parent, Path(args.cancel_file)))
        else:
            request_file = Path(args.request)
            if request_file.stat().st_size > 1024**2:
                raise ValueError('Excessive video request')
            request = json.loads(request_file.read_bytes())
            candidate = raster.response_path(request.get('result'))
            if candidate != Path(request['output']).resolve().parent / 'result.json':
                raise ValueError('Result must stay in its owned job directory')
            response = candidate
            prepare(request)
            clip = Path(request['output']) / 'clip.json'
            result = dict(ok=True, clip=str(clip), sha256=raster.sha(clip))
        raster.write_json(response, result)
        return 0
    except Exception as error:
        if response:
            raster.write_json(response, dict(ok=False, error=str(error)))
        return 2 if isinstance(error, raster.Cancelled) else 1


if __name__ == '__main__':
    raise SystemExit(main())

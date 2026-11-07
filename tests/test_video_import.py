"""Procedural media only; exercise the real installed FFmpeg without native art."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import prepare_video as video
import drawing_origin as origin

FFMPEG = os.environ.get('HYBRID_FFMPEG') or shutil.which('ffmpeg')
PROCESS_FLAGS = dict(creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
CHROMA = dict(enabled=False, color='00ff00', similarity=.1, blend=.05)


def fixture(path, rate='2', alpha=False):
    frames = []
    for color in [(255, 0, 0, 128 if alpha else 255), (0, 0, 255, 255)]:
        pixels = bytearray(bytes((0, 255, 0, 0 if alpha else 255)) * (64 * 36))
        for y in range(10, 26):
            for x in range(20, 44):
                at = (y * 64 + x) * 4
                pixels[at:at+4] = bytes(color)
        frames.append(pixels)
    subprocess.run([FFMPEG, '-v', 'error', '-n', '-f', 'rawvideo', '-pixel_format', 'rgba',
                    '-video_size', '64x36', '-framerate', rate, '-i', '-', '-an', '-c:v', 'qtrle',
                    '-threads', '1', str(path)], input=b''.join(frames), check=True, **PROCESS_FLAGS)
    return path


@unittest.skipUnless(FFMPEG and Path(FFMPEG).with_name('ffprobe.exe' if os.name=='nt' else 'ffprobe').exists(), 'installed FFmpeg/FFprobe required')
class VideoImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = fixture(self.root / 'source.mov')
        self.identity = video.raster.sha(self.source)
        self.request = dict(source=str(self.source), source_sha256=self.identity,
                            output=str(self.root/'prepared'), cancel=str(self.root/'cancel'),
                            ffmpeg=FFMPEG, width=64, height=36, fps_num=4, fps_den=1,
                            available_frames=240, max_cels=32, chroma=copy.deepcopy(CHROMA))

    def pixels(self, packet, index):
        row = next(h for h in packet['holds'] if h['start'] <= index < h['start'] + h['duration'])
        return subprocess.check_output([FFMPEG, '-v', 'error', '-i', str(Path(self.request['output'])/row['path']),
                                        '-f', 'rawvideo', '-pix_fmt', 'rgba', '-threads', '1', '-'], **PROCESS_FLAGS)

    def long_source(self, count):
        path=self.root/'long.mov'
        pixels=b''.join(bytes((i%256,i//256,120,255))*(64*36) for i in range(count))
        subprocess.run([FFMPEG,'-v','error','-n','-f','rawvideo','-pixel_format','rgba','-video_size','64x36','-framerate','24','-i','-','-an','-c:v','qtrle','-threads','1',str(path)],input=pixels,check=True,**PROCESS_FLAGS)
        self.request.update(source=str(path),source_sha256=video.raster.sha(path),fps_num=24,available_frames=500,max_cels=400)
        return path

    def test_four_hundred_unique_video_drawings_extended_range(self):
        source=self.long_source(400);before=video.raster.sha(source)
        packet=video.prepare(self.request)
        self.assertEqual(packet['duration_frames'],400)
        self.assertEqual(len(packet['holds']),400)
        self.assertEqual([(h['start'],h['duration']) for h in packet['holds']],[(i,1) for i in range(400)])
        self.assertEqual(len({h['sha256'] for h in packet['holds']}),400)
        self.assertEqual(video.raster.sha(source),before)

    def test_four_hundred_frame_limit_refuses_without_truncation(self):
        self.long_source(401)
        with self.assertRaisesRegex(ValueError,'400'):video.prepare(self.request)
        self.assertFalse((Path(self.request['output'])/'clip.json').exists())

    def test_complete_timing_and_deduplication(self):
        packet = video.prepare(self.request)
        self.assertEqual(packet['duration_frames'], 4)
        self.assertEqual([(h['start'], h['duration']) for h in packet['holds']], [(0, 2), (2, 2)])
        center = (18*64+32)*4
        self.assertEqual(self.pixels(packet, 0)[center:center+4], bytes((255,0,0,255)))
        self.assertEqual(self.pixels(packet, 2)[center:center+4], bytes((0,0,255,255)))
        self.assertEqual(self.identity, video.raster.sha(self.source))
        self.assertFalse(packet['native_audio_imported'])

    def test_original_alpha_and_keyed_alpha(self):
        self.source.unlink();fixture(self.source, alpha=True)
        self.request['source_sha256'] = video.raster.sha(self.source)
        packet = video.prepare(self.request)
        pixels = self.pixels(packet, 0)
        self.assertEqual(pixels[3], 0)
        self.assertAlmostEqual(pixels[(18*64+32)*4+3], 128, delta=1)
        self.request['output'] = str(self.root/'keyed')
        self.request['chroma']['enabled'] = True
        packet = video.prepare(self.request)
        pixels = self.pixels(packet, 0)
        self.assertEqual(pixels[3], 0)
        # Keying must not replace an existing semi-transparent foreground alpha.
        self.assertAlmostEqual(pixels[(18*64+32)*4+3], 128, delta=1)

    def test_webm_alpha_decoder_preserves_transparency(self):
        original=fixture(self.root/'alpha.mov',alpha=True)
        webm=self.root/'alpha.webm'
        subprocess.run([FFMPEG,'-v','error','-n','-i',str(original),'-c:v','libvpx-vp9','-lossless','1','-pix_fmt','yuva420p','-threads','1',str(webm)],check=True,**PROCESS_FLAGS)
        self.request.update(source=str(webm),source_sha256=video.raster.sha(webm))
        packet=video.prepare(self.request);pixels=self.pixels(packet,0)
        self.assertEqual(pixels[3],0)
        self.assertAlmostEqual(pixels[(18*64+32)*4+3],128,delta=1)

    def test_green_key_and_letterbox(self):
        self.request.update(width=64, height=64)
        self.request['chroma']['enabled'] = True
        packet = video.prepare(self.request)
        pixels = self.pixels(packet, 0)
        self.assertEqual(pixels[3], 0)
        self.assertEqual(pixels[(32*64+2)*4+3], 0)
        self.assertEqual(pixels[(32*64+32)*4:(32*64+32)*4+4], bytes((255,0,0,255)))
        self.assertEqual(packet['fit'], dict(width=64,height=36,x=0,y=14))

    def test_fractional_duration_has_no_phantom_frame(self):
        self.source.unlink();fixture(self.source, rate='24000/1001')
        self.request.update(source_sha256=video.raster.sha(self.source), fps_num=24000, fps_den=1001)
        packet = video.prepare(self.request)
        self.assertEqual(packet['duration_frames'], 2)
        self.assertEqual(packet['source']['source_duration'], [1001,12000])

    def test_longer_ignored_audio_does_not_extend_video_holds(self):
        source=self.root/'long-audio.mkv'
        subprocess.run([FFMPEG,'-v','error','-n','-i',str(self.source),'-f','lavfi','-i',
                        'anullsrc=r=48000:cl=mono','-t','2','-map','0:v:0','-map','1:a:0',
                        '-c:v','ffv1','-c:a','pcm_s16le','-threads','1',str(source)],check=True,**PROCESS_FLAGS)
        self.request.update(source=str(source),source_sha256=video.raster.sha(source))
        packet=video.prepare(self.request)
        self.assertEqual(packet['duration_frames'],4)
        self.assertEqual(packet['source']['source_duration'],[1,1])

    def test_exceeding_range_or_hold_budget_refuses_whole_import(self):
        for key, value in [('available_frames',3), ('max_cels',1)]:
            with self.subTest(key=key):
                request = {**self.request, key:value, 'output':str(self.root/key)}
                with self.assertRaises(ValueError):video.prepare(request)
                self.assertFalse((Path(request['output'])/'clip.json').exists())

    def test_source_changed_after_review_refuses(self):
        self.source.write_bytes(self.source.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError, 'changed since review'):video.prepare(self.request)
        self.assertFalse(Path(self.request['output']).exists())

    def test_cancel_does_not_create_output(self):
        Path(self.request['cancel']).touch()
        with self.assertRaises(video.raster.Cancelled):video.prepare(self.request)
        self.assertFalse(Path(self.request['output']).exists())

    def test_reused_output_refuses_without_overwriting(self):
        folder = Path(self.request['output']);folder.mkdir();marker=folder/'keep';marker.write_text('original')
        with self.assertRaisesRegex(ValueError, 'fresh output'):video.prepare(self.request)
        self.assertEqual(marker.read_text(), 'original')

    def test_bad_chroma_and_nonlocal_sources_refuse(self):
        for change in [dict(enabled=1),dict(color='ff0000'),dict(blend=float('nan')),dict(similarity=0),dict(extra=True)]:
            with self.subTest(change=change),self.assertRaises(ValueError):video.key_settings({**CHROMA,**change})
        for path in ['https://host/source.mp4', '//host/source.mov', str(self.root/'file.m3u8')]:
            with self.subTest(path=path),self.assertRaises((ValueError,FileNotFoundError)):video.source_path(path)


if __name__ == '__main__':unittest.main()

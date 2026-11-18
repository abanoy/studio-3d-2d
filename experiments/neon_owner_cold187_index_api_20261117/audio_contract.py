"""Independent packed-WAV reference; never extracts or publishes media."""
from io import BytesIO
from pathlib import PurePosixPath
import hashlib
import wave
import zipfile


def audio_rows(audio):
    if not audio:
        return []
    if 'clips' in audio or 'format' in audio:
        if set(audio) != {'format', 'clips'} or audio['format'] not in {
                'studio_audio_2', 'studio_audio_3', 'studio_audio_4', 'studio_audio_5'}:
            raise ValueError('Unsupported portable audio collection')
        return audio['clips']
    return [audio]


def audio_expectations(package, audio):
    rows = audio_rows(audio)
    if not isinstance(rows, list) or len(rows) > 16:
        raise ValueError('Bounded audio reference required')
    result = []
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        for row in rows:
            name = row['path']
            parts = PurePosixPath(name)
            if parts.is_absolute() or '..' in parts.parts or name != 'assets/' + row['sha256'] + '.wav':
                raise ValueError('Noncanonical managed audio path')
            if names.count(name) != 1 or archive.getinfo(name).file_size > 32 * 1024 * 1024:
                raise ValueError('Missing/duplicate/oversized packed WAV')
            raw = archive.read(name)
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Packed WAV identity mismatch')
            with wave.open(BytesIO(raw), 'rb') as source:
                channels, rate, frames = source.getnchannels(), source.getframerate(), source.getnframes()
                if source.getcomptype() != 'NONE' or source.getsampwidth() != 2 or channels not in (1, 2):
                    raise ValueError('PCM16 mono/stereo reference required')
                if not 8000 <= rate <= 96000 or not 0 < frames <= 60 * rate:
                    raise ValueError('Bounded WAV sample domain required')
                pcm = source.readframes(frames)
            if len(pcm) != frames * channels * 2:
                raise ValueError('Incomplete PCM reference')
            result.append({'id': row['id'], 'path': name, 'sha256': row['sha256'],
                           'source_name': row['source_name'], 'channels': channels, 'rate': rate,
                           'frames': frames, 'pcm_bytes': len(pcm),
                           'pcm_sha256': hashlib.sha256(pcm).hexdigest()})
    if len({row['id'] for row in result}) != len(result):
        raise ValueError('Duplicate audio identity')
    return result

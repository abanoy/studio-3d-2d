"""Normalize a bounded local MP3/Ogg into Studio's existing PCM audio contract."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import wave

MAX_INPUT=32*1024*1024
MAX_SECONDS=60
RATE=48000

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def prepare(request):
    source=Path(request['source']).resolve(strict=True)
    demuxer={'.mp3':'mp3','.ogg':'ogg'}.get(source.suffix.lower())
    if not demuxer:raise ValueError('Choose a WAV, MP3 or Ogg audio file.')
    if not source.is_file() or not 1<=source.stat().st_size<=MAX_INPUT:raise ValueError('Audio input must be a file no larger than32MiB.')
    output=Path(request['output']).resolve();cancel=Path(request['cancel'])
    temporary=output.with_suffix('.partial.wav');log=output.with_suffix('.decode.log')
    if output==source or output.exists() or temporary.exists():raise ValueError('Audio preparation needs a new output file.')
    if cancel.exists():raise RuntimeError('Audio import cancelled.')
    original=digest(source)
    args=[request['ffmpeg'],'-nostdin','-hide_banner','-v','error','-xerror','-n',
          '-protocol_whitelist','file','-f',demuxer,'-i',str(source),
          '-map','0:a:0','-vn','-sn','-dn','-t',str(MAX_SECONDS+1),
          '-af','aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=mono|stereo','-c:a','pcm_s16le','-map_metadata','-1',
          '-rf64','never','-f','wav',str(temporary)]
    try:
        with log.open('wb') as stream:
            try:process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=stream,stderr=stream,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            except FileNotFoundError:raise RuntimeError('FFmpeg is unavailable. Set the movie encoder path in Advanced, then add the sound again.') from None
            started=time.monotonic()
            try:
                while process.poll() is None:
                    if cancel.exists():raise RuntimeError('Audio import cancelled.')
                    if time.monotonic()-started>45:raise RuntimeError('Audio preparation exceeded45seconds. Try a shorter sound.')
                    if log.stat().st_size>2*1024*1024:raise RuntimeError('Audio decoder reported too many errors. Try another audio file.')
                    time.sleep(.025)
                if process.returncode:raise RuntimeError('Cannot decode this audio file. It may be damaged or unsupported by the installed FFmpeg. Details: '+str(log))
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=3)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
        if cancel.exists():raise RuntimeError('Audio import cancelled.')
        if digest(source)!=original:raise RuntimeError('The audio source changed during preparation. Add it again.')
        if not temporary.is_file() or temporary.stat().st_size>12*1024*1024:raise ValueError('Decoded audio exceeds its preparation budget.')
        with wave.open(str(temporary),'rb') as decoded:
            frames=decoded.getnframes();channels=decoded.getnchannels()
            if not 0<frames<=RATE*MAX_SECONDS:raise ValueError('Sound clips currently support up to60seconds. Choose or trim a shorter source; no truncated clip was added.')
            if channels not in (1,2) or (decoded.getsampwidth(),decoded.getframerate(),decoded.getcomptype())!=(2,RATE,'NONE') or len(decoded.readframes(frames))!=frames*channels*2:
                raise ValueError('Audio conversion returned incomplete PCM samples.')
        temporary.replace(output)
        return {'ok':True,'path':str(output),'sha256':digest(output),'source_sha256':original,'source_name':source.name,'frames':frames,'rate':RATE,'channels':channels}
    finally:
        if temporary.exists():temporary.unlink()

def main():
    request=json.loads(Path(sys.argv[1]).read_bytes());result_path=Path(request['result'])
    try:result=prepare(request)
    except (OSError,ValueError,RuntimeError,KeyError,wave.Error) as error:result={'ok':False,'error':str(error)}
    temporary=result_path.with_suffix('.tmp');temporary.write_text(json.dumps(result),encoding='utf-8');temporary.replace(result_path)
    return 0 if result['ok'] else 1

if __name__=='__main__':sys.exit(main())

"""Bounded native canvas contract shared by project container validation."""
PROFILES={'1080p':(1920,1080),'720p':(1280,720),'540p':(960,540)}
def profile(video):
    if not isinstance(video,dict):return ''
    width,height=video.get('width'),video.get('height')
    if type(width) not in (int,float) or type(height) not in (int,float):return ''
    return next((key for key,size in PROFILES.items() if (width,height)==size),'')
def error(video):return '' if profile(video) else 'Choose a supported native canvas: 1920 x 1080, 1280 x 720 or 960 x 540.'

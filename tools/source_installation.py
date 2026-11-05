"""Read-only installed Source context. SFM content does not require GMod."""
from pathlib import Path
from source_content import discover, child, value, kv_read
from source_paths import require_gmod, DEFAULT_GMOD, DEFAULT_WORKSHOP


def sfm_installation(root):
    root = Path(root).resolve()
    info = child(kv_read(root / 'game/usermod/gameinfo.txt'), 'GameInfo')
    filesystem = child(info, 'FileSystem')
    if value(filesystem, 'SteamAppId') != '1840' or not (root / 'game/sfm.exe').is_file():
        raise ValueError('Source Filmmaker installation is incomplete. Verify it in Steam: ' + str(root))
    return root


def source_is_sfm(source, discovery):
    source = Path(source).resolve()
    return any(p['present'] and p['origin'].startswith('sfm') and
               (source == Path(p['path']) or p['kind'] == 'folder' and source.is_relative_to(Path(p['path'])))
               for p in discovery['providers'])


def installed_context(gmod=DEFAULT_GMOD, workshop=DEFAULT_WORKSHOP, extra=(), source=None):
    """Allow browsing with either installed host; native GMod assets still require GMod.

    Without GMod, native imports must originate in a recognized installed SFM
    provider (including its Workshop locations). Extra directories remain useful
    as dependencies, but merely calling an arbitrary folder SFM cannot admit it.
    No executable is run; presence/configuration checks are not Steam ownership DRM.
    """
    discovery = discover(gmod, workshop, extra)
    gmod_error = None
    try:
        game = require_gmod(gmod)
    except ValueError as error:
        game = None; gmod_error = error
    sfm = []
    for row in discovery['games']:
        if row['appid'] != '1840': continue
        for location in row['locations']:
            try: sfm.append(sfm_installation(location))
            except ValueError as error: discovery['warnings'].append(str(error))
    if game is None:
        if not sfm:
            raise ValueError(str(gmod_error) + ' Alternatively install Source Filmmaker to use its installed content.')
        # Missing/broken GMod content is not a dependency fallback for SFM-only use.
        valid_sfm = {str(p) for p in sfm}
        discovery['providers'] = [p for p in discovery['providers'] if
                                  p['origin'] == 'sfm-workshop' or
                                  p['origin'].startswith('sfm') and p.get('installation') in valid_sfm or
                                  p['origin'] in {'steam', 'manual'}]
        if source is not None and not source_is_sfm(source, discovery):
            raise ValueError(str(gmod_error) + ' Without GMod, choose content from an installed SFM location or its Workshop folder.')
        discovery['warnings'].append('GMod is unavailable. Browsing installed SFM content; GMod imports still require an installed GMod copy.')
    return {'discovery': discovery, 'gmod_installation': str(game) if game else '',
            'sfm_installations': [str(p) for p in sfm],
            'source_profile': 'sfm' if source is not None and source_is_sfm(source, discovery) else 'gmod'}

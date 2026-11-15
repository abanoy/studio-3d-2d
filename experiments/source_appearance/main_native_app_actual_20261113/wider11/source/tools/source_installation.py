"""Read-only installed discovery and standalone Source conversion context."""
from pathlib import Path
from asset_audit import AssetError
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
    """Allow installed browsing with either host; GMod browsing still requires GMod.

    This installed browsing context recognizes validated SFM providers without
    GMod. Arbitrary supplied files use conversion_context instead; their
    conversion does not require an installed game.
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


def conversion_context(gmod=DEFAULT_GMOD, workshop=DEFAULT_WORKSHOP, extra=(), source=None):
    """Resolve a supplied package independently of optional installed game content.

    Installed browsing keeps its host checks. A directly selected file can be
    read without a game, even if its folder resembles a former installation.
    Optional installed providers are mounted only when their host is validated.
    """
    if source is None:
        return installed_context(gmod, workshop, extra)
    source = Path(source).resolve(strict=True)
    try:
        discovery = discover(gmod, workshop, extra)
    except (AssetError, OSError, ValueError) as error:
        # Broken optional game configuration must not reject an unrelated asset.
        providers = []
        for item in extra:
            path = Path(item).resolve()
            providers.append({'path': str(path), 'label': path.name, 'origin': 'manual',
                              'present': path.exists(), 'enabled': path.exists(),
                              'kind': 'folder' if path.is_dir() else path.suffix.lower()[1:]})
        discovery = {'providers': providers, 'games': [], 'libraries': [],
                     'warnings': ['Optional installed-content discovery failed: ' + str(error)],
                     'note': 'Using selected asset and explicit dependencies only.'}
    try:
        game = require_gmod(gmod)
    except ValueError:
        game = None
    sfm = []
    for row in discovery['games']:
        if row['appid'] != '1840':
            continue
        for location in row['locations']:
            try:
                sfm.append(sfm_installation(location))
            except ValueError:
                pass
    valid_sfm = {str(path) for path in sfm}
    game_origins = {'game', 'addon', 'workshop', 'download', 'gamemode', 'mount.cfg'}
    discovery['providers'] = [provider for provider in discovery['providers']
                             if (provider['origin'] not in game_origins or game is not None)
                             and (not provider['origin'].startswith('sfm') or
                                  provider.get('installation') in valid_sfm or
                                  provider['origin'] == 'sfm-workshop' and bool(sfm))]
    return {'discovery': discovery, 'gmod_installation': str(game) if game else '',
            'sfm_installations': [str(path) for path in sfm],
            'source_profile': ('sfm' if source_is_sfm(source, discovery) else
                               'gmod' if game and (source.is_relative_to(game) or source.is_relative_to(Path(workshop).resolve()))
                               else 'standalone')}

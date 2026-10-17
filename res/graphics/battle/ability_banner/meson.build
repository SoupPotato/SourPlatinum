ability_banner_nclr = custom_target(
  'ability_banner.NCLR',
  output: 'banner.NCLR',
  input: files('banner.png'),
  command: [
    nitrogfx_exe, '@INPUT@', '@OUTPUT@',
    '-bitdepth', '4',
    '-nopad',
    '-invertsize',
    '-pcmp',
  ],
)

battle_sprites += [
  copy_gen.process(
    ability_banner_nclr,
    preserve_path_from: base_build_directory,
  ),

  ncgr_lz_gen.process(
    files('banner.png'),
    preserve_path_from: base_directory,
    extra_args: [ '-bitdepth', '4', '-clobbersize', '-mappingtype', '64' ],
  ),

  ncer_lz_gen.process(
    files('banner_cell.json'),
    preserve_path_from: base_directory,
  ),
]

# The art itself is copied into the sprite at run time, with the text drawn over it
ability_banner_embed = custom_target(
  'banner.4bpp.h',
  output: [
    'banner.4bpp',
    'banner.4bpp.h',
  ],
  input: files('banner.png'),
  command: [ nitrogfx_exe, '@INPUT@', '@OUTPUT0@', '-embed', 'sAbilityBannerBitmap' ],
)

embed_headers += ability_banner_embed[1]

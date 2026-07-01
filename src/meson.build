pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'pardus_z_kutuphane'
gnome = import('gnome')

# Collect every .blp file under src/ui automatically so new ones don't need to
# be listed here by hand.
blueprint_files = run_command(
  find_program('python3'),
  '-c',
  '''
import glob, os
subdir = os.path.join(os.environ['MESON_SOURCE_ROOT'], os.environ['MESON_SUBDIR'])
for f in sorted(glob.glob(os.path.join(subdir, 'ui', '*.blp'))):
    print(os.path.relpath(f, subdir))
''',
  check: true,
).stdout().strip().split('\n')

blueprints = custom_target('blueprints',
  input: files(blueprint_files),
  output: '.',
  command: [
    find_program('blueprint-compiler'),
    'batch-compile',
    '@OUTPUT@',
    meson.current_source_dir() / 'ui',
    '@INPUT@',
  ],
)

gnome.compile_resources('pardus-z-kutuphane',
  'pardus-z-kutuphane.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'pardus-z-kutuphane.in',
  output: 'pardus-z-kutuphane',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

pardus_z_kutuphane_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

install_data(pardus_z_kutuphane_sources, install_dir: moduledir)

# Collect every .py file under src/widgets automatically so new widget modules
# don't need to be listed here by hand.
widgets_sources = run_command(
  find_program('python3'),
  '-c',
  '''
import glob, os
subdir = os.path.join(os.environ['MESON_SOURCE_ROOT'], os.environ['MESON_SUBDIR'])
for f in sorted(glob.glob(os.path.join(subdir, 'widgets', '*.py'))):
    print(os.path.relpath(f, subdir))
''',
  check: true,
).stdout().strip().split('\n')

install_data(widgets_sources, install_dir: moduledir / 'widgets')

backend_sources = run_command(
  find_program('python3'),
  '-c',
  '''
import glob, os
subdir = os.path.join(os.environ['MESON_SOURCE_ROOT'], os.environ['MESON_SUBDIR'])
for f in sorted(glob.glob(os.path.join(subdir, 'backend', '*.py'))):
    print(os.path.relpath(f, subdir))
''',
  check: true,
).stdout().strip().split('\n')

install_data(backend_sources, install_dir: moduledir / 'backend')

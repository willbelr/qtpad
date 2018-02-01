#!/usr/bin/python3
import os
import setuptools
import setuptools.command.build_py
here = os.path.abspath(os.path.dirname(__file__))


class CreateDesktopFile(setuptools.command.build_py.build_py):
  def run(self):
    with open(os.path.join(here + "/qtpad.desktop"), 'w') as f:
        f.write("[Desktop Entry]\n")
        f.write("Name=qtpad\n")
        f.write("GenericName=Sticky Notes\n")
        f.write("Terminal=false\n")
        f.write("Type=Application\n")
        f.write("Categories=Utility;\n")
        f.write("Icon=qtpad\n")
        f.write("Exec=qtpad\n")
    setuptools.command.build_py.build_py.run(self)


# Workaround in case PyQt5 was installed without pip
install_requires=['requests']
try:
    from PyQt5 import uic
    uic.compileUiDir('qtpad')
except:
    install_requires.append("pyqt5")

setuptools.setup(
    name='qtpad',
    version='0.0.3',
    description='Modern and customizable sticky note application',
    keywords='sticky note text editor note-taking',
    author='William Belanger',
    url='https://github.com/willbelr/qtpad',

    # From https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    cmdclass={'build_py': CreateDesktopFile},
    data_files=[
        ('share/icons/hicolor/scalable/apps', ['qtpad.svg']),
        ('share/applications', ['qtpad.desktop'])
    ],
    package_data={'': ['icons/*.svg']},
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'qtpad=qtpad:main',
        ],
    },
)

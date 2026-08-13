import os
from setuptools import setup, find_packages

working_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(working_dir, 'README.md'), encoding="utf-8") as f:
    long_description = f.read()

RELEASE = '0.0.1'
DESCRIPTION = ('GRINQ — GNSS Rinex INgestion & Quality control is a toolkit for '
               'retrieving rinex data from data holdings and make quality statistics')

setup(
    name='grinq',
    version=RELEASE,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PJarrin/grinq",
    author='Paul Jarrin (Geoazur, IRD, CNRS, France)',
    author_email='paul.jarrin@geoazur.unice.fr',
    packages=find_packages(),
    license='MIT',
    install_requires=['numpy<=1.26.4','matplotlib<=3.8.0','earthscope-sdk','argparse==1.4.0','hatanaka==2.8.1',
            'path==17.1.1','unlzw==0.1.1','unlzw3==0.2.3','ansicolors==1.1.8','wget==3.2',
            'tqdm==4.59.0','scipy<=1.16.1','lxml<=6.0.2'],
    keywords=['Geodesy', 'GNSS', 'rinex','Quality control'],
    zip_safe=False,
    package_data={'grinq': ['info/*.dat']},
    scripts=['grinq/scripts/grinq_get_rinex.py',
             'grinq/scripts/grinq_ftp_mirror_sync.py',
             'grinq/scripts/grinq_make_qc.py'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License'
    ]
)

from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
      name='gotmgui',
      version='0.1.2',
      description=' --- update - ',
#      long_description=readme(),
      url='http://github.com/BoldingBruggeman/gotmgui',
      author='Jorn Bruggeman',
      author_email='jorn@bolding-bruggeman.com',
      license='GPL',
      install_requires=['xmlplot>=0.9.19'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Programming Language :: Python',
      ],
      entry_points={
          'console_scripts': [
                'gotmgui=gotmgui.gotmgui:main',
          ]
      },
      packages=['gotmgui', 'gotmgui/core', 'gotmgui/util'],
      package_data={
                    'gotmgui': [
                                'icons/*', 
                                'reporttemplates/*/*',
                                'schemas/*/*',
                                'gotmgui.ico',
                                'icon.png',
                                'logo.png',
                                '*.so', '*.dll', '*.dylib',
                               ],
                   }, 
#      include_package_data=True,
      zip_safe=False)

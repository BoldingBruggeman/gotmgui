from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='gotmgui',
      version='0.1',
      description=' --- update - ',
      long_description=readme(),
      url='http://github.com/BoldingBruggeman/gotmgui',
      author='Jorn Bruggeman',
      author_email='jorn@bolding-bruggeman.com',
      license='GPL',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: Numerical Models :: Configuration Tools',
          'License :: OSI Approved :: GPL License',
          'Programming Language :: Python :: 2.7',
      ],
      entry_points={
          'console_scripts': [
                'gotmgui=gotmgui.gotmgui:main',
#                'nml2xml=editscenario.nml2xml:main',
          ]
      },
      packages=['gotmgui', 'gotmgui/core', 'gotmgui/pygotm_init', 
                'gotmgui/util'],
      package_data={'gotmgui': ['icons/*', 
                                 'reporttemplates/*/*',
                                 'schemas/*/*',
                               ]}, 
      include_package_data=True,
      zip_safe=False)

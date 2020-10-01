from setuptools import setup, find_packages

try:
    import wheel.bdist_wheel
    class bdist_wheel(wheel.bdist_wheel.bdist_wheel):
        def finalize_options(self):
            wheel.bdist_wheel.bdist_wheel.finalize_options(self)
            self.root_is_pure = False
        def get_tag(self):
            python, abi, plat = wheel.bdist_wheel.bdist_wheel.get_tag(self)
#            python, abi = 'py2.py3', 'none'
            return python, abi, plat
except ImportError:
    bdist_wheel = None


def readme():
    with open('README.md') as f:
        return f.read()

setup(
      name='gotmgui',
      version='0.1.1',
      description=' --- update - ',
#      long_description=readme(),
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
      cmdclass={'bdist_wheel': bdist_wheel},
#      include_package_data=True,
      zip_safe=False)

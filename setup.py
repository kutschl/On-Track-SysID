# from setuptools import setup, find_packages

# setup(

#     name='on_track_sys_"id',  # The name of your package
#     version='0.1.0',         # Version of the package
#     packages=find_packages('src'),  # Find all packages under 'src'
#     package_dir={'': 'src'},        # Specify the root package directory
# )

from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'on_track_sys_id'

setup(
    name=package_name,
    version='0.1.0',
    packages=[
        package_name,
        f'{package_name}.helpers',
    ],
    # packages=find_packages('src', exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.xml'))),
        (os.path.join('share', package_name, 'params'), glob(os.path.join('params', '*.yaml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lukas Kutsch',
    maintainer_email='lkutsch@uni-bonn.de',
    description='On-Track System Identification',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'on_track_sys_id_node = on_track_sys_id.on_track_sys_id_node:main'
        ],
    },
)

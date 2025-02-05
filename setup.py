__version__ = '0.0.1'
from setuptools import setup, find_packages

setup(
    name='db-inspector',  # 包名
    version='0.1',    # 包版本
    packages=find_packages(),  # 自动找到所有包
    install_requires=[  # 项目所依赖的库
        'click',
        'psycopg2',
        'mysql-connector-python',
        'toml',
    ],
    entry_points={  # 定义命令行脚本
        'console_scripts': [
            'db-inspector=db-inspector.script:main',  # 指定命令行工具名和主函数
        ],
    },
    include_package_data=True,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)

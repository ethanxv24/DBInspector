__version__ = '0.0.1'
from setuptools import setup, find_packages

setup(
    name='dbinspector-tool',  # 包名
    version='0.0.1',    # 包版本
    packages=find_packages(),  # 自动找到所有包
    license='BSD License',
    description='A database inspector tool',  # 简要描述
    install_requires=[  # 项目所依赖的库
        'click',
        'psycopg2',
        'mysql-connector-python',
        'toml',
    ],
    entry_points={  # 定义命令行脚本
        'console_scripts': [
            'db_inspector=db_inspector.script:main',  # 指定命令行工具名和主函数
        ],
    },
    include_package_data=True,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ethanxv24/DBInspector',  # 项目地址
    author='Ethan Xv',  # 作者
    author_email='kasetacor@gmail.com',  # 作者邮箱
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.7',
)

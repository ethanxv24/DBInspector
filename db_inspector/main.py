import os

import click

from db_inspector.config.config_loader import load_config_from_file
from db_inspector.pipelines.base import PipelineManager
from db_inspector.pipelines.pg_pipeline import PostgreSQLPipeline
from db_inspector.reports.html_report import SummaryReportGenerator


# 使用 click 解析命令行参数
@click.command()
@click.option('--config', type=click.Path(exists=True, readable=True), required=True, help="Path to the TOML configuration file")
@click.option('--report-format', type=click.Choice(['json', 'html'], case_sensitive=False), default='json', help="Format of the generated report")
@click.option('--output-report-dir',type=click.Path(exists=True, readable=True),default='report', help="Path to the directory where the report will be saved")

def main(config, report_format,output_report_dir):
    # 配置文件路径
    #config_file_path = './config/default_config.toml'

    # 加载配置文件
    config = load_config_from_file(config)

    # 如果配置无效，则退出
    if config is None:
        print("Failed to load configuration. Exiting...")
        return


    # 用于存储所有数据库的检查结果
    db_results = []

    # 配置有效，继续进行后续操作
    for db_config in config['databases']:
        pipe = PipelineManager()
        # 判断数据库类型 用switch case
        if db_config['type'] == 'postgres':
            # 创建 PostgreSQL 管道实例
            pipe = PostgreSQLPipeline(db_name=db_config['name'],db_uri=db_config['uri'], check_names=db_config['checks'], report_format=report_format,report_dir=output_report_dir)
        #TODO: Add support for other database types
        else:
            print(f"Unsupported database type: {db_config['type']}")
            continue


        pipe.parse_db_uri()
        pipe.connect()
        pipe.set_checks()

        # 执行管道并获取结果
        results = pipe.execute()
        db_results.append(results)

        # 生成报告（JSON 格式）
        report = pipe.generate_report(results)
        print(f"Report for {db_config['name']}:\n{report}\n")

        # 关闭数据库连接
        pipe.close()


    # 生成汇总报告
    summary_report_generator = SummaryReportGenerator()
    summary_report = summary_report_generator.generate(db_results,output_file=os.path.join(output_report_dir, 'summary_report.html'))
    print(f"Report for Summary:\n{summary_report}\n")

    print("All checks completed.")


if __name__ == "__main__":
    main()




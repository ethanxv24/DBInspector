from jinja2 import Environment, FileSystemLoader, Template
import os

class HTMLReportGenerator:
    def __init__(self, template_path=None):
        """
        初始化 HTMLReportGenerator
        :param template_path: 可选，HTML 模板文件路径。如果不传入，则使用内嵌模板。
        """
        if template_path and os.path.exists(template_path):
            # 使用指定模板文件
            template_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)
            env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
            self.template = env.get_template(template_file)
        else:
            # 使用内嵌模板
            self.template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>数据库检查报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>数据库检查报告</h1>

    {% for db in databases %}
    <h2>数据库: {{ db.db_name }} (地址: {{ db.db_host }}:{{ db.db_port }})</h2>
    <table>
        <thead>
            <tr>
                <th>检查项</th>
                <th>状态</th>
                <th>信息</th>
            </tr>
        </thead>
        <tbody>
        {% for result in db.check_results %}
            <tr>
                <td>{{ result.check_name }}</td>
                <td>{{ result.status }}</td>
                <td>{{ result.message }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% endfor %}
</body>
</html>
            """, autoescape=True)

    def generate(self, databases, output_file=None):
        """
        根据传入的检查结果生成 HTML 格式报告。
        :param databases: 数据库信息和检查结果的列表，每个元素包括数据库信息和对应的检查结果。
        :param output_file: 可选，若指定则将 HTML 内容写入该文件。
        :return: 生成的 HTML 字符串
        """
        html_content = self.template.render(databases=databases)

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"HTML 报告已写入 {output_file}")
            except Exception as e:
                print(f"写入文件 {output_file} 时发生错误: {e}")

        return html_content

class SummaryReportGenerator:
    def __init__(self, template_path=None):
        if template_path and os.path.exists(template_path):
            template_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)
            env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
            self.template = env.get_template(template_file)
        else:
            # 内嵌汇总报告模板
            self.template = Template("""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>数据库巡检汇总报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>数据库巡检汇总报告</h1>

    <h2>巡检结果概览</h2>
    <table>
        <thead>
            <tr>
                <th>数据库</th>
                <th>状态</th>
                <th>正常状态</th>
                <th>错误状态</th>
                <th>告警状态</th>
                <th>详细报告</th>
            </tr>
        </thead>
        <tbody>
        {% for db in databases %}
            <tr>
                <td>{{ db.db_name }}</td>
                <td>{{ db.status }}</td>
                <td>{{ db.success_count }}</td>
                <td>{{ db.failure_count }}</td>
                <td>{{ db.warning_count }}</td>
                <td><a href="{{ db.report_link }}">查看详细报告</a></td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
</body>
</html>
            """)

    def generate(self, databases, output_file=None):
        html_content = self.template.render(databases=databases)

        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"汇总报告已写入 {output_file}")
            except Exception as e:
                print(f"写入文件 {output_file} 时发生错误: {e}")

        return html_content

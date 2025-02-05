import psycopg2
import json
from abc import ABC, abstractmethod
from jinja2 import Template

# base_pipeline.py
class BasePipeline(ABC):
    def __init__(self, connection_info):
        self.connection_info = connection_info
        self.conn = None
        self.cursor = None

    @abstractmethod
    def get_check_methods(self):
        """Return a list of methods to perform checks."""
        pass

    def connect(self):
        """Establish a connection to the database."""
        self.conn = psycopg2.connect(
            dbname=self.connection_info['dbname'],
            user=self.connection_info['user'],
            password=self.connection_info['password'],
            host=self.connection_info['host'],
            port=self.connection_info['port']
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def disconnect(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def run(self):
        """Run all the checks defined in get_check_methods."""
        self.connect()
        results = {}
        for method in self.get_check_methods():
            results.update(method())
        self.disconnect()
        return results

    def output_report(self, results, output_format="json", output_file=None):
        """Generate a report in the specified format."""
        if output_format == "json":
            report = json.dumps(results, indent=4)
        elif output_format == "html":
            template = Template("""
            <html>
            <head><title>Database Inspection Report</title></head>
            <body>
                <h1>Database Inspection Report</h1>
                <pre>{{ results | tojson(indent=4) }}</pre>
            </body>
            </html>
            """)
            report = template.render(results=results)
        else:
            raise ValueError("Unsupported format")

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
        else:
            print(report)

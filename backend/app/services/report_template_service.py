"""
Decoupled Template Engine
=========================
Separates report templates into modular strategy classes.
Future templates can be added by implementing BaseReportTemplate without modifying ReportService.
"""
from typing import Dict, Any, List
from abc import ABC, abstractmethod
import datetime


class BaseReportTemplate(ABC):
    """
    Abstract base class defining layout structure methods for report templates.
    """

    @property
    @abstractmethod
    def template_id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def parameters(self) -> List[str]:
        pass

    @abstractmethod
    def render(self, title: str, start: str, end: str, kpis: Dict[str, Any], violations: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> str:
        """Renders the text layout for the template."""
        pass


class ExecutiveTemplate(BaseReportTemplate):
    template_id = "executive_report"
    name = "Executive Summary Report"
    description = "High-level summary of total scanned vehicles, flagged violations, and assessed fines."
    supported_formats = ["pdf", "csv", "xlsx", "json"]
    parameters = ["start_date", "end_date"]

    def render(self, title: str, start: str, end: str, kpis: Dict[str, Any], violations: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> str:
        line = "=" * 75
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
{line}
                  EXECUTIVE SUMMARY COMPLIANCE REPORT
{line}
TITLE             : {title}
DATE RANGE        : {start} to {end}
GENERATED AT      : {now_str} UTC
---------------------------------------------------------------------------
Total Violations  : {kpis.get('total_violations', 0)}
Total Fines       : INR {kpis.get('total_fines', 0.0):.2f}
Database Status   : {kpis.get('db_health', 'healthy').upper()}
{line}
"""


class ViolationTemplate(BaseReportTemplate):
    template_id = "violation_report"
    name = "Detailed Violation Audit"
    description = "Detailed list of violation counts categorized by cameras and type classifications."
    supported_formats = ["pdf", "csv", "json"]
    parameters = ["start_date", "end_date", "violation_type"]

    def render(self, title: str, start: str, end: str, kpis: Dict[str, Any], violations: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> str:
        line = "=" * 75
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            line,
            f"                  DETAILED VIOLATION REPORT: {title}",
            line,
            f"RANGE             : {start} to {end}",
            f"GENERATED         : {now_str} UTC",
            "---------------------------------------------------------------------------",
            f"{'Violation Category':<45} | {'Count':<10}",
            "---------------------------------------------------------------------------"
        ]
        for v in violations:
            lines.append(f"{v['name']:<45} | {v['value']:<10}")
        lines.append(line)
        return "\n".join(lines) + "\n"


class AnalyticsTemplate(BaseReportTemplate):
    template_id = "analytics_report"
    name = "Weekly Traffic Analytics Trends"
    description = "Weekly breakdown of traffic flows, vehicle classes, and camera performance averages."
    supported_formats = ["pdf", "xlsx", "json"]
    parameters = ["start_date", "end_date"]

    def render(self, title: str, start: str, end: str, kpis: Dict[str, Any], violations: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> str:
        line = "=" * 75
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            line,
            f"                  TRAFFIC & VEHICLE ANALYTICS: {title}",
            line,
            f"RANGE             : {start} to {end}",
            f"GENERATED         : {now_str} UTC",
            "---------------------------------------------------------------------------",
            f"{'Vehicle Class':<45} | {'Count':<10}",
            "---------------------------------------------------------------------------"
        ]
        for vh in vehicles:
            lines.append(f"{vh['name']:<45} | {vh['value']:<10}")
        lines.append(line)
        return "\n".join(lines) + "\n"


class SystemTemplate(BaseReportTemplate):
    template_id = "system_report"
    name = "AI Model & Hardware Health Report"
    description = "Diagnostics summary of AI camera latency, network connections, and system availability."
    supported_formats = ["pdf", "json"]
    parameters = []

    def render(self, title: str, start: str, end: str, kpis: Dict[str, Any], violations: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> str:
        line = "=" * 75
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
{line}
                  AI ENGINE SYSTEM DIAGNOSTICS REPORT
{line}
TITLE             : {title}
GENERATED         : {now_str} UTC
---------------------------------------------------------------------------
Diagnostics Status: HEALTHY
System Uptime     : {kpis.get('system_uptime', '99.95%')}
Average Conf      : {kpis.get('avg_confidence', 0.88):.2%}
{line}
"""


class ReportTemplateService:
    """
    Registry management class resolving template rendering strategies dynamically.
    """

    def __init__(self):
        self._templates: Dict[str, BaseReportTemplate] = {}
        # Self-register default strategies
        self.register_template(ExecutiveTemplate())
        self.register_template(ViolationTemplate())
        self.register_template(AnalyticsTemplate())
        self.register_template(SystemTemplate())

    def register_template(self, template: BaseReportTemplate) -> None:
        """Allows registering custom external templates dynamically."""
        self._templates[template.template_id] = template

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Lists metadata details for all registered templates."""
        return [
            {
                "id": t.template_id,
                "name": t.name,
                "description": t.description,
                "supported_formats": t.supported_formats,
                "parameters": t.parameters
            }
            for t in self._templates.values()
        ]

    def get_template(self, template_id: str) -> BaseReportTemplate:
        """Looks up a template by its ID. Falls back to ExecutiveTemplate on missing."""
        return self._templates.get(template_id, self._templates["executive_report"])

    def render_cover_page(self, title: str, report_type: str, start: str, end: str) -> str:
        """Returns standard ASCII-art cover header wrapper."""
        line = "=" * 75
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
{line}
                  SMART TRAFFIC VIOLATION DETECTION SYSTEM
                             OFFICIAL REPORT
{line}
REPORT TITLE      : {title}
REPORT TYPE       : {report_type.upper()}
DATE RANGE        : {start} to {end}
GENERATED AT      : {now_str} UTC
{line}
\n"""

    def render_kpis_table(self, kpis: Dict[str, Any]) -> str:
        """Compiles a formatted KPI stats grid."""
        return f"""
EXECUTIVE KPI SUMMARY:
---------------------------------------------------------------------------
Total Violations Flagged : {kpis.get('total_violations', 0):<15} | Active Cameras   : {kpis.get('active_cameras', 0)}
Total Vehicles Scanned   : {kpis.get('total_vehicles', 0):<15} | Database Status  : {kpis.get('db_health', 'unknown').upper()}
Total Fines Assessed     : INR {kpis.get('total_fines', 0.0):<11.2f} | Average AI Conf  : {kpis.get('avg_confidence', 0.0):.2%}
System Diagnostic Uptime : {kpis.get('system_uptime', '99.9%'):<15} |
---------------------------------------------------------------------------
\n"""

    def render_distributions(self, violations: List[Dict[str, Any]], vehicles: List[Dict[str, Any]]) -> str:
        """Formats vehicle and violation distributions side by side."""
        lines = []
        lines.append("DISTRIBUTION SUMMARIES:")
        lines.append("---------------------------------------------------------------------------")
        lines.append(f"{'Violation Category':<28} | {'Count':<6} || {'Vehicle Class':<20} | {'Count':<6}")
        lines.append("---------------------------------------------------------------------------")
        
        max_len = max(len(violations), len(vehicles))
        for i in range(max_len):
            v_str = ""
            if i < len(violations):
                v_str = f"{violations[i]['name'][:28]:<28} | {violations[i]['value']:<6}"
            else:
                v_str = f"{'':<28} | {'':<6}"
                
            vh_str = ""
            if i < len(vehicles):
                vh_str = f"{vehicles[i]['name'][:20]:<20} | {vehicles[i]['value']:<6}"
            else:
                vh_str = f"{'':<20} | {'':<6}"
                
            lines.append(f"{v_str} || {vh_str}")
            
        lines.append("---------------------------------------------------------------------------")
        return "\n".join(lines) + "\n\n"

    def render_footer(self, page_num: int = 1) -> str:
        """Generates a standard document footer."""
        line = "-" * 75
        return f"""
{line}
Generated by Traffic Violation AI   |   Page {page_num}   |   Confidential
{line}"""


# Singleton template service instance
report_template_service = ReportTemplateService()

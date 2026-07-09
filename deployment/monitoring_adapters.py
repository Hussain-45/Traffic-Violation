"""
Monitoring and Telemetry Adapters
=================================
Defines metrics exporting interfaces (Prometheus, OpenTelemetry, Loki, Jaeger).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseMonitoringExporter(ABC):
    """
    Abstract exporter interface for telemetry metrics.
    """

    @abstractmethod
    def export_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        """Sends a numeric metric value to telemetry metrics collectors."""
        pass


class PrometheusExporter(BaseMonitoringExporter):
    """
    Formats and exposes metrics ready for Prometheus scraping queries.
    """

    def export_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        # Formats metrics as: stvds_metric_name{tag="val"} 1.0
        tag_str = ",".join([f'{k}="{v}"' for k, v in tags.items()])
        formatted = f"stvds_{name}{{{tag_str}}} {value}"
        print(f"[Prometheus Export] {formatted}")


class LokiLogExporter(BaseMonitoringExporter):
    """
    Formats logs and events for Grafana Loki collection.
    """

    def export_metric(self, name: str, value: float, tags: Dict[str, str]) -> None:
        # Formats logs in Loki JSON payload
        log_payload = {
            "streams": [
                {
                    "stream": tags,
                    "values": [[str(value), f"Metric {name} value logged"]]
                }
            ]
        }
        print(f"[Loki Export] {log_payload}")

from typing import Optional
import logging
import json

from lnst.Controller.Recipe import RecipeRun
from lnst.Controller.RecipeResults import (
    DeviceAttrSetResult,
    DeviceConfigResult,
    DeviceCreateResult,
    DeviceMethodCallResult,
    JobResult,
    JobStartResult,
    MeasurementResult,
    BaseResult,
)
from .RunSummaryFormatter import RunSummaryFormatter


class JsonRunSummaryFormatter(RunSummaryFormatter):
    def __init__(self, pretty: bool = False):
        super().__init__()
        self.pretty = pretty

    def format_run(self, run: RecipeRun) -> str:
        recipe_results = [
            transformed
            for result in run.results
            if (transformed := self._transform_result(result)) is not None
        ]

        if exc := run.exception:
            exception_result = {
                "result": "FAIL",
                "type": "exception",
                "message": str(exc),
            }
            recipe_results.append(exception_result)

        return json.dumps(
            recipe_results,
            indent=4 if self.pretty else None,
        )

    def _transform_result(self, result: BaseResult) -> Optional[dict]:
        ret = {
            "result": str(result.result),
        }
        if isinstance(result, JobResult):
            if isinstance(result.job.what, str):
                job_info = {
                    "type": "shell",
                    "command": result.job.what,
                }
            else:
                job_info = {
                    "type": "module",
                    "repr": repr(result.job.what),
                }
            return ret | {
                "type": "job",
                "action": "start" if isinstance(result, JobStartResult) else "end",
                "job": job_info,
            }
        elif isinstance(result, DeviceConfigResult):
            if isinstance(result, DeviceCreateResult):
                action_info = {
                    "action": "create",
                    "device": {
                        "cls_name": result.device._dev_cls.__name__,
                        "args": [repr(arg) for arg in result.device._dev_args],
                        "kwargs": [f"{k}={v!r}" for k, v in result.device._dev_kwargs.items()],
                    },
                }
            elif isinstance(result, DeviceMethodCallResult):
                action_info = {
                    "action": "method_call",
                    "method": {
                        "name": result.method_name,
                        "args": [repr(arg) for arg in result.args],
                        "kwargs": [f"{k}={v!r}" for k, v in result.kwargs.items()],
                    },
                }
            elif isinstance(result, DeviceAttrSetResult):
                action_info = {
                    "action": "attr_set",
                    "attr": {
                        "name": result.attr_name,
                        "value": repr(result.value),
                        "old_value": repr(result.old_value),
                    },
                }
            else:
                logging.warning(f"unhandled device config result: {result.__class__.__name__}")
                action_info = {"action": "unknown"}
            return ret | {
                "type": "device_config",
                "host": result.device.host.hostid,
                "netns": result.device.netns.name if result.device.netns and result.device.netns.name else "",
                "dev_id": result.device._id,
            } | action_info
        elif isinstance(result, MeasurementResult):
            if result.measurement_type == "ping":
                measurement_data = result.data
            elif result.measurement_type == "cpu":
                measurement_data = {
                    "utilization": result.data["cpu"].average,
                }
            elif result.measurement_type == "flow":
                agg_results = result.data["flow_results"]
                measurement_data = {
                    "generator_results": agg_results.generator_results.average,
                    "generator_cpu_stats": agg_results.generator_cpu_stats.average,
                    "receiver_results": agg_results.receiver_results.average,
                    "receiver_cpu_stats": agg_results.receiver_cpu_stats.average,
                }
            elif result.measurement_type == "tc":
                measurement_data = {
                    "rule_install_rate": result.data["rule_install_rate"].average,
                }
            elif result.measurement_type == "linuxperf":
                # linuxperf measurement just generates files
                measurement_data = {}
            elif result.measurement_type == "rdma-bandwidth":
                measurement_data = {
                    "bandwidth": result.data["bandwidth"].average,
                }
            elif result.measurement_type == "xdp-bench":
                measurement_data = {
                    "generator_results": result.data["generator_results"].average,
                    "receiver_results": result.data["receiver_results"].average,
                }
            elif result.measurement_type == "xdp-redirect-cpu":
                measurement_data = {
                    "generator_results": result.data["generator_results"].average,
                    "receiver_results": result.data["receiver_results"].average,
                    "forwarded_results": result.data["forwarded_results"].average,
                }
            elif result.measurement_type == "forwarding":
                measurement_data = {
                    "generator_results": result.data["generator_results"].average,
                    "receiver_results": result.data["receiver_results"].average,
                    "forwarder_rx_results": result.data["forwarder_rx_results"].average,
                    "forwarder_tx_results": result.data["forwarder_tx_results"].average,
                }
            else:
                logging.warning(f"unhandled measurement result type: {result.measurement_type}")
                measurement_data = None
            out = ret | {
                "type": "measurement",
                "measurement_type": result.measurement_type,
                "data": measurement_data,
            }
            if (meas_results := result.measurement_results) is not None:
                out["measurement_class"] = meas_results.measurement.__class__.__name__
                out["metric_metadata"] = meas_results.metric_metadata
                out["hosts"] = self._extract_hosts(meas_results)
                if isinstance(measurement_data, dict):
                    units = {}
                    for metric in measurement_data:
                        metric_val = getattr(meas_results, metric, None)
                        if metric_val is not None and getattr(metric_val, "unit", None) is not None:
                            units[metric] = metric_val.unit
                    out["units"] = units
            return out
        else:
            if result.data is not None:
                logging.warning(f"unhandled recipe result type: {repr(result)}, can't format its data")

            return ret | {
                "type": "unknown",
                "description": result.description,
            }

    @staticmethod
    def _extract_hosts(meas_results) -> dict[str, str]:
        hosts: dict[str, str] = {}
        candidates = []
        if (host := getattr(meas_results, "host", None)) is not None:
            candidates.append(host)
        if (flows := getattr(meas_results, "flows", None)) is not None:
            for flow in flows:
                candidates.extend(
                    [getattr(flow, "generator", None), getattr(flow, "receiver", None)]
                )
        elif (flow := getattr(meas_results, "flow", None)) is not None:
            candidates.extend(
                [getattr(flow, "generator", None), getattr(flow, "receiver", None)]
            )
        for h in candidates:
            hostid = getattr(h, "hostid", None)
            hostname = getattr(h, "hostname", None)
            if hostid and hostname:
                hosts[hostid] = hostname
        return hosts

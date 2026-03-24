import argparse
import queue
import threading
from datetime import datetime
from typing import Any, Callable

try:
    import grpc
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "grpcio is required. Install with: python -m pip install -r requirements.txt"
    ) from exc

import robot_gateway_pb2 as pb2
import robot_gateway_pb2_grpc as pb2_grpc
import tkinter as tk
from google.protobuf.json_format import MessageToDict
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class ExternalGrpcGuiClient:
    def __init__(self, root: tk.Tk, default_target: str) -> None:
        self.root = root
        self.root.title("Robot gRPC External Test Client")
        self.root.geometry("1100x760")

        self._watch_thread: threading.Thread | None = None
        self._watch_stop_event = threading.Event()
        self._log_queue: queue.Queue[str] = queue.Queue()

        self.target_var = tk.StringVar(value=default_target)
        self.timeout_var = tk.StringVar(value="180.0")
        self.watch_interval_var = tk.StringVar(value="500")
        self.watch_count_var = tk.StringVar(value="0")

        self.exec_command_id_var = tk.StringVar(value="cmd-1")
        self.exec_task_id_var = tk.StringVar(value="")
        self.exec_task_type_var = tk.StringVar(value="0")
        self.exec_target_zone_var = tk.StringVar(value="")
        self.exec_target_x_var = tk.StringVar(value="0.0")
        self.exec_target_y_var = tk.StringVar(value="0.0")
        self.exec_target_yaw_var = tk.StringVar(value="0.0")
        self.exec_module_type_var = tk.StringVar(value="1")
        self.exec_module_power_var = tk.BooleanVar(value=True)
        self.exec_module_level_var = tk.StringVar(value="2")
        self.exec_max_exec_sec_var = tk.StringVar(value="120")

        self.cancel_command_id_var = tk.StringVar(value="cmd-cancel-1")
        self.cancel_task_id_var = tk.StringVar(value="task-1")

        self.estop_command_id_var = tk.StringVar(value="cmd-estop-1")
        self.estop_reason_var = tk.StringVar(value="manual_emergency")

        self.manual_command_id_var = tk.StringVar(value="cmd-manual-1")
        self.manual_vx_var = tk.StringVar(value="0.2")
        self.manual_wz_var = tk.StringVar(value="0.0")
        self.manual_duration_var = tk.StringVar(value="1500")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        top = ttk.LabelFrame(self.root, text="Connection")
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Target").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.target_var, width=28).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(top, text="RPC Timeout (sec)").grid(row=0, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.timeout_var, width=10).grid(
            row=0, column=3, sticky="w", padx=6, pady=6
        )
        ttk.Button(top, text="Get Status", command=self.on_get_status).grid(
            row=0, column=4, sticky="w", padx=6, pady=6
        )

        ttk.Label(top, text="Watch Interval (ms)").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.watch_interval_var, width=12).grid(
            row=1, column=1, sticky="w", padx=6, pady=6
        )
        ttk.Label(top, text="Watch Count (0=inf)").grid(row=1, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(top, textvariable=self.watch_count_var, width=10).grid(
            row=1, column=3, sticky="w", padx=6, pady=6
        )
        ttk.Button(top, text="Start Watch", command=self.on_start_watch).grid(
            row=1, column=4, sticky="w", padx=6, pady=6
        )
        ttk.Button(top, text="Stop Watch", command=self.on_stop_watch).grid(
            row=1, column=5, sticky="w", padx=6, pady=6
        )

        body = ttk.Frame(self.root)
        body.pack(fill="both", expand=True, padx=10, pady=0)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        self._build_execute_panel(body).grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self._build_ops_panel(body).grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        log_frame = ttk.LabelFrame(self.root, text="Response / Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text = ScrolledText(log_frame, height=16, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

        button_bar = ttk.Frame(self.root)
        button_bar.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(button_bar, text="Clear Log", command=self.clear_log).pack(side="right")

    def _build_execute_panel(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="ExecuteTask")
        fields = [
            ("command_id", self.exec_command_id_var),
            ("task_id", self.exec_task_id_var),
            ("task_type (0~3)", self.exec_task_type_var),
            ("target_zone", self.exec_target_zone_var),
            ("target_x", self.exec_target_x_var),
            ("target_y", self.exec_target_y_var),
            ("target_yaw", self.exec_target_yaw_var),
            ("module_type", self.exec_module_type_var),
            ("module_level", self.exec_module_level_var),
            ("max_exec_sec", self.exec_max_exec_sec_var),
        ]
        for idx, (label, var) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(frame, textvariable=var, width=22).grid(
                row=idx, column=1, sticky="w", padx=6, pady=4
            )
        ttk.Checkbutton(frame, text="module_power", variable=self.exec_module_power_var).grid(
            row=10, column=0, sticky="w", padx=6, pady=4
        )
        ttk.Button(frame, text="Execute", command=self.on_execute).grid(
            row=10, column=1, sticky="e", padx=6, pady=8
        )
        return frame

    def _build_ops_panel(self, parent: ttk.Frame) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text="Cancel / E-Stop / Manual")

        cancel = ttk.LabelFrame(frame, text="CancelTask")
        cancel.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        ttk.Label(cancel, text="command_id").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(cancel, textvariable=self.cancel_command_id_var, width=24).grid(
            row=0, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Label(cancel, text="task_id").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(cancel, textvariable=self.cancel_task_id_var, width=24).grid(
            row=1, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Button(cancel, text="Cancel", command=self.on_cancel).grid(
            row=2, column=1, sticky="e", padx=4, pady=6
        )

        estop = ttk.LabelFrame(frame, text="EmergencyStop")
        estop.grid(row=1, column=0, sticky="ew", padx=6, pady=6)
        ttk.Label(estop, text="command_id").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(estop, textvariable=self.estop_command_id_var, width=24).grid(
            row=0, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Label(estop, text="reason").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(estop, textvariable=self.estop_reason_var, width=24).grid(
            row=1, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Button(estop, text="E-Stop", command=self.on_estop).grid(
            row=2, column=1, sticky="e", padx=4, pady=6
        )

        manual = ttk.LabelFrame(frame, text="ManualControl")
        manual.grid(row=2, column=0, sticky="ew", padx=6, pady=6)
        ttk.Label(manual, text="command_id").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(manual, textvariable=self.manual_command_id_var, width=24).grid(
            row=0, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Label(manual, text="vx").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(manual, textvariable=self.manual_vx_var, width=24).grid(
            row=1, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Label(manual, text="wz").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(manual, textvariable=self.manual_wz_var, width=24).grid(
            row=2, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Label(manual, text="duration_ms").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(manual, textvariable=self.manual_duration_var, width=24).grid(
            row=3, column=1, sticky="w", padx=4, pady=4
        )
        ttk.Button(manual, text="Manual", command=self.on_manual).grid(
            row=4, column=1, sticky="e", padx=4, pady=6
        )

        return frame

    def _log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log_queue.put(f"[{now}] {message}")

    def _drain_log_queue(self) -> None:
        try:
            while True:
                text = self._log_queue.get_nowait()
                self.log_text.insert("end", text + "\n")
                self.log_text.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log_queue)

    def clear_log(self) -> None:
        self.log_text.delete("1.0", "end")

    def _call_unary(self, name: str, fn: Callable[[Any], Any]) -> None:
        try:
            target = self.target_var.get().strip()
            timeout = float(self.timeout_var.get().strip() or "180.0")
            with grpc.insecure_channel(target) as channel:
                stub = pb2_grpc.RobotGatewayStub(channel)
                response = fn((stub, timeout))
            payload = MessageToDict(response, preserving_proto_field_name=True)
            self._log(f"{name} response:\n{json_dumps(payload)}")
        except Exception as exc:  # noqa: BLE001
            self._log(f"{name} error: {exc}")

    def on_get_status(self) -> None:
        threading.Thread(
            target=self._call_unary,
            args=("GetStatus", lambda x: x[0].GetStatus(pb2.GetStatusRequest(), timeout=x[1])),
            daemon=True,
        ).start()

    def on_execute(self) -> None:
        def _exec(args):
            stub, timeout = args
            max_exec_sec = int(self.exec_max_exec_sec_var.get().strip() or "120")
            effective_timeout = max(float(timeout), float(max_exec_sec) + 30.0)
            req = pb2.ExecuteTaskRequest(
                command_id=self.exec_command_id_var.get().strip(),
                task_id=self.exec_task_id_var.get().strip(),
                task_type=int(self.exec_task_type_var.get().strip() or "0"),
                target_zone=self.exec_target_zone_var.get().strip(),
                target_x=float(self.exec_target_x_var.get().strip() or "0.0"),
                target_y=float(self.exec_target_y_var.get().strip() or "0.0"),
                target_yaw=float(self.exec_target_yaw_var.get().strip() or "0.0"),
                module_type=int(self.exec_module_type_var.get().strip() or "0"),
                module_power=bool(self.exec_module_power_var.get()),
                module_level=int(self.exec_module_level_var.get().strip() or "0"),
                max_exec_sec=max_exec_sec,
            )
            return stub.ExecuteTask(req, timeout=effective_timeout)

        threading.Thread(target=self._call_unary, args=("ExecuteTask", _exec), daemon=True).start()

    def on_cancel(self) -> None:
        def _cancel(args):
            stub, timeout = args
            req = pb2.CancelTaskRequest(
                command_id=self.cancel_command_id_var.get().strip(),
                task_id=self.cancel_task_id_var.get().strip(),
            )
            return stub.CancelTask(req, timeout=timeout)

        threading.Thread(target=self._call_unary, args=("CancelTask", _cancel), daemon=True).start()

    def on_estop(self) -> None:
        def _estop(args):
            stub, timeout = args
            req = pb2.EmergencyStopRequest(
                command_id=self.estop_command_id_var.get().strip(),
                reason=self.estop_reason_var.get().strip(),
            )
            return stub.EmergencyStop(req, timeout=timeout)

        threading.Thread(target=self._call_unary, args=("EmergencyStop", _estop), daemon=True).start()

    def on_manual(self) -> None:
        def _manual(args):
            stub, timeout = args
            req = pb2.ManualControlRequest(
                command_id=self.manual_command_id_var.get().strip(),
                vx=float(self.manual_vx_var.get().strip() or "0.0"),
                wz=float(self.manual_wz_var.get().strip() or "0.0"),
                duration_ms=int(self.manual_duration_var.get().strip() or "1000"),
            )
            return stub.ManualControl(req, timeout=timeout)

        threading.Thread(target=self._call_unary, args=("ManualControl", _manual), daemon=True).start()

    def on_start_watch(self) -> None:
        if self._watch_thread and self._watch_thread.is_alive():
            self._log("watch is already running")
            return
        self._watch_stop_event.clear()
        self._watch_thread = threading.Thread(target=self._watch_worker, daemon=True)
        self._watch_thread.start()
        self._log("watch started")

    def on_stop_watch(self) -> None:
        self._watch_stop_event.set()
        self._log("watch stop requested")

    def _watch_worker(self) -> None:
        try:
            target = self.target_var.get().strip()
            interval_ms = int(self.watch_interval_var.get().strip() or "500")
            count_limit = int(self.watch_count_var.get().strip() or "0")
            interval_ms = max(100, min(10000, interval_ms))

            with grpc.insecure_channel(target) as channel:
                stub = pb2_grpc.RobotGatewayStub(channel)
                req = pb2.StreamStatusRequest(interval_ms=interval_ms)
                stream = stub.StreamStatus(req)
                seen = 0
                for status in stream:
                    if self._watch_stop_event.is_set():
                        break
                    payload = MessageToDict(status, preserving_proto_field_name=True)
                    self._log(f"StreamStatus:\n{json_dumps(payload)}")
                    seen += 1
                    if count_limit > 0 and seen >= count_limit:
                        break
        except Exception as exc:  # noqa: BLE001
            self._log(f"watch error: {exc}")
        finally:
            self._log("watch stopped")

    def _on_close(self) -> None:
        self._watch_stop_event.set()
        self.root.destroy()


def json_dumps(payload: Any) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="External GUI gRPC test client")
    parser.add_argument("--target", default="127.0.0.1:50051", help="gRPC host:port")
    args = parser.parse_args()

    root = tk.Tk()
    app = ExternalGrpcGuiClient(root, default_target=args.target)
    app._log("GUI client ready")
    root.mainloop()


if __name__ == "__main__":
    main()

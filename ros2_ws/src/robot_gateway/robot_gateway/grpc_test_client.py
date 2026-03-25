import argparse
import json
import time
from typing import Any, Dict

try:
    import grpc  # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "grpcio is required for grpc_test_client. Install with: python -m pip install grpcio grpcio-tools"
    ) from exc

from . import robot_gateway_pb2 as pb2  # noqa: E402
from . import robot_gateway_pb2_grpc as pb2_grpc  # noqa: E402


def _print_proto(msg) -> None:
    data: Dict[str, Any] = {}
    for field, value in msg.ListFields():
        data[field.name] = value
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def cmd_execute(stub, args) -> None:
    req = pb2.ExecuteTaskRequest(
        command_id=args.command_id,
        task_id=args.task_id,
        task_type=args.task_type,
        target_zone=args.target_zone,
        target_x=args.target_x,
        target_y=args.target_y,
        target_yaw=args.target_yaw,
        module_type=args.module_type,
        module_power=args.module_power,
        module_level=args.module_level,
        max_exec_sec=args.max_exec_sec,
    )
    _print_proto(stub.ExecuteTask(req))


def cmd_cancel(stub, args) -> None:
    req = pb2.CancelTaskRequest(command_id=args.command_id, task_id=args.task_id)
    _print_proto(stub.CancelTask(req))


def cmd_estop(stub, args) -> None:
    req = pb2.EmergencyStopRequest(command_id=args.command_id, reason=args.reason)
    _print_proto(stub.EmergencyStop(req))


def cmd_manual(stub, args) -> None:
    req = pb2.ManualControlRequest(
        command_id=args.command_id, vx=args.vx, wz=args.wz, duration_ms=args.duration_ms
    )
    _print_proto(stub.ManualControl(req))


def cmd_status(stub, args) -> None:
    del args
    _print_proto(stub.GetStatus(pb2.GetStatusRequest()))


def cmd_watch(stub, args) -> None:
    req = pb2.StreamStatusRequest(interval_ms=args.interval_ms)
    stream = stub.StreamStatus(req)
    for idx, status in enumerate(stream):
        _print_proto(status)
        if args.count > 0 and idx + 1 >= args.count:
            break
        time.sleep(0.01)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="gRPC test client for robot gateway")
    parser.add_argument("--target", default="127.0.0.1:50051", help="gRPC target host:port")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_execute = sub.add_parser("execute")
    p_execute.add_argument("--command-id", required=True)
    p_execute.add_argument("--task-id", default="")
    p_execute.add_argument("--task-type", type=int, default=0)
    p_execute.add_argument("--target-zone", default="")
    p_execute.add_argument("--target-x", type=float, default=0.0)
    p_execute.add_argument("--target-y", type=float, default=0.0)
    p_execute.add_argument("--target-yaw", type=float, default=0.0)
    p_execute.add_argument("--module-type", type=int, default=0)
    p_execute.add_argument("--module-power", action="store_true")
    p_execute.add_argument("--module-level", type=int, default=0)
    p_execute.add_argument("--max-exec-sec", type=int, default=600)
    p_execute.set_defaults(func=cmd_execute)

    p_cancel = sub.add_parser("cancel")
    p_cancel.add_argument("--command-id", required=True)
    p_cancel.add_argument("--task-id", required=True)
    p_cancel.set_defaults(func=cmd_cancel)

    p_estop = sub.add_parser("estop")
    p_estop.add_argument("--command-id", required=True)
    p_estop.add_argument("--reason", default="manual_emergency")
    p_estop.set_defaults(func=cmd_estop)

    p_manual = sub.add_parser("manual")
    p_manual.add_argument("--command-id", required=True)
    p_manual.add_argument("--vx", type=float, default=0.0)
    p_manual.add_argument("--wz", type=float, default=0.0)
    p_manual.add_argument("--duration-ms", type=int, default=1000)
    p_manual.set_defaults(func=cmd_manual)

    p_status = sub.add_parser("status")
    p_status.set_defaults(func=cmd_status)

    p_watch = sub.add_parser("watch")
    p_watch.add_argument("--interval-ms", type=int, default=500)
    p_watch.add_argument("--count", type=int, default=10, help="0 for infinite")
    p_watch.set_defaults(func=cmd_watch)

    args = parser.parse_args(argv)
    with grpc.insecure_channel(args.target) as channel:
        stub = pb2_grpc.RobotGatewayStub(channel)
        args.func(stub, args)


if __name__ == "__main__":
    main()

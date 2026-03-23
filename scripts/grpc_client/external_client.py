import argparse
import json
from typing import Any, Dict

try:
    import grpc
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "grpcio is required. Install with: python -m pip install -r requirements.txt"
    ) from exc

from google.protobuf.json_format import MessageToDict
import robot_gateway_pb2 as pb2
import robot_gateway_pb2_grpc as pb2_grpc


def _print_proto(msg) -> None:
    try:
        data: Dict[str, Any] = MessageToDict(
            msg,
            preserving_proto_field_name=True,
            always_print_fields_with_no_presence=True,
            use_integers_for_enums=True,
        )
    except TypeError:
        # Fallback for older protobuf versions.
        data = MessageToDict(
            msg,
            preserving_proto_field_name=True,
            including_default_value_fields=True,
            use_integers_for_enums=True,
        )
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
    _print_proto(stub.ExecuteTask(req, timeout=args.rpc_timeout_sec))


def cmd_cancel(stub, args) -> None:
    req = pb2.CancelTaskRequest(command_id=args.command_id, task_id=args.task_id)
    _print_proto(stub.CancelTask(req, timeout=args.rpc_timeout_sec))


def cmd_estop(stub, args) -> None:
    req = pb2.EmergencyStopRequest(command_id=args.command_id, reason=args.reason)
    _print_proto(stub.EmergencyStop(req, timeout=args.rpc_timeout_sec))


def cmd_manual(stub, args) -> None:
    req = pb2.ManualControlRequest(
        command_id=args.command_id,
        vx=args.vx,
        wz=args.wz,
        duration_ms=args.duration_ms,
    )
    _print_proto(stub.ManualControl(req, timeout=args.rpc_timeout_sec))


def cmd_status(stub, args) -> None:
    del args
    _print_proto(stub.GetStatus(pb2.GetStatusRequest()))


def cmd_watch(stub, args) -> None:
    req = pb2.StreamStatusRequest(interval_ms=args.interval_ms)
    stream = stub.StreamStatus(req)
    seen = 0
    for status in stream:
        _print_proto(status)
        seen += 1
        if args.count > 0 and seen >= args.count:
            break


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="External gRPC test client (no ROS2 dependency)"
    )
    parser.add_argument("--target", default="127.0.0.1:50051", help="gRPC host:port")
    parser.add_argument(
        "--rpc-timeout-sec",
        type=float,
        default=30.0,
        help="timeout for unary RPC calls",
    )

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
    p_execute.add_argument("--max-exec-sec", type=int, default=120)
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
    p_watch.add_argument("--count", type=int, default=10, help="0 means infinite")
    p_watch.set_defaults(func=cmd_watch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    with grpc.insecure_channel(args.target) as channel:
        stub = pb2_grpc.RobotGatewayStub(channel)
        args.func(stub, args)


if __name__ == "__main__":
    main()

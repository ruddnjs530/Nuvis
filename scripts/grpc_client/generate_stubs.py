import pathlib
import subprocess
import sys


def main() -> int:
    base = pathlib.Path(__file__).resolve().parent
    proto = base / "robot_gateway.proto"
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{base}",
        f"--python_out={base}",
        f"--grpc_python_out={base}",
        str(proto),
    ]
    print(" ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())

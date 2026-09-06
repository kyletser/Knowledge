#!/usr/bin/env python3
"""在服务器 150.158.89.70 上执行 shell 命令（公众号订阅自动化运维助手）。

密码不落盘：从环境变量 WECHAT_SSH_PW 读取。
用法：
    WECHAT_SSH_PW=xxx python sshrun.py "docker ps"          # 执行单条命令
    echo "cmd1; cmd2" | python sshrun.py                    # 从 stdin 读命令
"""
from __future__ import annotations

import os
import sys

import paramiko

HOST = "150.158.89.70"
USER = "root"


def main() -> int:
    pw = os.environ.get("WECHAT_SSH_PW")
    if not pw:
        print("错误：请先设置环境变量 WECHAT_SSH_PW", file=sys.stderr)
        return 2
    cmd = " ".join(sys.argv[1:]).strip() or sys.stdin.read().strip()
    if not cmd:
        print("错误：没有要执行的命令", file=sys.stderr)
        return 2

    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, password=pw, timeout=15,
                look_for_keys=False, allow_agent=False)
    try:
        stdin, stdout, stderr = cli.exec_command(cmd, timeout=180)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        rc = stdout.channel.recv_exit_status()
        if out:
            print(out, end="" if out.endswith("\n") else "\n")
        if err:
            print("[stderr] " + err, file=sys.stderr, end="" if err.endswith("\n") else "\n")
        return rc
    finally:
        cli.close()


if __name__ == "__main__":
    raise SystemExit(main())

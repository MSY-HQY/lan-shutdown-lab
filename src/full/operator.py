# -*- coding: utf-8 -*-
"""
远程关机实验 · 操作端（改进版）
—— 这份跑在「你手上这台电脑」上。

只在你自己拥有、或明确授权你测试的设备上使用。

用法：
    python operator.py

启动后它会列出本机的局域网 IP，把其中一个填进被控端（例如 192.168.1.10）。

相比原版改了什么：
    1. 启动时打印本机所有局域网 IP，省得你猜该填哪个
    2. 先 bind 再 accept，收到一个连接断开后还能继续等下一个（原版只接一次）
    3. 命令改成循环发送，一条连接可以连发多条（原版发一次就退出）
    4. 能看到被控端回话（收到什么、执行结果），原版发完就没下文
    5. 加了 3=取消关机、4=测试（响两声）、5=查对方主机名和 IP
"""
import os
import socket
import time

端口 = int(os.environ.get("LAB_PORT", "4444"))   # 端口被占用时：set LAB_PORT=4455 再运行
监听地址 = "0.0.0.0"          # 表示"本机所有地址都监听"，这样被控端填哪个 IP 都能连进来

菜单 = """
  ┌───────────────────────────────────────────────┐
  │  1 = 关机（30 秒后执行）   2 = 重启（30 秒后）│
  │  3 = 取消关机/重启         4 = 测试（响两声） │
  │  5 = 查对方主机名和 IP     9 = 断开这次连接   │
  │  q = 退出操作端                               │
  └───────────────────────────────────────────────┘
"""


def 本机地址():
    """列出本机局域网 IP（去掉 127.0.0.1 这类回环地址）。"""
    地址 = set()
    try:
        地址 |= {i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
    except Exception:
        pass
    return sorted(a for a in 地址 if not a.startswith("127."))


def 主流程():
    print("=" * 54)
    print("操作端 已启动，等待被控端连进来……")
    print("本机局域网 IP（被控端里填的就是其中之一）：")
    for ip in 本机地址() or ["（没读到，运行 ipconfig 自己看一下）"]:
        print("   ", ip)
    print(f"监听端口 {端口}   —— 第一次运行防火墙弹窗时选「专用网络」「允许」")
    print("=" * 54)

    with socket.socket() as S:
        S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        S.bind((监听地址, 端口))
        S.listen(1)

        while True:                          # 外层：一次连接用完，回去等下一个
            print("等待被控端……")
            s, addr = S.accept()
            print(f"[{time.strftime('%H:%M:%S')}] 被控端已连上：{addr[0]}:{addr[1]}")
            print(菜单)

            with s:
                while True:                  # 内层：同一条连接上连发多条命令
                    try:
                        命令 = input("命令（1/2/3/4/5/9/q）：").strip()
                    except (EOFError, KeyboardInterrupt):
                        命令 = "q"
                    if not 命令:
                        continue
                    if 命令.lower() in ("q", "quit", "exit"):
                        print("退出操作端。")
                        return

                    try:
                        s.send(命令.encode("utf-8"))
                    except Exception as e:
                        print("发送失败：", e)
                        break

                    if 命令 == "9":
                        print("已断开这次连接，回去等下一个。")
                        break

                    s.settimeout(3)
                    try:
                        回复 = s.recv(4096).decode("utf-8", "ignore")
                        if 回复:
                            print("  被控端回话：", 回复)
                    except socket.timeout:
                        print("  （3 秒内没回话，可能对方程序没在跑）")
                    except Exception as e:
                        print("  接收失败：", e)
                    finally:
                        s.settimeout(None)

            # 断开后先问一句，再回去等下一个连接（否则会卡在 accept 上读不到键盘）
            try:
                继续 = input("回车＝继续等下一个连接，q＝退出操作端：").strip().lower()
            except (EOFError, KeyboardInterrupt):
                继续 = "q"
            if 继续 == "q":
                print("退出操作端。")
                return


if __name__ == "__main__":
    try:
        主流程()
    except KeyboardInterrupt:
        print("\n已退出。")

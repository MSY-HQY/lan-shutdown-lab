# -*- coding: utf-8 -*-
"""
远程关机实验 · 被控端（改进版）
—— 这份跑在「要被控制的那台电脑」上。

只在你自己拥有、或明确授权你测试的设备上运行。别往别人的机器上放。

用法（推荐第一种）：
    python target.py 192.168.1.10    # 直接给出操作端那台电脑的局域网 IP
    python target.py                 # 不带参数：先读 被控端配置.txt，没有就现场问你

相比原版改了什么：
    1. IP 不再写死；给了参数/配置就记住，下次不用再输
    2. 连不上就每 3 秒重试，所以「谁先运行」不再重要（原版必须操作端先跑）
    3. 收命令改成循环：一条连接可以连发多条命令，原版发一次就结束
    4. 新增 3=取消关机、4=响两声（测试用不关机）、5=查主机名和 IP、9=断开
    5. 关机/重启留 30 秒倒计时，来得及用 3 取消（原来只留 1 秒）
"""
import os
import socket
import subprocess
import sys
import time

try:
    import winsound
except ImportError:          # 非 Windows 上跑也不至于直接崩
    winsound = None

端口 = int(os.environ.get("LAB_PORT", "4444"))   # 端口被占用时：set LAB_PORT=4455 再运行
延迟秒 = 30                  # 关机/重启的倒计时，测试时不要改太短
配置文件 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "被控端配置.txt")


def 取操作端地址():
    """优先命令行参数，其次配置文件，最后现场问。"""
    ip = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not ip and os.path.exists(配置文件):
        ip = open(配置文件, encoding="utf-8").read().strip()
    if not ip:
        ip = input("请输入操作端那台电脑的局域网 IP（例如 192.168.1.10）：").strip()
        if ip:
            try:
                with open(配置文件, "w", encoding="utf-8") as f:
                    f.write(ip)
            except OSError:
                pass
    return ip


def 本机地址():
    try:
        return sorted({i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)})
    except Exception:
        return []


def 响两声():
    """响两声 + 弹个窗。
    注意：winsound.Beep() 走的是老式 Beep API（主板蜂鸣器那一路），
    很多笔记本、以及插着耳机的时候根本不出声，所以这里改用系统提示音，
    它走真正的音频设备，耳机里能听到。
    """
    if winsound:
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
            time.sleep(0.5)
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            print("\a")
    else:
        print("\a")


def 弹提示(文字):
    """弹一个提示框当视觉证据（放线程里，不挡命令循环）。"""
    def _弹():
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, 文字, "被控端 · 测试命令", 0x40)
        except Exception:
            pass
    import threading
    threading.Thread(target=_弹, daemon=True).start()


def 跑命令(命令):
    """跑一条 Windows 命令，返回 (退出码, 输出文字)。中文系统输出是 GBK/ANSI，别按 UTF-8 解。"""
    try:
        r = subprocess.run(命令, shell=True, capture_output=True, encoding="mbcs", errors="replace")
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return -1, str(e)


def 执行(命令):
    """执行一条命令，返回 (要不断开, 回给操作端的话)。"""
    if 命令 == "1":
        码, _ = 跑命令(f"shutdown -s -t {延迟秒}")
        return False, (f"已安排关机，{延迟秒} 秒后执行（发 3 可取消）" if 码 == 0 else f"关机命令失败，退出码 {码}（可能没有权限）")
    if 命令 == "2":
        码, _ = 跑命令(f"shutdown -r -t {延迟秒}")
        return False, (f"已安排重启，{延迟秒} 秒后执行（发 3 可取消）" if 码 == 0 else f"重启命令失败，退出码 {码}（可能没有权限）")
    if 命令 == "3":
        码, 输出 = 跑命令("shutdown -a")
        return False, ("已取消关机/重启" if 码 == 0 else "当前没有待执行的关机或重启")
    if 命令 == "4":
        响两声()
        弹提示("这是一条测试命令：\n响过了两声，电源没动。\n\n（如果你在操作端看到这条，说明链路通了）")
        return False, "测试命令已执行（响了提示音 + 弹了个窗），没有动电源"
    if 命令 == "5":
        名字 = socket.gethostname()
        地址 = "、".join(本机地址()) or "未知"
        return False, f"主机名 {名字}；本机 IP {地址}"
    if 命令 in ("9", "q", "quit", "exit"):
        return True, "收到退出命令"
    return False, f"未知命令 {命令!r}（可选 1/2/3/4/5/9）"


def 主流程():
    ip = 取操作端地址()
    if not ip:
        print("没给操作端地址，退出。")
        return
    print("=" * 50)
    print("被控端 已启动")
    print("本机 IP  ：", "、".join(本机地址()) or "未知")
    print("操作端   ：", f"{ip}:{端口}")
    print("=" * 50)

    while True:                              # 外层：断了就回去重连
        s = socket.socket()
        try:
            s.settimeout(8)
            s.connect((ip, 端口))
        except Exception as e:
            s.close()
            print(f"[{time.strftime('%H:%M:%S')}] 连不上 {ip}:{端口}（{e}），3 秒后重试；Ctrl+C 退出")
            time.sleep(3)
            continue

        s.settimeout(None)
        print(f"[{time.strftime('%H:%M:%S')}] 已连上操作端，等命令……")
        while True:                          # 内层：同一条连接上连收多条命令
            try:
                data = s.recv(1024)
            except Exception as e:
                print("接收出错：", e)
                break
            if not data:
                print("操作端断开了，回去等下一次连接。")
                break

            命令 = data.decode("utf-8", "ignore").strip()
            if not 命令:
                continue
            print(f"[{time.strftime('%H:%M:%S')}] 收到命令 {命令!r}")
            try:
                断开, 回复 = 执行(命令)
            except Exception as e:                 # 单条命令出错不该把整个程序带走
                断开, 回复 = False, f"执行出错：{e}"
            try:
                s.send(f"[{socket.gethostname()}] {回复}".encode("utf-8"))
            except Exception:
                pass
            if 断开:
                s.close()
                print("按命令退出。")
                return
        s.close()


if __name__ == "__main__":
    try:
        主流程()
    except KeyboardInterrupt:
        print("\n已手动退出。")

# -*- coding: utf-8 -*-
# 被控端 · 写死 IP 版
# 跑在「要被关机的那台电脑」上（家里的电脑）。
#
# 这就是短视频里那种做法：IP 直接写在代码里，拷过去一运行就连回我这台电脑。
# ↓↓↓ 要换电脑／换网络，只改下面这一行就行 ↓↓↓
IP = "192.168.1.10"     # ← 改成「操作端那台电脑」的局域网 IP

from socket import *
import os
import time
import winsound

端口 = 4444

while True:
    s = socket()
    try:
        s.connect((IP, 端口))
    except Exception as e:
        print(f"连不上 {IP}:{端口}（{e}），3 秒后重试")
        s.close()
        time.sleep(3)
        continue

    print("已连上操作端，等命令……")
    while True:
        try:
            data = s.recv(1024)
        except Exception as e:                 # 操作端被强行关掉时这里会报错，回到外层重连
            print("连接断了（", e, "），重连中……")
            break
        if not data:
            print("操作端断开了，等它再连")
            break
        choice = data.decode("utf-8", "ignore").strip()
        if not choice:
            continue
        print("收到命令：", choice)
        if choice == "1":
            os.system("shutdown -s -t 30")
        elif choice == "2":
            os.system("shutdown -r -t 30")
        elif choice == "3":
            os.system("shutdown -a")
        elif choice == "4":
            for _ in range(2):
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                time.sleep(0.6)
    s.close()

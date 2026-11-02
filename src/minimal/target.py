# -*- coding: utf-8 -*-
# 被控端 · 精简版
# 跑在「要被关机的那台电脑」上。在你原来那份 木马.py 上只改了 5 处，其他照旧：
#
#   ① IP 不再写死：命令行给一个，或者第一次运行问你、记住下次
#   ② 连不上就每 3 秒重试一次（所以谁先启动都行，原版必须操作端先跑）
#   ③ 一条连接可以连发多条命令（原版收一条就结束）
#   ④ 新增 3＝取消关机/重启，4＝只响两声、不动电源
#   ⑤ 关机/重启留 30 秒倒计时，来得及发 3 取消（原来只留 1 秒）
#
# 用法：
#   python target.py 192.168.1.10      ← 直接告诉它操作端那台电脑的 IP
#   python target.py                   ← 不给就问你一次，记进 被控端配置.txt

from socket import *
import os
import sys
import time
import winsound

# 打包成 exe 后 __file__ 指向临时解包目录，所以配置要放到 exe 旁边
if getattr(sys, "frozen", False):
    基准目录 = os.path.dirname(sys.executable)
else:
    基准目录 = os.path.dirname(os.path.abspath(__file__))
配置 = os.path.join(基准目录, "被控端配置.txt")

if len(sys.argv) > 1:                                   # ①
    IP = sys.argv[1]
elif os.path.exists(配置):
    IP = open(配置, encoding="utf-8").read().strip()
else:
    IP = input("请输入操作端那台电脑的局域网 IP（例如 192.168.1.10）：").strip()
    open(配置, "w", encoding="utf-8").write(IP)

端口 = 4444

while True:
    s = socket()
    try:
        s.connect((IP, 端口))
    except Exception as e:
        print(f"连不上 {IP}:{端口}（{e}），3 秒后重试")   # ②
        s.close()
        time.sleep(3)
        continue

    print("已连上操作端，等命令……")
    while True:                                          # ③
        try:
            data = s.recv(1024)
        except Exception as e:                           # 操作端被强行关掉时回到外层重连
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
            os.system("shutdown -s -t 30")               # ⑤
        elif choice == "2":
            os.system("shutdown -r -t 30")               # ⑤
        elif choice == "3":
            os.system("shutdown -a")                     # ④
        elif choice == "4":                              # ④
            for _ in range(2):
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                time.sleep(0.6)
    s.close()

# -*- coding: utf-8 -*-
# 操作端 · 精简版
# 跑在「你自己手上这台电脑」上。在你原来那份 后台.py 上只改了 3 处：
#
#   ① 启动时先打印本机的局域网 IP，省得你猜被控端该填哪个
#   ② 命令改成循环发送，一条连接可以连发多条（原版发一次就退出）
#   ③ 多了 3＝取消关机/重启、4＝响两声（测试用，不动电源）
#
# 用法：
#   python operator.py

from socket import *
import time

端口 = 4444

S = socket()
S.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)      # 刚用完立刻重开也不会报端口占用
S.bind(("0.0.0.0", 端口))                      # 本机所有地址都监听，被控端填哪个 IP 都行
S.listen(1)

print("本机局域网 IP（被控端里填的就是其中之一）：")   # ①
for i in getaddrinfo(gethostname(), None, AF_INET):
    print("   ", i[4][0])
print(f"监听端口 {端口}，等待被控端连进来……（第一次运行防火墙弹窗要选『专用网络』允许）")

s, addr = S.accept()
print("被控端已连上：", addr)

print("1.关机  2.重启  3.取消关机/重启  4.响两声（不关机）")
while True:                                            # ②
    choice = input("请输入你的行为号码（q 退出）：").strip()
    if choice.lower() == "q":
        break
    if not choice:
        continue
    s.send(choice.encode())                            # ③ 发完继续问，不用重连
    time.sleep(0.3)

s.close()
S.close()
print("已退出。")

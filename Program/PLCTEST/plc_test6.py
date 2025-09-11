import serial
from tkinter import *

ser = serial.Serial('COM6', 9600, timeout=1)

root = Tk()
root.title("시리얼 통신") 
root.geometry("480x480+300+100") 


def btncmd_z():
    ser.write(b'\x0501WSS0106%PW0020000\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_0():
    ser.write(b'\x0501WSS0106%PW0020001\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_1():
    ser.write(b'\x0501WSS0106%PW0020002\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_2():
    ser.write(b'\x0501WSS0106%PW0020004\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_3():
    ser.write(b'\x0501WSS0106%PW0020008\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_4():
    ser.write(b'\x0501WSS0106%PW0020010\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_5():
    ser.write(b'\x0501WSS0106%PW0020020\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_6():
    ser.write(b'\x0501WSS0106%PW0020040\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_7():
    ser.write(b'\x0501WSS0106%PW0020080\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_8():
    ser.write(b'\x0501WSS0106%PW0020100\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_9():
    ser.write(b'\x0501WSS0106%PW0020200\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_A():
    ser.write(b'\x0501WSS0106%PW0020400\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_B():
    ser.write(b'\x0501WSS0106%PW0020800\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_C():
    ser.write(b'\x0501WSS0106%PW0021000\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_D():
    ser.write(b'\x0501WSS0106%PW0022000\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_E():
    ser.write(b'\x0501WSS0106%PW0024000\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_F():
    ser.write(b'\x0501WSS0106%PW0028000\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)

def btncmd_all():
    ser.write(b'\x0501WSS0106%PW002FFFF\x04')
    readOut = ser.readline().decode('ascii')
    print(readOut)


btn_0 = Button(root, text="20",  command=btncmd_0, width=5, height=2) 
btn_1 = Button(root, text="21",  command=btncmd_1,  width=5, height=2)
btn_2 = Button(root, text="22",  command=btncmd_2, width=5, height=2)
btn_3 = Button(root, text="23",  command=btncmd_3, width=5, height=2)
btn_0.grid(row=1, column=1, padx=5, pady=5)
btn_1.grid(row=1, column=2, padx=5, pady=5)
btn_2.grid(row=1, column=3, padx=5, pady=5)
btn_3.grid(row=1, column=4, padx=5, pady=5)

btn_4 = Button(root, text="24",  command=btncmd_4, width=5, height=2)
btn_5 = Button(root, text="25",  command=btncmd_5, width=5, height=2)
btn_6 = Button(root, text="26",  command=btncmd_6, width=5, height=2)
btn_7 = Button(root, text="27",  command=btncmd_7, width=5, height=2)
btn_4.grid(row=1, column=5, padx=5, pady=5)
btn_5.grid(row=1, column=6, padx=5, pady=5)
btn_6.grid(row=1, column=7, padx=5, pady=5)
btn_7.grid(row=1, column=8, padx=5, pady=5)

btn_8 = Button(root, text="28",  command=btncmd_8, width=5, height=2)
btn_9 = Button(root, text="29",  command=btncmd_9, width=5, height=2)
btn_A = Button(root, text="2A",  command=btncmd_A, width=5, height=2)
btn_B = Button(root, text="2B",  command=btncmd_B, width=5, height=2)
btn_8.grid(row=2, column=1, padx=5, pady=5)
btn_9.grid(row=2, column=2, padx=5, pady=5)
btn_A.grid(row=2, column=3, padx=5, pady=5)
btn_B.grid(row=2, column=4, padx=5, pady=5)

btn_C = Button(root, text="2C",  command=btncmd_C, width=5, height=2)
btn_D = Button(root, text="2D",  command=btncmd_D, width=5, height=2)
btn_E = Button(root, text="2E",  command=btncmd_E, width=5, height=2)
btn_F = Button(root, text="2F",  command=btncmd_F, width=5, height=2)
btn_C.grid(row=2, column=5, padx=5, pady=5)
btn_D.grid(row=2, column=6, padx=5, pady=5)
btn_E.grid(row=2, column=7, padx=5, pady=5)
btn_F.grid(row=2, column=8, padx=5, pady=5)

btn_k = Button(root, fg="red", text="초기화", command=btncmd_z, width=5, height=2)
btn_k.grid(row=3, column=1, padx=5, pady=10)

btn_all = Button(root, fg="blue", text="ALL", command=btncmd_all, width=5, height=2)
btn_all.grid(row=3, column=2, padx=5, pady=10)

root.mainloop()
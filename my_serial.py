import serial
import time
import os
import struct
import binascii
import threading
import serial.tools.list_ports


from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import pyqtSignal, QObject,QThread


class serial_thread(QThread):

    signal_1 = pyqtSignal(str)
    signal_stat = pyqtSignal(str)

    def __init__(self):
        super(serial_thread, self).__init__()        
        #threading.Thread.__init__(self)
        self.serial_flag = False
        self.serial_num = ''

    def run(self):
        global send_packet_count

        while True:
            #列出所有可用的串口号    
            port_list = list(serial.tools.list_ports.comports())
            #依次扫描串口

            for c in port_list:
                self.serial_num = c[0]
                print(c[0])
                try:
                    self.signal_stat.emit('正在扫描串口:%s'% c[0])
                except:
                    pass
                try:                    
                    self.ser = serial.Serial(c[0], 115200)
                    self.ser.timeout = 1
                    self.ser.interCharTimeout = 0.1
                    self.ser.write('ap\r\n'.encode())
                    data = self.ser.read(1024)
                    print('rev:',data)
                    if len(data) == 0:
                        self.ser.close()
                        continue
                    strdata = data.decode(encoding='gbk')
                    index = strdata.find('etc_ap') 
                    index_end = strdata[index:].find('\n') 
                    print(index,index_end)
                    if index >= 0 :
                        print('已经找到',strdata[index:index+index_end])
                        try:
                            self.signal_stat.emit('已经找到etc ap 串口号:%s\n %s'% (c[0],strdata[index:index+index_end]))
                        except:
                            pass
                        self.ser.interCharTimeout = 0.01
                        self.ser.timeout = 5
                        self.serial_flag = True
                        while self.serial_flag:
                            try:
                                data = self.ser.readline()
                            except:
                                self.serial_flag = False
                                break
                            if len(data) == 0:
                                # try:
                                #     print("nodata")
                                #     self.signal_1.emit("nodata")
                                # except:
                                #     pass   
                                try:
                                    self.ser.write('ap\r\n'.encode())
                                except:
                                    self.serial_flag = False   
                                    try:
                                        self.signal_stat.emit('etc ap 发送错误 已经关闭 串口号:%s'% (self.serial_num))
                                    except:
                                        pass          
                                continue
                            try:
                                print(data.decode())
                                self.signal_1.emit(data.decode())
                            except:
                                pass
                    else:
                        self.ser.close()
                        continue

                except Exception as ext:
                    print(ext)
                    try:
                        self.ser.close()
                    except:
                        pass
                    continue

            time.sleep(1)  

    def send(self,cmd):
        try:
            self.ser.write(cmd.encode())
        except:
            self.serial_flag = False
            try:
                self.signal_stat.emit('etc ap 发送错误 已经关闭 串口号:%s'% (self.serial_num))
            except:
                pass            
            return False
        return True
                
send_packet_count = 0

spc = 0
st = 0
times = 0
all_sec = 0

def fun_timer():
    global send_packet_count
    global spc
    global st
    global times
    global all_sec

    
    times +=1
    timer = threading.Timer(0.1,fun_timer)
    timer.start()
    if send_packet_count <= 0:
        return

    all_sec += 1
    if spc != send_packet_count:
        st.ser.write("sendgprs200".encode())
        print('send %d %d' % (send_packet_count,int(all_sec/10)))
        times = 0
        spc = send_packet_count
        
    if times > 10*30:
        st.ser.write("sendgprs200".encode())
        print('send %d %d' % (send_packet_count,int(all_sec/10)))
        times = 0        
    
    print(times)


def main():
    global send_packet_count
    global st
    global all_sec
    
    st = serial_thread()
    st.start()

    
#    timer = threading.Timer(0.1,fun_timer)
#    timer.start()
    
    while True:
        strdata = input('>>')
        
        cmd = strdata.split(' ')
        print(cmd)
        if cmd[0] == 'send_sensor':
            st.send('send_sensor')
        elif cmd[0] == 'send_sensor_rp':
            st.send('send_sensor_rp\r\n')
#            all_sec = 0
        if cmd[0] == 'ap':
            st.ser.write((strdata[3:]+'\r\n').encode())

            
if __name__ == '__main__':
    main()


            

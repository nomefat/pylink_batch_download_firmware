import os
import pylink
import operator
import sys
import re
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from main_ui import * 
import time
import my_serial


def jlink_f():
    jlink = pylink.JLink()

    jlink.open('69661582')
    jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
    print(jlink.connect('STM32F429II'))
    print(jlink.core_id())
    #print(jlink.device_family())
    print(jlink.target_connected())
    #print(jlink.erase())
    print(jlink.flash_file('C:\work\etc_project_new_board_v2\MDK-ARM\etc_n1.bin', 0X08004000))
    # jlink.reset()
    # jlink.close()

    firm_data = open('C:\work\etc_project_new_board_v2\MDK-ARM\etc_n1.bin','rb').read()

    read_firm = jlink.code_memory_read(0X08004000,len(firm_data))


    print(operator.eq(firm_data,bytes(read_firm)))

    jlink.reset()
    jlink.close()
version = 'ETC_AP 下载固件和出厂测试工具 V:1.0'


class MainDlg(QDialog):
    signal_1 = pyqtSignal()

    def __init__(self):
        QDialog.__init__(self)

        self.file_list = []
        self.dir_name = ''
        self.file_name = ''
        self.now_file_index = 0
        self.str_log = ''
        self.str_test_log = ''
        self.serial_etc_ap = False
        self.start_test_num = 0
        self.ser = my_serial.serial_thread()
        self.init_ui()
        self.setWindowTitle(version)

    def init_ui(self):
        self.ui = Ui_dialog()
        self.ui.setupUi(self)
        self.ui.pushButton_down_firm.setEnabled(False)
        self.ui.pushButton.clicked.connect(self.slot_btn_find_file_bengin)
        self.ui.pushButton_connect_ap.clicked.connect(self.slot_btn_connect_jlink)
        self.ui.pushButton_down_firm.clicked.connect(self.slot_btn_down_firm)
        self.ui.pushButton_start_test.clicked.connect(self.slot_btn_start_test)
        self.ser.signal_1[str].connect(self.slot_serial_data)
        self.ser.signal_stat[str].connect(self.slot_serial_stat)
        self.ser.start()
        self.signal_1.connect(self.slot_signal_1)

    def slot_serial_data(self,str_data):
        # if len(self.str_log) > 1024*500:
        #     self.str_log = ''
        # self.str_log += str_data
        # self.ui.textBrowser_log.setText(self.str_log)
        real_rev = 0
        rssi = -100
        str_ret = ' Error'
        if str_data.find('enable send ack forever') >=0:
            self.str_test_log += 'etc ap 已经开始测试...\n'
            self.start_test_num = 0
            self.ui.textBrowser_log_1.setText(self.str_test_log)
        elif str_data.find('test_rf2_rev wish') >=0:
            str_real_rev = re.search('real=\d+',str_data)
            str_rssi = re.search('rssi=.\d+',str_data)

            if str_real_rev is not None:
                real_rev = int(str_real_rev.group()[5:])
            if str_rssi is not None:
                rssi = int(str_rssi.group()[5:])  
            if real_rev>95 and rssi > -99:
                str_ret = ' 通过\n'
            else:
                str_ret = ' 失败\n'
            self.str_test_log += str_data + str_ret
            self.ui.textBrowser_log_1.setText(self.str_test_log)
        elif str_data.find('test_rf1_rev wish') >=0:
            str_real_rev = re.search('real=\d+',str_data)
            str_rssi = re.search('rssi=.\d+',str_data)

            if str_real_rev is not None:
                real_rev = int(str_real_rev.group()[5:])
            if str_rssi is not None:
                rssi = int(str_rssi.group()[5:])  
            if real_rev>95 and rssi > -99:
                str_ret = ' 通过\n'
            else:
                str_ret = ' 失败\n'
            self.str_test_log += str_data + str_ret
            self.ui.textBrowser_log_1.setText(self.str_test_log)
        elif str_data.find('etc ap_n1') >= 0:
            self.ser.send('ap\r\n')
            self.ui.lineEdit_gprs.setText('')
            self.ui.lineEdit_gps.setText('')
            self.ui.lineEdit_gprs_gprs_rssi.setText('')
            time.sleep(0.01)
            self.slot_btn_start_test()
        elif str_data.find('etc_ap') >= 0:
            s = ''
            if str_data.find('etc ap 发送错误') >= 0:
                s = 'False:'
                self.serial_etc_ap = False
            elif str_data.find('已经找到etc') >= 0:
                s = 'True:'
                self.serial_etc_ap = True

            self.ui.textBrowser_log_2.setText(s+'已经找到etc ap 串口号:%s\n %s'% (self.ser.serial_num,str_data))            
        elif str_data.find('gprs:') >= 0:
            self.ui.lineEdit_gprs.setText(str_data[5:])
        elif str_data.find('gps:') >= 0:
            self.ui.lineEdit_gps.setText(str_data[4:])
        elif str_data.find('gprs_rssi:') >= 0:
            self.ui.lineEdit_gprs_gprs_rssi.setText(str_data[10:])

    def slot_btn_start_test(self):
        self.start_test_num += 1
        if self.ser.send('syn_forever 10\r\n') is True:
            self.str_test_log = '启动测试:%d\n'% self.start_test_num
            self.ui.textBrowser_log_1.setText(self.str_test_log)
        else:
            self.str_test_log = '启动测试失败，串口不通:%d\n'% self.start_test_num
            self.ui.textBrowser_log_1.setText(self.str_test_log)   

    def slot_serial_stat(self,str_data):
        s = ''
        if str_data.find('etc ap 发送错误') >= 0:
            s = 'False:'
            self.serial_etc_ap = False
        elif str_data.find('已经找到etc') >= 0:
            s = 'True:'
            self.serial_etc_ap = True

        self.ui.textBrowser_log_2.setText(s+str_data)

    def delete_all_log(self):
        self.str_test_log = ''
        self.ui.textBrowser_log_2.setText('')
        self.ui.textBrowser_log_1.setText(self.str_test_log)
        self.ui.textBrowser_log.clear()
        self.ui.lineEdit_gprs.setText('')
        self.ui.lineEdit_gps.setText('')
        self.ui.lineEdit_gprs_gprs_rssi.setText('')
        
    def slot_btn_find_file_bengin(self):
        '''
        响应打开固件的按键，获取指定的文件夹，文件夹下所有的文件名，当前选中的文件以及索引，
            会对所有文件进行排序，必须是 [数字]_ 开头的文件名 才能进行正确的排序，否则不予执行
        '''
        qfd = QFileDialog()
        qfd.setFileMode(QFileDialog.AnyFile)
        if qfd.exec():
            #获取选中的文件名
            filenames = qfd.selectedFiles()   
            #从绝对路径中提取文件名
            self.file_name = filenames[0].split('/')[-1]
            #从绝对路径中提取目录
            self.dir_name = os.path.dirname(filenames[0]) 
            #从目录中提取所有的文件名
            self.file_list = os.listdir(self.dir_name)
            #尝试对文件名list进行排序  如果出错即终止程序
            try:
                self.file_list.sort(key=lambda param:int(param.split('_')[0]))
            except Exception as ext:
                QMessageBox.warning(self, "Error", "固件名排序错误，必须是以[数字]_开头的文件才能排序", QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            #获取选中的文件在文件list中的索引
            self.now_file_index = self.file_list.index(self.file_name)
            self.ui.lineEdit_FirmWare_Path.setText(filenames[0])
            self.ui.lineEdit_FirmWare_Path_Useing.setText(self.file_list[self.now_file_index].split('_')[2])
            self.ui.lineEdit_FirmWare_Firm_Index.setText('已下载%d个' % self.now_file_index) 
            #self.ui.lineEdit_FirmWare_Path_Useing.setText(filenames[0])
            #print(self.dir_name,self.file_list,self.now_file_index,self.file_list[self.now_file_index])
    

    def slot_btn_connect_jlink(self):
        try:
            self.jlink = pylink.JLink()
            jid = '69661582'
            self.jlink.open()
            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)

        except Exception as ext:
            QMessageBox.warning(self, "连接jlink错误", str(ext), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return   

        try:       
            self.jlink.connect('STM32F429II')
            if self.jlink.target_connected() is True:
                self.ui.pushButton_down_firm.setEnabled(True)
                self.ui.pushButton_connect_ap.setText('已连接')
            else:
                QMessageBox.warning(self, "连接目标板错误0", 'jlink 已经链接成功，但是目标板连接失败:', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
        except Exception as ext:
            QMessageBox.warning(self, "连接目标板错误1", 'jlink 已经链接成功，但是目标板连接失败,\nExcept:' + str(ext), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return 
    def slot_btn_down_firm(self):    
        self.delete_all_log()
        self.ui.pushButton_down_firm.setEnabled(False)
        self.signal_1.emit()

    def slot_signal_1(self):
        
        if len(self.file_list) == 0 or self.dir_name == '':
            self.ui.pushButton_down_firm.setEnabled(True)
            QMessageBox.warning(self, "下载固件前 读取固件错误", '必须先选择固件路径', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return            
        try:
            target_id = self.jlink.core_id()
        except:
            self.ui.pushButton_down_firm.setEnabled(False)      
            self.ui.pushButton_connect_ap.setText('连接AP')            
            QMessageBox.warning(self, "下载固件前 读取目标板ID错误", 'jlink已经断开连接', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return             
        
        if target_id == -1:
            self.ui.pushButton_down_firm.setEnabled(False)      
            self.ui.pushButton_connect_ap.setText('连接AP')
            QMessageBox.warning(self, "下载固件前 读取目标板ID错误", '目标板已断开连接', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return 

        str_log = '读取目标板id:%d\n开始下载固件:%s...\n' % (target_id,self.file_list[self.now_file_index])
        self.ui.textBrowser_log.setText(str_log)

        try:
            self.jlink.flash_file(self.dir_name + '/' + self.file_list[self.now_file_index], 0X08000000)
        except Exception as ext:
            self.ui.pushButton_down_firm.setEnabled(False)      
            self.ui.pushButton_connect_ap.setText('连接AP')            
            QMessageBox.warning(self, "下载固件错误", '下载固件,\nExcept:' + str(ext), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return 

        str_log += '下载成功，校验...\n'
        self.ui.textBrowser_log.setText(str_log)        

        firm_data = open(self.dir_name + '/' + self.file_list[self.now_file_index],'rb').read()

        read_firm = self.jlink.code_memory_read(0X08000000,len(firm_data))
        if operator.eq(firm_data,bytes(read_firm)) is True:
            str_log += '校验成功\n请拨动拨码开关重启设备\n'
            self.ui.textBrowser_log.setText(str_log)
            self.now_file_index += 1
            self.ui.lineEdit_FirmWare_Path_Useing.setText(self.file_list[self.now_file_index].split('_')[2])       
            self.ui.lineEdit_FirmWare_Firm_Index.setText('已下载%d个' % self.now_file_index) 
            self.jlink.reset()
        else:
            str_log += '校验失败，需要重新下载 '
            self.ui.textBrowser_log.setText(str_log)
            QMessageBox.warning(self, "下载固件", '校验失败' , QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        self.ui.pushButton_down_firm.setEnabled(True)

app = QtWidgets.QApplication(sys.argv)
main_dlg = MainDlg()
main_dlg.show()

app.exec()


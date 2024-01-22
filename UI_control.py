from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import QTimer,Qt
from PyQt5.QtWidgets import QFileDialog, QDialog,QMessageBox
import Modules.WebParser as parser
from UI.Poster_UI import Ui_RentAutoPoster
from UI.Demo_UI import Demo_ui
from UI.Share_post_UI import  Ui_shared_post
import UI.UI_icon # type: ignore
from PyQt5.QtGui import QImage, QPixmap
from MyQR import myqr
import json
import os

"""將UI轉換成.py檔案指令 :pyuic5  Poster_UI.ui -o Poster_UI.py"""

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() # in python3, super(Class, self).xxx = super().xxx
        self.ui = Ui_RentAutoPoster()
        self.ui.setupUi(self)
        self.setup_control()
        self.parser = parser.web_parser()
        self.all_post={}
        self.sys_info=''
        self.poster_info=''
        self.poster_name=''
        self.poster_phone=''
        self.demo_str=r"""///不需先付押金才能排隊看房
…………………………………………………

{title}

租金：{rent}
類型：{house_kind}
樓層：{floor}
寵物：不可
電費：台水電
車位：已含租金（平面車位)
備註：

詳情請看>>> {detail_url}
⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯"""

    def setup_control(self):
        self.ui.update_poster.clicked.connect(self.update_poser)
        self.ui.add_photo_btn.clicked.connect(self.add_photo)
        self.ui.remove_photo_btn.clicked.connect(self.remove_photo)
        self.ui.update_db.clicked.connect(self.update_db)
        self.ui.post_demo.clicked.connect(self.edit_demo)
        self.ui.titles.currentIndexChanged.connect(self.show_post)
        self.ui.start_btn.clicked.connect(self.set_title_demo_post)
        self.ui.update_post_btn.clicked.connect(self.update_each_post)
        self.ui.photo_btn.clicked.connect(self.show_photo)
        self.ui.output_all_btn.clicked.connect(self.output)
        self.ui.share_btn.clicked.connect(self.share_post)
    
    def update_poser(self):
        """更新聯絡人資訊"""
        poster = self.ui.name.text()
        phone = self.ui.phone.text()
        check_phone =phone.replace('-','') if '-' in phone else phone
        if not check_phone.isdigit():
            self.send_sys_info('phone格式錯誤! 請輸入數字')
            phone='0900-000-000'
        poster_id = self.ui.poster_id_value.text()
        broker = self.ui.broker_name.text()
        broker_id=self.ui.broker_id_value.text()
        lineid = self.ui.LineID_value.text()
        self.poster_info = f"""📲洽詢專線：{phone}\nLine ID ： {lineid}\n⚠️起租日7-10天前再約看\n營業員:{poster} {poster_id}\n經紀人:{broker} {broker_id}\n✨成交時需收取租金50%服務費\n✨歡迎屋主委託、代租、代管"""
        self.ui.text_review_area.setPlainText(self.poster_info)
        self.poster_name=poster
        self.poster_phone=phone
        self.send_sys_info('已更新聯絡人資料')
        self.set_title_demo_post()

    def add_photo(self):
        old_photo_path = self.ui.photo_path.toPlainText()
        filePath , filterType = QtWidgets.QFileDialog.getOpenFileNames()  # 選擇檔案對話視窗
        filePath_str=old_photo_path+'\n'
        for path in filePath:
            filePath_str+=path+'\n'
        self.ui.photo_path.setText(filePath_str)
        self.send_sys_info('成功新增圖片')

    def remove_photo(self):
        old_photo_path = self.ui.photo_path.toPlainText()
        line_index = self.ui.photo_path.textCursor().blockNumber() # 取得所在行數
        lines = old_photo_path.split('\n') #將原本路經分隔成一個一個
        if line_index >= 0 and line_index < len(lines):
            del lines[line_index]
        new_text = '\n'.join(lines)
        self.ui.photo_path.setText(new_text)
        self.send_sys_info('成功移除圖片')
    
    def show_photo(self):
        old_photo_path = self.ui.photo_path.toPlainText()
        line_index = self.ui.photo_path.textCursor().blockNumber() # 取得所在行數
        photo_list = old_photo_path.split('\n')
        photo_path=photo_list[line_index]
        self.review_photo_to_label(photo_path)

    def update_db(self):
        """抓取網頁爬蟲，超過七天的資料會被刪除"""
        timer = QTimer()
        self.send_sys_info('資料庫更新中...請稍後 ')
        timer.start(1500)  #延遲兩秒
        self.parser.parser_service()#重爬網站
        timer.start(2000)  #延遲兩秒
        self.set_title_demo_post()
        self.send_sys_info('租屋資料已更新完畢...')

    def send_sys_info(self,msg):
        """將系統訊息傳送到訊息框內"""
        self.sys_info+=msg+'\n'
        self.ui.sys_info_view.setPlainText(self.sys_info)

    def edit_demo(self):
        def accepted():
            self.demo_str = dialog.ui.post_demo.toPlainText()
            self.send_sys_info('已更新貼文範本')

        def rejected():
            self.send_sys_info('取消更新貼文範本')
        dialog = QDialog()
        dialog.ui = Demo_ui()
        dialog.ui.setupUi(dialog)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.setWindowTitle("編輯範本")
        dialog.setWindowIcon(QtGui.QIcon("./picture/note.png"))
        poster_=self.poster_info if '營業員' not in self.demo_str else ''
        dialog.ui.post_demo.setPlainText(str(self.demo_str+'\n'+poster_))
        dialog.ui.update_demo_btn.accepted.connect(accepted)
        dialog.ui.update_demo_btn.rejected.connect(rejected)
        dialog.exec_()


    def change_font_size(self,dialog, title):
        # 获取标签的宽度
        label_width = dialog.ui.post_title.width()
        # 创建 QFontMetrics 对象，用于计算文本的大小
        font_metrics = QFontMetrics(dialog.ui.post_title.font())
        # 获取原始字体大小
        original_font_size = dialog.ui.post_title.font().pointSize()
        # 循环减小字体大小，直到文本适应标签的宽度为止
        while font_metrics.width(title) > label_width:
            original_font_size -= 2
            font = QFont(dialog.ui.post_title.font())
            font.setPointSize(original_font_size)
            font_metrics = QFontMetrics(font)

        # 根据计算得到的字体大小设置新的字体
        font = QFont(dialog.ui.post_title.font())
        font.setPointSize(original_font_size)
        dialog.ui.post_title.setFont(font)
        # 设置文本
        dialog.ui.post_title.setText(title)

    def share_post(self):
        dialog = QDialog()
        dialog.ui = Ui_shared_post()
        dialog.ui.setupUi(dialog)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.setWindowTitle("分享物件")
        dialog.setWindowIcon(QtGui.QIcon("./picture/note.png"))
        title = self.ui.titles.currentText() #抓取目前物件標題
        if not self.poster_name:
            QMessageBox.warning(self, '提醒', '請先更新聯絡人資料')
            return
        dialog.ui.poser_name.setText(self.poster_name)
        dialog.ui.poster_phton.setText(self.poster_phone)
        data = self.all_post[title]['data']
        self.change_font_size(dialog,title)
        # dialog.ui.post_title.setText(title)
        dialog.ui.address.setText(data[3])
        dialog.ui.rent_cost.setText(data[5]+'元/月')
        dialog.ui.house_kind.setText(data[7])
        detail =''
        for i in range(8,12):
            detail += data[i]+'\n'
        #放物件照片
        dialog.ui.detail_info.setText(detail)
        qpixmap = QPixmap() 
        if qpixmap.load(self.all_post[title]['photo_path']):
            img = qpixmap.scaled(500, 500)
            dialog.ui.post_img.setPixmap(img)
        ###產生 詳細圖片的qrcode
        myqr.run(words = self.all_post[title]['detail_url'], # 可放網址或文字(限英文)
         picture = './UI/icon/logo123.png', 
         level = 'H', # 糾錯水平，預設是H(最高)
         colorized = True, # 背景圖片是否用彩色，True為彩色
         save_name = 'post_qrcode.png') 
        #放網址qrcode圖片
        # 获取当前脚本的路径
        current_path = os.path.dirname(os.path.abspath(__file__))
        # 构建图片文件的相对路径
        qrcode_path = os.path.join(current_path, 'post_qrcode.png')
        # 获取 QLabel 的宽度和高度
        label_width = dialog.ui.qrcode.width()
        label_height = dialog.ui.qrcode.height()

        # 顯示網址 qrcode 圖片
        qpixmap_qr = QPixmap() 
        if qpixmap_qr.load(qrcode_path):
            img_qr = qpixmap_qr.scaled(label_width, label_height, aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
            dialog.ui.qrcode.setPixmap(img_qr)
        dialog.exec_()
    
    def show_post(self):
        """顯示下拉選單的預覽貼文"""
        title = self.ui.titles.currentText()
        each_post =self.all_post[title]['post']
        photo_path=self.all_post[title]['photo_path']
        self.ui.text_review_area.setPlainText(each_post)
        self.ui.photo_path.setText(photo_path)
        self.review_photo_to_label(photo_path)
    
    def review_photo_to_label(self,photo_path):
        #將圖片顯示在標籤
        qpixmap = QPixmap() 
        if qpixmap.load(photo_path):
            img = qpixmap.scaled(400, 400)
            self.ui.show_photo.setPixmap(img)
        else:
            self.send_sys_info(f"无法加载图像：{photo_path}")

    def set_title_demo_post(self):
        """重新設定下選單和所有貼文"""
        titles=[]
        results={}
        try:
            datas = self.parser.get_all_data()
            if datas:
                for data in datas:
                    title= data[2]
                    titles.append(data[2])
                    rent = data[5]
                    house_kind = data[9]
                    floor=data[10]
                    poster_=self.poster_info if '營業員' not in self.demo_str else ''
                    results[title]={
                        'post':self.demo_str.format(title=title,rent=rent,house_kind=house_kind,floor=floor,detail_url=f'https://www.firsthome.tw/Findhouse/Detail/{data[-1]}')+'\n'+poster_,
                        'photo_path':f'./rent_pic/{data[4]}',
                        'detail_url':f'https://www.firsthome.tw/Findhouse/Detail/{data[-1]}',
                        'data':data}
            self.all_post=results
            #將所有物件標題放入下拉選單裡面
            self.ui.titles.addItems(titles)
        except Exception as e:
            print(e)

    def update_each_post(self):
        """更改一篇貼文"""
        post_ = self.ui.text_review_area.toPlainText()
        title = self.ui.titles.currentText()
        self.all_post[title]['post']=post_
        self.send_sys_info(f'已更新--{title}--')

    def output(self):
        demo={'posts':[]}
        for key,item in self.all_post.items():
            demo['posts'].append({'msg':item['post'],'media':item['photo_path']})
        # 将字典保存为文本文件，使用 UTF-8 编码
        with open("post.txt", "w", encoding="utf-8") as file:
            file.write(json.dumps(demo, ensure_ascii=False))
        self.send_sys_info('已將全部貼文匯出~')

        
            



            
        
#################################################################
#这个程序是基于Pyside6的图形用户界面程序
#################################################################

import sys
import cv2
# 导入YOLO模型在Pyside6之前
from ultralytics import YOLO

from PySide6.QtWidgets import QMainWindow, QApplication, QFileDialog

#QImage是中间变量，QPixmap是最终显示在label用户界面上的
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt,QTimer

# 大多数的导包都是人家封装好的类，比如这里导入的就是 PySide6 里面的main_window_ui.py类
from main_window_ui import Ui_MainWindow



# opencv的图像矩阵转换为QImage
def convert2QImage(img):
   height, width, channel = img.shape
   return QImage(img, width, height, width * channel, QImage.Format.Format_BGR888)#yolo用BGR格式


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):#构造函数
        super(MainWindow, self).__init__()
        self.setupUi(self)

        #图像获取按钮的信号与槽绑定
        self.pushButton.clicked.connect(self.get_image_path)

        # 初始化用于目标检测的模型
        self.model = YOLO('yolo11n.pt') #基础模型
        self.model_init()

        #视频检测初始化函数调用
        self.video_init()
        
        # 初始化视频对象
        self.video = None

    

    #视频检测初始化函数
    def video_init(self):
        #视频检测按钮的信号与槽绑定
        self.pushButton_video.clicked.connect(self.get_video_path)
        #创建一个定时器对象并且设置计时间隔
        self.timer = QTimer(self)
        self.timer.setInterval(30) #30ms间隔
        #定时器计数一次之后触发的信号与图像显示函数进行绑定
        self.timer.timeout.connect(self.video_detect)
        # 初始化进度条
        self.horizontalSlider.setEnabled(False)  # 初始禁用
        self.horizontalSlider.setValue(0)         # 初始值设为0
        # 绑定进度条滑块释放事件，实现拖拽控制
        self.horizontalSlider.sliderReleased.connect(self.slider_released)

    # 通用方法：当点击其他的按钮时停止视频检测
    def stop_video_detection(self):
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, 'video') and self.video is not None and self.video.isOpened():
            self.video.release()
            self.video = None
        self.label_orig.clear()
        self.label_det.clear()
        self.horizontalSlider.setEnabled(False)
        self.horizontalSlider.setValue(0)
        
    # 进度条滑块释放时触发，用于跳转视频
    def slider_released(self):
        # 只有在视频播放时才处理
        if hasattr(self, 'video') and self.video is not None and self.timer.isActive():
            # 获取当前滑块位置
            desired_frame = self.horizontalSlider.value()
            # 设置视频跳转到指定帧
            self.video.set(cv2.CAP_PROP_POS_FRAMES, desired_frame)
            # 立即更新一帧
            self.video_detect()

    # 视频选择函数(初始化视频对象并且启动定时器)
    def get_video_path(self):
        print("视频检测")
        
        # 先停止当前可能正在运行的视频检测
        self.stop_video_detection()

        # 获取打开的文件路径，返回值是一个元组，第一个值是文件路径，第二个值是文件类型
        path = QFileDialog.getOpenFileName(filter='*.mp4;*.avi;*.mov')  # filter过滤掉非视频文件

        #索引获取到的第一个元组成员文件路径
        video_path = path[0]
    
        #video_path不为空就是True，要求只能检测视频数据
        if video_path:
            print("开始检测:")
            #打开视频文件
            self.video = cv2.VideoCapture(video_path)
            print(video_path)
            # 获取视频总帧数并设置进度条最大值
            self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
            self.horizontalSlider.setMaximum(self.total_frames)
            self.horizontalSlider.setEnabled(True)  # 启用进度条
            #视频初始化完成之后，启动定时器
            self.timer.start()
        #如果用户没有选择文件则video_path为假，不做检测
        else:
            print("用户没有选择视频")

    # 获取单张视频帧并且检测
    def video_detect(self):
        # 检查视频对象是否有效
        if self.video is None or not self.video.isOpened():
            self.stop_video_detection()
            return
            
        #读取视频帧，第一个参数是布尔值，第二个参数是图像矩阵
        ret, frame = self.video.read()
        #判断是否获取到图像矩阵
        # 如果ret为假则表示读取失败，代表视频读取完了
        if ret:
            #将获取到的文件路径作为检测参数进行检测
            result = self.model(source=frame)

            #原始图像矩阵
            orig_video_arr = result[0].orig_img
            #调用显示函数显示原始图像
            self.image_show(orig_video_arr, self.label_orig)
            
            #检测框图像矩阵
            det_video_arr = result[0].plot()
            #调用显示函数显示检测结果图像
            self.image_show(det_video_arr, self.label_det)

            # 更新进度条（只有在非拖拽状态下才自动更新）
            if not self.horizontalSlider.isSliderDown():
                current_frame = int(self.video.get(cv2.CAP_PROP_POS_FRAMES))
                self.horizontalSlider.setValue(current_frame)
        else:
            print("视频检测完毕")
            self.stop_video_detection()



    # 初始化用于目标检测的模型,通过combox选择不同的模型
    def model_init(self):
        #添加combox的文本信息，模型类别
        self.comboBox.addItem("基础模型")
        self.comboBox.addItem("自训练模型")
        #在combox文本信息添加完成之后，绑定combox的信号与槽函数
        self.comboBox.currentIndexChanged.connect(self.model_changed)
    #模型切换槽函数
    def model_changed(self):
        # 停止可能正在运行的视频检测
        self.stop_video_detection()

        #测试不同条目信息下的页码以及文本信息
        print(f'index:', self.comboBox.currentIndex()) #获取当前模型索引
        print(f'text:', self.comboBox.currentText()) #获取当前模型文本
        #根据不同的索引加载不同的模型
        index = self.comboBox.currentIndex()
        if index == 0:
            self.model = YOLO('yolo11n.pt')  # 基础模型
        elif index == 1:
            self.model = YOLO('runs/detect/train/weights/best.pt')  # 自训练模型



    # 文件访问函数,目标检测test.py当中的source拿到文件路径即可
    def get_image_path(self):
        print("图像检测")

        # 停止可能正在运行的视频检测
        self.stop_video_detection()

        # 获取打开的文件路径，返回值是一个元组，第一个值是文件路径，第二个值是文件类型
        path = QFileDialog.getOpenFileName(filter='*.png;*.jpg;*.bmp')  # filter过滤掉非图像文件
        
        #索引获取到的第一个元组成员文件路径
        image_path = path[0]
        print(image_path)

        #image_path不为空就是True，要求只能检测图像数据
        if image_path:
            print("开始检测:")

            #将获取到的文件路径作为检测参数进行检测
            result = self.model(source=image_path)

            #原始图像矩阵
            orig_img_arr = result[0].orig_img
            #调用显示函数显示原始图像
            self.image_show(orig_img_arr, self.label_orig)

            #检测框图像矩阵
            det_img_arr = result[0].plot()
            #调用显示函数显示检测结果图像
            self.image_show(det_img_arr, self.label_det)

        #如果用户没有选择文件则image_path为假，不做检测
        else:
            print("用户没有选择图像")
            
    # 图像显示函数需要传入图像矩阵以及画布，两转一剪
    def image_show(self, img_arr, place):
        # 1.矩阵转换为QImage
        qimage = convert2QImage(img_arr)

        # 2.QImage转换为QPixmap
        qpixmap = QPixmap.fromImage(qimage)

        # 3.裁剪将QPixmap格式图像依照画布进行裁剪
        img_qpixmap = qpixmap.scaled(place.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        # 将裁剪好的QPixmap格式图像显示在原始label上
        place.setPixmap(img_qpixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()
    
    app.exec()  # 事件循环机制，可以实现非阻塞的的死循环，途中可以实现其余操作还能显示出来
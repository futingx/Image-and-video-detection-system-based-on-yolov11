
from ultralytics import YOLO
model = YOLO('yolo11n.pt')

#模型训练需要指定参数
#1 data参数:参与模型训练的数据集路径
#2 epochs参数:训练的轮次设置为50即可
#3 workers:数据加载的工作多线程数量设置建议为0
if 0:
    model.train(
        data='bvn.yaml', 
        epochs=50, 
        workers=0
    )
else:
    #重新初始化模型，调用自己训练好的模型进行视频或者图像检测
    model = YOLO('runs/detect/train/weights/best.pt')
    model(source='datasets/BVN.mp4', show=True, save=True)

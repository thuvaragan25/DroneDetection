from flask import Flask, render_template, request, jsonify
import os
import torch
import cv2

model = torch.hub.load('ultralytics/yolov5', 'custom', 'MachineLearning/model.onnx')

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def dronedetection():
    if request.method == 'GET':
        return render_template('main.html')
    elif request.method == 'POST':        
        imagefile = request.files['imagefile']
        image_path = "./static/storage/" + imagefile.filename

        if imagefile.filename == '':
            return render_template('main.html')

        imagefile.save(image_path)

        image = cv2.imread(image_path)
        resize_proportion = 1.2
        image = cv2.resize(image, None, fx=resize_proportion, fy=resize_proportion)

        blob = torch.from_numpy(cv2.dnn.blobFromImage(image, 1/255, (640, 640), (0, 0, 0), True, crop=False))

        model.eval()
        outs = model.forward(blob)
        outs = outs.cpu().detach().numpy()

        confidences = []
        boxes = []

        xf = image.shape[1] / 640
        yf = image.shape[0] / 640

        for out in outs:
            for detection in out:
                confidence = detection[4]
                if confidence > 0.50:

                    center_x = int(detection[0])
                    center_y = int(detection[1])

                    x = int((center_x - (detection[2] / 2)) * xf)
                    y = int((center_y - (detection[3] / 2)) * yf)

                    w = int(detection[2] * xf)
                    h = int(detection[3] * yf)

                    boxes.append([x, y, w, h])
                    confidences.append(confidence)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        for i  in indexes:
            x, y, w, h = boxes[i]
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        resize_proportion = 0.5
        image = cv2.resize(image, None, fx=resize_proportion, fy=resize_proportion)
        cv2.imwrite(image_path, image)
        return render_template("main.html", image_loc=imagefile.filename)
    else:
        raise Exception("Must be GET or POST request.")

@app.route('/delete_pictures', methods=['POST'])
def delete_pictures():
    folder = 'static/storage'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        os.remove(file_path)
    return jsonify({})

if __name__=="__main__": 
    app.run(port=5000, debug=True)
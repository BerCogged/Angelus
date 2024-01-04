import cv2
import numpy as np
import os
import tensorflow as tf
import socket
import pickle
import struct
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder
from object_detection.utils import config_util
import threading

@tf.function
def detect_fn(image):
    image, shapes = detection_model.preprocess(image)
    prediction_dict = detection_model.predict(image, shapes)
    detections = detection_model.postprocess(prediction_dict, shapes)
    return detections

def send_frames(image_np_with_detections,client_socket):
    a = pickle.dumps(image_np_with_detections)
    message = struct.pack("Q", len(a)) + a
    client_socket.sendall(message)

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
data_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = '192.168.1.8'
print('Host IP:', host_ip)
port = 1055
port2= 1077
socket_address = (host_ip, port)
data_address = (host_ip, port2)

server_socket.bind(socket_address)
data_socket.bind(data_address)

TF_RECORD_SCRIPT_NAME = 'generate_tfrecord.py'
LABEL_MAP_NAME = 'label_map.pbtxt'

paths = {
    'CHECKPOINT_PATH': os.path.join('zavrseni modeli', 'model jaje'),
 }

files = {
    'PIPELINE_CONFIG': os.path.join('zavrseni modeli', 'model jaje', 'pipeline.config'),
    'LABELMAP': os.path.join('zavrseni modeli', 'model jaje', 'label_map.pbtxt')
}

configs = config_util.get_configs_from_pipeline_file(files['PIPELINE_CONFIG'])
detection_model = model_builder.build(model_config=configs['model'], is_training=False)

ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(os.path.join(paths['CHECKPOINT_PATH'], 'ckpt-31')).expect_partial()


category_index = label_map_util.create_category_index_from_labelmap (files['LABELMAP'])
cap = cv2.VideoCapture(0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

server_socket.listen(5)
data_socket.listen(5)
print("LISTENING AT: ",socket_address)
print("LISTENING AT: ",data_address)
client_socket, addr = server_socket.accept()
client_data, addr2 = data_socket.accept()
print('GOT CONNECTION FROM: ', addr)
print('GOT CONNECTION FROM: ', addr2)
ko=0
while cap.isOpened():
    ret, frame = cap.read()
    image_np = np.array(frame)
    if image_np is not None:

        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections = detect_fn(input_tensor)
        if detections is not None :
            num_detections = int(detections.pop('num_detections'))
            detections = {key: value[0, :num_detections].numpy()
                              for key, value in detections.items()}
            detections['num_detections'] = num_detections

            detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

            label_id_offset = 1
            image_np_with_detections = image_np.copy()

            viz_utils.visualize_boxes_and_labels_on_image_array(
                image_np_with_detections,
                detections['detection_boxes'],
                detections['detection_classes'] + label_id_offset,
                detections['detection_scores'],
                category_index,
                use_normalized_coordinates=True,
                max_boxes_to_draw=1,
                min_score_thresh=.7,
                agnostic_mode=False)
            '''
            a = pickle.dumps(image_np_with_detections)
            message = struct.pack("Q", len(a)) + a
            client_socket.sendall(message)
            '''
            client_thread = threading.Thread(target=send_frames, args=(image_np_with_detections, client_socket))
            client_thread.start()
            cv2.imshow("Detections",image_np_with_detections)


            min_score_thresh = .7
            threshold = 0.5
            max_scores = max(detections['detection_scores'])
            for i in range(num_detections):
                box = detections['detection_boxes'][i]
                score = detections['detection_scores'][i]
                if score > .7:
                    ymin, xmin, ymax, xmax = box.tolist()
                    pos = ymin + ymax + xmax + xmin
                    print("POS:", pos)
                    print("KO: ",ko)

                    x = abs(pos-ko)
                    print(x)
                    if x>0.05:
                        print("Poslato")
                        client_data.send(str(5).encode())
                        ko = pos
                    else :
                        print("nije poslato")
                        ko = pos
                else :
                    client_data.send(str(0).encode())
        if cv2.waitKey(10) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            client_socket.close()
            client_data.close()
            break
import json
import time

from SocketServer.type_definitions import HoloLens2PVImageData, HoloLens2SensorData
from SocketServer.StreamServer import StreamServer
# import track_object
import cv2
import numpy as np


# from handtracker.module_SARTE import HandTracker


# track_hand = HandTracker()

def processing_loop(client_obj):
    while True:
        if client_obj.quit_event.is_set():
            # 주의: quit_event가 set되면, 아직 처리하지 않은 frame이 있어도 종료된다.
            break
        try:
            pv_frame: HoloLens2PVImageData = client_obj.get_latest_pv_frame()  # 프레임 손실, delay 적음
            # pv_frame:HoloLens2SensorData = client_obj.get_oldest_pv_frame()  # 프레임 무손실, delay 더 큼
            # print(pv_frame.frameID)
            # flip input array on y-axis
            input = pv_frame.data

            cv2.imshow("pv", input)
            cv2.waitKey(1)

            result_object = None  # track_object.Process(input)
            result_hand = None  # track_hand.Process(input)

            ### set sample hand pose ###
            result_hand = []
            sample_uvd = np.ones((21, 3), dtype=np.float32)
            result_hand.append(sample_uvd)

            """ Packing data for sending to hololens """
            resultData = dict()
            resultData['frameInfo'] = pv_frame.encode_frame_info()
            resultData['objectDataPackage'] = encode_object_data(result_object)
            resultData['handDataPackage'] = encode_hand_data(result_hand)

            # with open("C:/Woojin/research/sample.json", "w") as json_file:
            #     json.dump(resultData, json_file)
            """ Send data """
            resultBytes = json.dumps(resultData).encode('utf-8')
            # print("bytes of total : {}".format(len(resultBytes)))
            try:
                client_obj.socket.send(resultBytes)
                # print("bytes sended")
            except Exception as e:
                # print(e)
                pass
            # time.sleep(0.1) # 10Hz, 테스트용 처리시간.

        except IndexError as e:
            # empty deque
            pass


def encode_hand_data(hand_result):
    """ Encode hand data to json format """

    """ Example """
    """
    handDataPackage['joints_0']
    handDataPackage['joints_1']
    if the hand is not detected, returns zero value joints 
    
    currently consider single hand
    """
    handDataPackage = dict()
    joints = list()
    num_joints = 21

    for joint_uvd in hand_result:
        for id in range(num_joints):
            joint = dict()
            joint['id'] = int(id)
            joint['u'] = float(joint_uvd[id, 0])
            joint['v'] = float(joint_uvd[id, 1])
            joint['d'] = float(joint_uvd[id, 2])
            joints.append(joint)
        break
    handDataPackage['joints'] = joints

    # print(joints)

    return handDataPackage


def encode_object_data(object_result):
    """ Example """
    num_obj = 3
    objectDataPackage = dict()

    objects = list()
    for obj_id in range(num_obj):
        objectInfo = dict()
        keyPoints = list()
        for kpt_id in range(8):
            keyPoint = dict()
            keyPoint['id'] = kpt_id
            keyPoint['x'] = 0.123
            keyPoint['y'] = 0.456
            keyPoint['z'] = 0.789
            keyPoints.append(keyPoint)

        objectInfo['keypoints'] = keyPoints
        objectInfo['id'] = obj_id
        objects.append(objectInfo)

    objectDataPackage['objects'] = objects

    return objectDataPackage


if __name__ == '__main__':
    server = StreamServer()

    server.listening('', 9091, processing_loop)

    # processing thread 시작

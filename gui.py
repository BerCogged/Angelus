import customtkinter as ck
from PIL import Image, ImageTk
import cv2
import imutils
import threading
import socket
import struct
import pickle

class App:
    def __init__(self,window,window_title):
        self.window=window
        self.window.title(window_title)


        self.vid = cv2.VideoCapture(0)
        self.vid.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.frame1= ck.CTkFrame(master=window)
        self.frame1.pack(pady=20,padx=60,fill="both",expand=True)

        self.label = ck.CTkLabel(master=self.frame1, text="Angelus", font=("Roboto",30))
        self.label.pack(pady=12,padx=10)

        self.con = ck.CTkLabel(master=self.frame1, text="NOT CONNECTED", font=("Roboto", 20))
        self.con.pack(padx=10)

        self.host_ip = '192.168.1.8'

        self.videoframe=ck.CTkCanvas(master=self.frame1)
        self.videoframe.pack(pady=30,padx=70)

        self.text = ck.CTkLabel(master=self.frame1, text="Host IP: ", font=("Roboto",24), anchor="nw")
        self.text.pack(pady=12,padx=10)

        self.text2 = " "

        self._, self.start_frame = self.vid.read()

        self.start_frame = imutils.resize(self.start_frame, width=500)
        self.start_frame = cv2.cvtColor(self.start_frame, cv2.COLOR_BGR2GRAY)
        self.start_frame = cv2.GaussianBlur(self.start_frame, (21, 21), 0)

        self.alarm = False
        self.alarm_mode = False
        self.alarm_counter = 0

        self.button = ck.CTkButton(master=self.frame1, text="START", command=self.start)
        self.button.pack(pady=12,padx=12)

        self.press = ck.CTkLabel(master =self.frame1, text="press START to connect", font=("Roboto",18), anchor="nw")
        self.press.pack(pady=12,padx=12)

        self.slider = ck.CTkSlider(master=self.frame1, from_=0, to=5000, command=self.update_thresh)
        self.slider.pack(pady=12,padx=12)

        self.slider_text = ck.CTkLabel(master= self.frame1, text="TURN LEFT FOR MORE SENSITIVITY", font = ("Roboto",15), anchor="nw")
        self.slider_text.pack(pady=12,padx=12)
        self.diff = 2500

        self.window.mainloop()

    def update_thresh(self,value):
        self.diff = value

    def start(self):
        self.text2 = self.button.cget("text")
        if self.text2 == "START":
            self.text.configure(text="HOST IP: " + self.host_ip)
            client_thread = threading.Thread(target=self.connect)
            client_thread.start()
            self.button.configure(text="STOP")
            self.text2 = self.button.cget("text")
        else:
            self.window.destroy()
            self.button.configure(text="START")

    def connect(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 1055
        port2 = 1077
        socket_address = (self.host_ip, port)
        data_address = (self.host_ip, port2)

        server_socket.bind(socket_address)
        data_socket.bind(data_address)
        server_socket.listen(5)
        data_socket.listen(5)

        print("LISTENING AT: ", socket_address)
        print("LISTENING AT: ", data_address)
        client_socket, addr = server_socket.accept()
        client_data, addr2 = data_socket.accept()
        print('GOT CONNECTION FROM: ', addr)
        print('GOT CONNECTION FROM: ', addr2)
        self.con.configure(text="CONNECTED")
        self.press.configure(text="press STOP to exit")
        self.update_frame(client_socket,client_data)


    def alarm_data(self,client_data):
        _, frame2 = self.vid.read()
        frame2 = imutils.resize(frame2, width=500)
        if self.alarm_mode:
            frame_bw = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            frame_bw = cv2.GaussianBlur(frame_bw, (5, 5), 0)

            difference = cv2.absdiff(frame_bw, self.start_frame)
            threshold = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)[1]
            self.start_frame = frame_bw
            if threshold.sum() > self.diff:
                self.alarm_counter += 1
                data_thread = threading.Thread(target=self.moves, args=(client_data,))
                data_thread.start()
            else:
                if self.alarm_counter > 0:
                    self.alarm_counter -= 1
            notmoving = threading.Thread(target=self.not_moving,args=(client_data,))
            notmoving.start()
        if self.alarm_counter > 10:
            if not self.alarm:
                self.alarm = True
        self.alarm_mode = not self.alarm_mode
        self.alarm_counter = 0

    def update_frame(self,client_socket,client_data):
        ret, frame = self.vid.read()
        socket_thread = threading.Thread(target=self.send_frame, args=(frame,client_socket))
        socket_thread.start()
        alarm_thread = threading.Thread(target=self.alarm_data, args=(client_data,))
        alarm_thread.start()
        if self.text2 == "STOP":
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            img_tk = ImageTk.PhotoImage(image=img)
            self.videoframe.img = img_tk
            self.videoframe.create_image(0, 0, anchor=ck.NW, image=img_tk)
        self.window.after(10, lambda: self.update_frame(client_socket,client_data))


    def moves(self, client_data):
        client_data.send(str(5).encode())

    def not_moving(self, client_data):
        client_data.send(str(0).encode())

    def send_frame(self,frame,client_socket):
        a = pickle.dumps(frame)
        message = struct.pack("Q", len(a)) + a
        client_socket.sendall(message)

    def __del__(self):
        self.vid.release()

ck.set_appearance_mode('dark')
ck.set_default_color_theme('dark-blue')

root = ck.CTk()
root.geometry("900x700")
app=App(root,"Angelus")
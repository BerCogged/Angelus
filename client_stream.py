from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.image import Image
from kivymd.uix.label import MDLabel
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivymd.uix.dialog import MDDialog
from kivy.clock import mainthread
from playsound import playsound
import threading
import socket
import cv2
import pickle
import struct
from datetime import datetime

class Angelus(MDApp):
    def build(self):
        layout = MDBoxLayout(orientation='vertical')
        self.theme_cls.theme_style = "Dark"
        self.text = "CONNECT"
        self.image = Image(size_hint=(1, 1),  pos=(0, 2))
        self.moved_text = self.moved_text3 = self.moved_text4 =self.moved_text5 = self.moved_text6 = 'Did not moved yet'
        layout.add_widget(self.image)
        self.label = MDLabel(
            text=self.text,
            adaptive_height=True,
            halign='center', valign='middle'
        )
        layout.add_widget(self.label)
        self.label2 = MDLabel(
            text = self.moved_text,
            adaptive_height = True,
            halign='center', valign='middle'
        )
        self.label3 = MDLabel(
            text = self.moved_text3,
            adaptive_height = True,
            halign='center', valign='middle'
        )
        self.label4 = MDLabel(
            text = self.moved_text4,
            adaptive_height = True,
            halign='center', valign='middle'
        )
        self.label5 = MDLabel(
            text=self.moved_text5,
            adaptive_height=True,
            halign='center', valign='middle'
        )
        self.label6 = MDLabel(
            text = self.moved_text6,
            adaptive_height = True,
            halign='center', valign = 'middle'
        )
        self.button = MDRaisedButton(
            text="HISTORY",
            on_release=lambda *args: self.show_history(),
            halign = 'center',
            valign= "center"
        )

        self.dialog = MDDialog(
            title='History',
            md_bg_color=self.theme_cls.bg_dark,
            size_hint=(0.8, None),
            height=500,
            auto_dismiss=True,
            buttons=[
                MDRaisedButton(
                    text="ClOSE",
                    on_release=lambda *args: self.close()
                ),
            ],
        )

        layout.add_widget(self.button)
        self.i = 1
        self.counter = 0
        self.data = b""
        self.payload_size = struct.calcsize("Q")
        self.hic = 0
        self.content = MDBoxLayout(orientation='vertical', spacing='12dp', padding='12dp')
        Clock.schedule_once(lambda dt: self.show_popup(), 0)

        return layout

    def sound(self):
        threading.Thread(target=self.play_sound_thread).start()

    def play_sound_thread(self):
        playsound('zvukovi/zvuk2.MP3')

    def show_history(self):
        self.content = MDBoxLayout(orientation='vertical', spacing='12dp', padding='12dp')
        self.content.add_widget(self.label2)
        self.content.add_widget(self.label3)
        self.content.add_widget(self.label4)
        self.content.add_widget(self.label5)
        self.content.add_widget(self.label6)
        self.dialog = MDDialog(
            title='History',
            md_bg_color=self.theme_cls.bg_dark,
            size_hint=(0.8, None),
            height=400,
            auto_dismiss=False,
            buttons=[
                MDRaisedButton(
                    text="ClOSE",
                    on_release=lambda *args: self.close()
                ),
            ],
        )
        self.dialog.add_widget(self.content)
        self.dialog.open()
        self.hic = 1

    def close(self):
        self.content.remove_widget(self.label2)
        self.content.remove_widget(self.label3)
        self.content.remove_widget(self.label4)
        self.content.remove_widget(self.label5)
        self.content.remove_widget(self.label6)
        self.dialog.remove_widget(self.content)
        self.dialog.dismiss()

    def show_popup(self):
        content = MDBoxLayout(orientation='vertical', spacing='12dp', padding='12dp')

        text_field = MDTextField(
            size_hint = (0.84, None)
        )
        content.add_widget(text_field)

        dialog = MDDialog(
            title='Enter your IP',
            md_bg_color=self.theme_cls.bg_dark,
            size_hint=(0.8, None),
            height=200,
            auto_dismiss=False,
            buttons=[
                MDRaisedButton(
                    text="CONNECT",
                    on_release=lambda *args: self.on_ok(dialog, text_field.text)
                ),
            ],
        )

        dialog.add_widget(content)
        dialog.open()


    def on_ok(self, dialog, text):
        self.host_ip = text
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.host_ip = '192.168.1.8'
        self.port = 1055
        self.port2 = 1077
        self.client_socket.connect((self.host_ip, self.port))
        self.data_socket.connect((self.host_ip, self.port2))
        Clock.schedule_interval(lambda dt: self.update_frame(self.client_socket), 1.0 / 30.0)
        Clock.schedule_interval(lambda dt: self.update_data(self.data_socket), 1 / 2)
        dialog.dismiss()

    def update_frame(self, dt):

        while len(self.data) < self.payload_size:
            packet = self.client_socket.recv(4 * 1024)
            if not packet: break
            self.data += packet
        packet_msg_size = self.data[:self.payload_size]
        self.data = self.data[self.payload_size:]
        msg_size = struct.unpack("Q", packet_msg_size)[0]

        while len(self.data) < msg_size:
            self.data += self.client_socket.recv(4 * 1024)
        frame_data = self.data[:msg_size]
        self.data = self.data[msg_size:]

        frame = pickle.loads(frame_data)

        buffer = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture = texture

    def update_data(self, dt):
        data2 = str(self.data_socket.recv(1024).decode())
        self.counter= self.counter +1
        print(data2[0])
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        if self.i == 1 and data2[0] == "5":
            self.label2.text = "Moved at: " + current_time
            self.i=2
        elif self.i == 2 and data2[0] == "5":
            self.label3.text = "Moved at: " + current_time
            self.i=3
        elif self.i == 3 and data2[0] == "5":
            self.label4.text = "Moved at: " + current_time
            self.i=4
        elif self.i==4 and data2[0] == "5":
            self.label5.text = "Moved at: " + current_time
            self.i=5
        elif self.i==5 and data2[0] == "5":
            self.label6.text = "Moved at: " + current_time
            self.i=1
        if self.counter == 1:
            self.label.text = "CONNECTED"
            self.label.size_hint_x = None
            self.label.width = self.label.texture_size[0]
            data2 = []
        elif data2[0] == "5":
            self.label.text = "MOVED AT: " + current_time
            self.label.size_hint_x = None
            self.label.width = self.label.texture_size[0]
            data2 = []
            self.sound()


Angelus().run()
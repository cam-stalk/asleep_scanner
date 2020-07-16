#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import socket

from io import BytesIO
from PIL.Image import Image
from av.packet import Packet
from av.logging import set_level
from av.codec.context import CodecContext

from dvrip.monitor import Stream
from dvrip.ptz import PTZButton
from dvrip.io import DVRIPClient
from dvrip.errors import DVRIPRequestError

from strongtyping.strong_typing import match_typing


Status = {
		None: 0,
		'Wrong password': -1,
		'Banned': 2
	}


class XMEye:
	def __init__(self, ip, port):
		self.model = ''
		self.ip = ip
		self.port = port
		self.login = None
		self.password = None
		self.channels_count = 0
		self.status = 0
		set_level(1)

	@match_typing
	def auth(self, login: str, password: str):
		global Status

		self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.Socket.settimeout(4)
		self.conn = DVRIPClient(self.Socket)
		log_in = self.conn.connect((self.ip, self.port), login, password)
		self.status = Status[log_in]

		if self.status is Status[None]:
			self.login = login
			self.password = password
			self.sys_info()
			print(self.model)

	@match_typing
	def get_snapshot(self, ch: int):
		self.codec_264 = CodecContext.create("h264", "r")
		while True:
			try:
				self.Socket2 = socket.create_connection((self.ip, self.port), 6)
				h264 = self.conn.monitor(self.Socket2, channel=ch, stream=Stream.HD)
				break
			# баг в либе [TODO]
			except DVRIPRequestError:
				continue

		data = b''
		while True:
			# Ln76 adds \xff\xd9 for each chunk / frame :c
			if len(data) > 550000: # ~ HD
				break
			if chunk := h264.read(1024):
				data += chunk

		frame = self.codec_264.decode(Packet(data))
		jpeg = BytesIO()
		frame[0].to_image().save(jpeg, format='JPEG')
		# if ch == self.channels_count:
		# 	self.conn.logout()
		# 	self.Socket.close()
		return jpeg.getvalue()

	def sys_info(self):
		info = self.conn.systeminfo()
		self.channels_count = int(info.videoin)
		self.model = f'{info.chassis}_{info.board}'
		try:
			ptz = self.conn.button(channel=0, button=PTZButton.MENU)
		except DVRIPRequestError:
			ptz = None
		if int(info.audioin) > 0 and ptz is None:
			self.model = f'{self.model}-Sound'
		elif ptz is not None:
			self.model = f'{self.model}-PTZ'
		return


#	def debug(self):
#		self.conn.keepalive()


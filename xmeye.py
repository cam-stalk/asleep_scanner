#!/usr/bin/env python3.8
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





class XMEye:
	def __init__(self, ip=None, port=None):
		self.model = ''
		self.ip = ip
		self.port = port
		self.login = None
		self.password = None
		self.channels_count = 0
		self.status = None
		self.Socket = None
		self.Socket2 = None
		self.conn = None
		self.codec_264 = CodecContext.create("h264", "r")
		self.status_enum = {
							None: 0,
							'Wrong password': -1,
							'Banned': 2
							}
		set_level(1)

	@match_typing
	def auth(self, login: str, password: str):
		self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn = DVRIPClient(self.Socket)
		self.Socket.settimeout(4)
		try:
			log_in = self.conn.connect((self.ip, self.port), login, password)
			self.status = self.status_enum[log_in]
		except:
			return -1
		finally:
			self.Socket.close()

		if self.status is self.status_enum[None]:
			self.login = login
			self.password = password
			self.sys_info()
			print([self.ip, self.model])

	@match_typing
	def get_snapshot(self, ch: int):
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
			# if len(data) > 54000: # ~ SD
			# 	break
			if chunk := h264.read(1024):
				data += chunk
			if len(chunk) < 1024:
				break

		frame = self.codec_264.decode(Packet(data))
		jpeg = BytesIO()
		frame[0].to_image().save(jpeg, format='JPEG')
		self.Socket2.close()
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


	def logout(self):
		if self.Socket:
			self.Socket.close()
		if self.Socket2:
			self.Socket2.close()

#	def debug(self):
#		self.conn.keepalive()


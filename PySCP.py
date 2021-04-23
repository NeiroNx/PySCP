#!/usr/bin/env python3
#
#	PySCP, Copyrights Vishnu Shankar B, NeiroN
#
#	List of Tk extensions used:
#		Arc theme (modified to red color and more styles were added) : https://wiki.tcl.tk/48689
#		TkDND : https://sourceforge.net/projects/tkdnd/
#

from locale import getdefaultlocale
import os
from os import listdir
from os.path import isfile, join, expanduser
import json
from datetime import datetime
import threading
import queue
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import PhotoImage
from tkinter import messagebox
from FTP_controller import *
from SFTP_controller import *
from TkDND_wrapper import *
import platform

if(platform.system() == 'Windows'):
	from ctypes import windll

sort_func = {
	"name":lambda x: ' '.join(x.split()[8:]).upper(),
	"size":lambda x: int(x.split()[4])if len(x.split()[4]) else 0,
	"date":lambda x: datetime.strptime(' '.join(x.split()[5:8]),"%d %b %H:%M").timestamp(),
	"rights":lambda x: x.split()[0],
}

#Function to get all removable mountpoints attached to the computer
def get_mounts():
	mountpoints = []	
	if(platform.system() == 'Linux'):
		f = open('/proc/mounts')
		dev_types = ['/dev/sda', '/dev/sdc', '/dev/sdb', '/dev/hda', '/dev/hdc', '/dev/hdb', '/dev/nvme']
		for line in f:
			details = line.split()
			if(details[0][:-1] in dev_types):
				if(details[1] != '/boot/efi'):
					details_decoded_string = bytes(details[1], "utf-8").decode("unicode_escape")
					mountpoints.append(details_decoded_string)
		f.close()
	elif(platform.system() == 'Darwin'):
		for mountpoint in os.listdir('/Volumes/'):
			mountpoints.append('/Volumes/' + mountpoint)
	elif(platform.system() == 'Windows'):
		bitmask = windll.kernel32.GetLogicalDrives()
		mountpoints = ["{}:\\".format(v) for k,v in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ') if bitmask&(1<<k)]
	return mountpoints

def center_window(master_window, child_window, x_offset = None, y_offset = None):
		if x_offset!=None:
			x = master_window.winfo_rootx()
			y = master_window.winfo_rooty()
			main_height = master_window.winfo_height()
			main_width = master_window.winfo_width()
			geom = '+%d+%d' % (x+(main_width/2) - x_offset, y+(main_height/2) - y_offset)
			child_window.geometry(geom)
		else:
			#center the window
			child_window.withdraw()
			child_window.update()
			x = master_window.winfo_rootx()
			y = master_window.winfo_rooty()
			main_height =master_window.winfo_height()
			main_width = master_window.winfo_width()
			window_height = child_window.winfo_reqheight()
			window_width = child_window.winfo_reqwidth()
			geom = '+%d+%d' % ((x + main_width//2 - window_width//2), (y + main_height//2 - window_height//2))  
			child_window.geometry(geom)
			child_window.deiconify()

class PanelButton(ttk.Label):
	def __init__(self, parent, name, icon, path, command):
		#Save reference to path and function
		self.path = path
		self.path_function = command
		#Create the label
		super().__init__(parent, text = name, image = icon, compound = 'left')
		super().pack(side = 'top', pady = 3, padx = 3, fill = X)
		#Bind events
		super().bind('<Button-1>', lambda path: self.path_function(self.path))
		super().bind('<Enter>', self.hover)
		super().bind('<Leave>', self.leave)

	def hover(self, event):
		super().configure(background = '#cfd6e6')
	
	def leave(self, event):
		super().configure(background = '#f5f6f7')

class ToolbarButton(ttk.Label):
	#Custum button class that uses the 'Label' widget
	def __init__(self, parent, image, image_hover, command):
		#Save reference to icon
		self.icon = image
		self.hover_icon = image_hover
		#save reference to the function
		self.command = command
		#Create the label
		super().__init__(parent, image = self.icon)
		#Bind events
		super().bind('<Enter>', self.hover)
		super().bind('<Leave>', self.left)
		super().bind('<Button-1>', self.click)

	def click(self, event):
		super().configure(image = self.icon)
		if self.command!=None: self.command()
		super().configure(image = self.hover_icon)

	def hover(self, event):
		super().configure(image = self.hover_icon)

	def left(self, event):
		super().configure(image = self.icon)

class AboutDialog:
	def __init__(self, master, Title, icon, software_version, author):
		#Change to script's directory
		abspath = os.path.abspath(__file__)
		dname = os.path.dirname(abspath)
		os.chdir(dname)

		os_name = platform.system() + ' ' + platform.release() 

		#Load icons
		if(platform.system() == 'Linux'):
			self.os_icon = PhotoImage(file=join(dname,'Icons','linux_large.png'))
		elif(platform.system() == 'FreeBSD'):
			self.os_icon = PhotoImage(file=join(dname,'Icons','freebsd_large.png'))
		elif(platform.system() == 'Darwin'):
			self.os_icon = PhotoImage(file=join(dname,'Icons','darwin_large.png'))
		elif(platform.system() == 'Windows'):
			self.os_icon = PhotoImage(file=join(dname,'Icons','windows_large.png'))

		python_version = 'python v' + platform.python_version()
		if(sys.maxsize > (2**31-1)):
			python_version += ' (64 bit)'
		else:
			python_version += ' (32 bit)'

		message = software_version + '\n' +  python_version + '\n' + os_name +'\n' + author

		#Create a new dialog box window
		self.about_dialog_window = Toplevel()

		#Make it non-resizeble, set title
		self.about_dialog_window.resizable(False, False)
		self.about_dialog_window.title(Title)

		#Create frames 
		self.icon_frame = ttk.Frame(self.about_dialog_window)
		self.icon_frame.pack(side = 'left', fill = Y)
		self.entry_frame = ttk.Frame(self.about_dialog_window)
		self.entry_frame.pack(side = 'left', fill = Y)
		self.os_icon_frame = ttk.Frame(self.about_dialog_window)
		self.os_icon_frame.pack(side = 'left', fill = Y)

		#Create the label showing main icon
		ttk.Label(self.icon_frame, image = icon).pack(padx = 3, pady = 3)

		#Create the label
		ttk.Label(self.entry_frame, text = message, anchor = 'w').pack(padx = 3, fill = X, expand = True)

		#Create the label showing os icon
		ttk.Label(self.os_icon_frame, image = self.os_icon).pack(padx = 3, pady = 3)

		#Create buttons
		self.rename_ok_button = ttk.Button(self.entry_frame, text = _('OK'), command = self.destroy)
		self.rename_ok_button.pack(pady = 3, padx = 3 )

		#center the window
		if(platform.system() == 'Windows'):
			center_window(master, self.about_dialog_window, 135, 68)
		else:
			center_window(master, self.about_dialog_window)

		#Prevent new task in taskbar
		self.about_dialog_window.transient(master)  

		#Focus on the dialog box, freeze controll of main window
		self.about_dialog_window.focus_force()
		while True:
			try:
				self.about_dialog_window.grab_set()
				break
			except: continue

	def destroy(self):
		self.about_dialog_window.destroy()

class WarningDialog:
	def __init__(self, master, Title, func_command, icon, message):
		#Create a new dialog box window
		self.warning_dialog_window = Toplevel(master)

		#Make it non-resizeble, set title
		self.warning_dialog_window.resizable(False, False)
		self.warning_dialog_window.title(Title)

		#Create frames 
		self.icon_frame = ttk.Frame(self.warning_dialog_window)
		self.icon_frame.pack(side = 'left', fill = Y)
		self.entry_frame = ttk.Frame(self.warning_dialog_window)
		self.entry_frame.pack(side = 'left', fill = Y)

		#Create the label showing rename icon
		ttk.Label(self.icon_frame, image = icon).pack()

		#Create the label
		ttk.Label(self.entry_frame, text = message, anchor = 'w').pack(padx = 3, fill = X, expand = True)

		#Create buttons
		self.cancel_ok_button = ttk.Button(self.entry_frame, text = _('Cancel'), command = self.warning_dialog_window.destroy)
		self.cancel_ok_button.pack(side = 'right', pady = 3, padx = 3 )
		self.rename_ok_button = ttk.Button(self.entry_frame, text = _('OK'), command = func_command)
		self.rename_ok_button.pack(side = 'right', pady = 3, padx = 3 )

		#center the window
		if(platform.system() == 'Windows'):
			center_window(master, self.warning_dialog_window, 116, 46)
		else:
			center_window(master, self.warning_dialog_window)

		#Prevent new task in taskbar
		self.warning_dialog_window.transient(master)  

		#Focus on the dialog box, freeze controll of main window
		self.warning_dialog_window.focus_force()
		while True:
			try:
				self.warning_dialog_window.grab_set()
				break
			except: continue

	def destroy(self):
		self.warning_dialog_window.destroy()   

class NameDialog:
	def __init__(self, master, Title, func_command, icon, message = "", name = ""):
		#Create a new dialog box window
		self.name_dialog_window = Toplevel(master)

		#Make it non-resizeble, set title
		self.name_dialog_window.resizable(False, False)
		self.name_dialog_window.title(Title)

		#Create frames 
		self.icon_frame = ttk.Frame(self.name_dialog_window)
		self.icon_frame.pack(side = 'left', fill = Y)
		self.entry_frame = ttk.Frame(self.name_dialog_window)
		self.entry_frame.pack(side = 'left', fill = Y)

		#Create the label showing rename icon
		ttk.Label(self.icon_frame, image = icon).pack(padx = 3, pady = 3)

		#Create the label
		ttk.Label(self.entry_frame, text = message, anchor = 'w').pack(padx = 3, fill = X, expand = True)

		#Create the entry and set focus on entry
		self.rename_entry = ttk.Entry(self.entry_frame,)
		self.rename_entry.insert(END,name)
		self.rename_entry.select_range(0,END)
		self.rename_entry.pack(padx = 3, pady = 3, fill = X, expand = True)
		self.rename_entry.focus()

		#Create buttons
		self.cancel_ok_button = ttk.Button(self.entry_frame, text = _('Cancel'), command = self.name_dialog_window.destroy)
		self.cancel_ok_button.pack(side = 'right', pady = 3, padx = 3 )
		self.rename_ok_button = ttk.Button(self.entry_frame, text = _('OK'), command = func_command)
		self.rename_ok_button.pack(side = 'right', pady = 3, padx = 3 )

		#center the window
		if(platform.system() == 'Windows'):
			center_window(master, self.name_dialog_window, 119, 61)
		else:
			center_window(master, self.name_dialog_window)

		#Bind events
		self.rename_entry.bind('<Return>', func_command)

		#Prevent new task in taskbar
		self.name_dialog_window.transient(master) 

		#Focus on the dialog box, freeze controll of main window
		self.name_dialog_window.focus_force()
		while True:
			try:
				self.name_dialog_window.grab_set()
				break
			except: continue 

	def destroy(self):
		self.name_dialog_window.destroy()

class ReplaceDialog:
	def __init__(self, master, Title, icon, message):
		#Variable to tell which button has been pressed
		self.command = ''

		#Create a new dialog box window
		self.replace_dialog_window = Toplevel(master)

		#Make it non-resizeble, set title
		self.replace_dialog_window.resizable(False, False)
		self.replace_dialog_window.title(Title)

		#Overide [x] button
		self.replace_dialog_window.protocol('WM_DELETE_WINDOW', self.skip)

		#Create frames 
		self.icon_frame = ttk.Frame(self.replace_dialog_window)
		self.icon_frame.pack(side = 'left', fill = Y)
		self.entry_frame = ttk.Frame(self.replace_dialog_window)
		self.entry_frame.pack(side = 'left', fill = Y)

		#Create the label showing icon
		ttk.Label(self.icon_frame, image = icon).pack(padx = 3, pady = 3)

		#Create the label
		ttk.Label(self.entry_frame, text = message, anchor = 'w').pack(padx = 3, fill = X, expand = True)

		#Create buttons
		self.skip_button = ttk.Button(self.entry_frame, text = _('Skip'), command = self.skip)
		self.skip_button.pack(side = 'left', pady = 3, padx = 3 )
		self.replace_button = ttk.Button(self.entry_frame, text = _('Replace'), command = self.replace)
		self.replace_button.pack(side = 'left', pady = 3, padx = 3 )
		self.skip_all_button = ttk.Button(self.entry_frame, text = _('Skip all'), command = self.skip_all)
		self.skip_all_button.pack(side = 'left', pady = 3, padx = 3 )
		self.replace_all_button = ttk.Button(self.entry_frame, text = _('Replace all'), command = self.replace_all)
		self.replace_all_button.pack(side = 'left', pady = 3, padx = 3 )

		#center the window
		center_window(master, self.replace_dialog_window)

		#Prevent new task in taskbar
		self.replace_dialog_window.transient(master)  

		#Focus on the dialog box, freeze controll of main window
		self.replace_dialog_window.focus_force()
		while True:
			try:
				self.replace_dialog_window.grab_set()
				break
			except: continue

	def skip(self):
		self.command = 'skip'
		self.replace_dialog_window.destroy()

	def replace(self):
		self.command = 'replace'
		self.replace_dialog_window.destroy()

	def skip_all(self):
		self.command = 'skip_all'
		self.replace_dialog_window.destroy()

	def replace_all(self):
		self.command = 'replace_all'
		self.replace_dialog_window.destroy()

	def destroy(self):
		self.replace_dialog_window.destroy()

class FilePropertiesDialog:
	def __init__(self, master, root, Title, rename_command, chmod_command, icon, properties):
		self.properties = properties.split()
		self.master = root
		#Create a new dialog box window
		self.file_properties_dialog_window = Toplevel(master)

		#Make it non-resizeble, set title
		self.file_properties_dialog_window.resizable(False, False)
		self.file_properties_dialog_window.title(Title)

		#Create frames 
		self.icon_frame = ttk.Frame(self.file_properties_dialog_window)
		self.icon_frame.pack(side = 'left', fill = Y)
		self.entry_frame = ttk.Frame(self.file_properties_dialog_window)
		self.entry_frame.pack(side = 'left', fill = Y)

		#Create the label showing rename icon
		ttk.Label(self.icon_frame, image = icon).pack(padx=5,pady=5)

		#Create the label
		#
		#Create the label
		ttk.Label(self.entry_frame, text = _("Size: {} bytes").format(self.properties[4])+"    "+_("Modifed")+":  "+" ".join(self.properties[5:8]), anchor = 'w').pack(padx = 5, fill = X, expand = True)
		self.name_frame = ttk.Frame(self.entry_frame)
		self.name_frame.pack(fill = X, expand = True)
		#Create the entry and set focus on entry
		self.rename_entry = ttk.Entry(self.name_frame,)
		self.rename_entry.insert(END," ".join(self.properties[8:]))
		self.rename_entry.select_range(0,END)
		self.rename_entry.pack(padx = 10, pady = 3,side = 'right', fill = X, expand = True)
		self.rename_entry.focus()
		ttk.Label(self.name_frame, text = _("Name")+":", anchor = 'w').pack(padx = 5, side = 'right')
		ttk.Label(self.entry_frame, text = _("Rights")+":", anchor = 'w').pack(padx = 5, fill = X, expand = True)
		vals = self.properties[0]
		self.is_dir,self.uid,self.gid = BooleanVar(),IntVar(),IntVar()
		self.is_dir.set(vals[0]=="d")
		self.uid.set(int(self.properties[2]))
		self.gid.set(int(self.properties[3]))
		self.rights = [[BooleanVar() for x in range(3)] for y in range(3)]
		vals = [[1 if v!="-" else 0 for v in vals[i::3]] for i in range(1,4)]
		self.rights_frame = ttk.Frame(self.entry_frame)
		self.rights_frame.pack(fill = X, expand = True)
		ttk.Label(self.rights_frame, text = _("Read"), anchor = 'center').grid(padx = 5,row = 0, column = 1, sticky="ew")
		ttk.Label(self.rights_frame, text = _("Write"), anchor = 'center').grid(padx = 5,row = 0, column = 2, sticky="ew")
		ttk.Label(self.rights_frame, text = _("Exec"), anchor = 'center').grid(padx = 5,row = 0, column = 3, sticky="ew")
		ttk.Label(self.rights_frame, text = _("Owner"), anchor = 'e').grid(row = 1, column = 0, sticky="ew")
		ttk.Label(self.rights_frame, text = _("Group"), anchor = 'e').grid(row = 2, column = 0, sticky="ew")
		ttk.Label(self.rights_frame, text = _("All"), anchor = 'e').grid(row = 3, column = 0, sticky="ew")
		ttk.Entry(self.rights_frame,textvariable=self.uid).grid(row = 1, column = 4, pady = 3, padx = 10, sticky="nsew")
		ttk.Entry(self.rights_frame,textvariable=self.gid).grid(row = 2, column = 4, pady = 3, padx = 10, sticky="nsew")
		ttk.Checkbutton(self.rights_frame, variable=self.is_dir, onvalue=1, offvalue=0 , text=_("Is directory")).grid(row = 3, column = 4, pady = 3, padx = 10, sticky="nsew")
		for y in range(3):
			for x in range(3):
				self.rights[y][x].set(vals[x][y])
				ttk.Checkbutton(self.rights_frame, variable=self.rights[y][x], onvalue=1, offvalue=0).grid(row = y+1, column = x+1, sticky="nsew")
		#Create buttons
		ttk.Button(self.entry_frame, text = _('Cancel'), command = self.file_properties_dialog_window.destroy).pack(side = 'right', pady = 10, padx = 10 )
		ttk.Button(self.entry_frame, text = _('OK'), command = self.apply).pack(side = 'right', pady = 10, padx = 10 )

		#center the window
		center_window(master, self.file_properties_dialog_window)

		#Prevent new task in taskbar
		self.file_properties_dialog_window.transient(master)  

		#Focus on the dialog box, freeze controll of main window
		self.file_properties_dialog_window.focus_force()
		while True:
			try:
				self.file_properties_dialog_window.grab_set()
				break
			except: continue
	
	def apply(self):
		vals = ("d" if self.is_dir.get() else "-") +"".join(["".join(["rwx"[x] if self.rights[y][x].get() else "-" for x in range(3)]) for y in range(3)])
		if vals!=self.properties[0]:
			#Octal to int
			valsoct = int("01"[self.is_dir.get()] +"".join([str(int("".join(["01"[self.rights[y][x].get()] for x in range(3)]),2)) for y in range(3)]), 8)
			self.master.change_permissions(self.master.ftpController, self.master.file_list, {self.master.current_file_index:True}, valsoct)
		if " ".join(self.properties[8:]) != self.rename_entry.get():
			self.master.rename_file(self.master.ftpController, self.master.file_list, self.master.detailed_file_list, self.master.current_file_index, self.rename_entry.get())
		if self.uid.get()!=int(self.properties[2]) or self.gid.get()!=int(self.properties[3]):
			self.ftpController.ftp.chown(self.rename_entry.get(), self.uid.get(), self.gid.get())
		while not thread_request_queue.empty(): thread_request_queue.get()
		self.master.deselect_everything()
		self.master.update_file_list()
		self.master.update_status(' ')
		self.file_properties_dialog_window.destroy()

	def destroy(self):
		self.file_properties_dialog_window.destroy()

class ConsoleDialog:
	def __init__(self, master, icon, destroy_func):
		#Save reference to destroy function
		self.destroy_function = destroy_func

		#Save reference to icon
		self.icon = icon

		#Create a new dialog box window
		self.console_dialog_window = Toplevel(master)
		#Make it non-resizeble, set title
		self.console_dialog_window.resizable(False, False)
		self.console_dialog_window.title(_('Terminal'))

		#Overide [x] button
		self.console_dialog_window.protocol('WM_DELETE_WINDOW', self.close_message)

		#Prevent new task in taskbar
		self.console_dialog_window.transient(master) 

		#Create frames
		self.label_frame = ttk.Frame(self.console_dialog_window)
		self.label_frame.pack(fill = X)
		self.pad_pad_frame = ttk.Frame(self.console_dialog_window)
		self.pad_pad_frame.pack(fill = BOTH, expand = True)
		self.pad_frame = ttk.Frame(self.pad_pad_frame, relief = 'groove')
		self.pad_frame.pack(fill = BOTH, expand = True, pady = 3, padx = 5)
		self.text_frame = ttk.Frame(self.pad_frame)
		self.text_frame.pack(fill = BOTH, expand = True, pady = 1, padx = 1)
		self.button_frame = ttk.Frame(self.console_dialog_window)
		self.button_frame.pack(fill = X)

		#Create icon and label
		ttk.Label(self.label_frame, image = icon).pack(padx = 3, side = 'left')
		ttk.Label(self.label_frame, text = _('Performing tasks....'), anchor = 'w').pack(fill = X, side = 'left', pady = 3)

		#Create scrollbar
		self.vbar = ttk.Scrollbar(self.text_frame, orient=VERTICAL, style = 'Vertical.TScrollbar')
		self.vbar.pack(side=RIGHT,fill=Y)

		#Create text widget
		self.console_text = Text(self.text_frame, width = 80, relief = 'flat', highlightthickness=0, background = 'white')
		self.console_text.pack(fill = BOTH)
		self.vbar.config(command = self.console_text.yview, style = 'Whitehide.TScrollbar')
		self.console_text['yscrollcommand'] = self.vbar.set

		#Fix the mouse bug
		self.console_text.bind('<Button-1>', lambda e: 'break')
		self.console_text.bind('<Double-Button-1>' , lambda e: 'break')	 
		self.console_text.bind('<Control-Button-1>', lambda e: 'break')
		self.console_text.bind('<B1-Motion>', lambda e: 'break')

		#Create close button
		self.close_button = ttk.Button(self.button_frame, text = _('Close'), command = self.destroy, state = DISABLED)
		self.close_button.pack(side = 'right', pady = 3, padx = 3 )

		#Center the window
		if(platform.system() == 'Windows'):
			center_window(master, self.console_dialog_window, 343, 252)
		else:
			center_window(master, self.console_dialog_window)

		#Focus on the dialog box, freeze controll of main window
		self.console_dialog_window.focus_force()
		while True:
			try:
				self.console_dialog_window.grab_set()
				break
			except: continue

	def insert(self, line):
		self.console_text.insert('end',line+'\n')
		self.console_text.see('end')
		if(int(self.console_text.index('end').split('.')[0]) == 26):
			self.vbar.config(style = 'TScrollbar')

	def progress(self, percentage):
		self.console_text.delete('insert linestart', 'insert lineend')
		self.console_text.insert('end', percentage)
		if(int(self.console_text.index('end').split('.')[0]) == 26):
			self.vbar.config(style = 'TScrollbar')

	def close_message(self):
		if self.closable:
			self.destroy()

	def enable_close_button(self):
		self.closable = True
		self.close_button.config(state = NORMAL)

	def destroy(self):
		self.destroy_function()
		self.console_dialog_window.destroy()

class OpenFileDialog:
	def __init__(self, master, theme, Title, func_command, directory_mode = False):
		#/!\ Although the comments and variable names say 'file_list', or 'items' it inculdes folders also

		self.theme = theme
		#Cell width of each cell
		self.cell_width = 190

		#Variable to hold the max no character name in file list (used for padding in GUIs)
		self.max_len = 0

		#List to store all file names that are currently being displayed and theit details
		self.file_list = []
		#An index that points to current file that the mouse is pointing
		self.current_file_index = -1

		#Variables for drawing and storing cursor position
		self.mouse_x = 0
		self.mouse_y = 0
		self.max_width = 0

		#Variable to store which cell cursor is currently pointeing
		self.x_cell_pos = 0
		self.y_cell_pos = 0

		#A dictionary to store indices and highlight rectangle references of selected files
		self.selected_file_indices = {}

		#Variable to store start cell position of drag select
		self.start_x = 0
		self.start_y = 0

		#Variable to tell weather directory mode or not
		self.directory_mode = False

		#Variable to tell weather hidden files are enabled
		self.hidden_files = False		

		#Variable to hold the file name with max characters
		self.max_len_name = ''

		#Variable for holding the font
		self.default_font = font.nametofont("TkDefaultFont")

		self.directory_mode = directory_mode
		#Change to script's directory
		abspath = os.path.abspath(__file__)
		dname = os.path.dirname(abspath)
		os.chdir(dname)

		#Load all icons
		self.folder_icon_small = PhotoImage(file=join(dname,'Icons','folder_small.png'))
		self.mountpoint_icon_small = PhotoImage(file=join(dname,'Icons','mountpoint_small.png'))
		self.folder_icon = PhotoImage(file=join(dname,'Icons','folder_big.png'))
		self.textfile_icon = PhotoImage(file=join(dname,'Icons','textfile_big.png'))
		self.up_icon = PhotoImage(file=join(dname,'Icons','up_small.png'))
		self.dnd_glow_icon = PhotoImage(file=join(dname,'Icons_glow','gotopath_large_glow.png'))

		#Create a new dialog box window and set minimum size
		self.open_file_dialog_window = Toplevel(master)
		self.open_file_dialog_window.title(Title)
		self.open_file_dialog_window.minsize(width = 640, height = 480)

		#center the window 
		center_window(master, self.open_file_dialog_window, 320, 260)

		#Prevent new task in taskbar
		self.open_file_dialog_window.transient(master)

		#Create a new frame for text showing dirctory
		self.directory_frame = ttk.Frame(self.open_file_dialog_window)
		self.directory_frame.pack(fill = BOTH)

		#Create a label
		ttk.Label(self.directory_frame, text = _('Directory:')).pack(side = 'left') 

		#Create a text bar for dirctory
		self.directory_text = ttk.Combobox(self.directory_frame)
		self.directory_text.pack(fill = X, expand = True, side = 'left')
		self.directory_text.insert(END, os.getcwd()) 
		
		#List of home folders
		home_folders = ['Desktop', 'Documents', 'Downloads', 'Music', 'Pictures', 'Videos']

		#Automatically find paths for side buttons
		launch_paths = []
		home = expanduser('~')
		if(platform.system() == 'Windows'):
			home = home.replace(os.sep, '/')
		launch_paths.append(home)
		for folder in home_folders:
			if(os.path.exists(home+'/'+folder)):
				launch_paths.append(home+'/'+folder)
		drives = get_mounts()
		launch_paths += drives
		self.directory_text['values'] = launch_paths

		#Create up button
		self.up_button = ttk.Button(self.directory_frame, image = self.up_icon, command = self.dir_up)
		self.up_button.pack(side = 'right', padx = 3, pady = 3)

		#Create frame for canvas and scrollbar
		self.pad_frame = ttk.Frame(self.open_file_dialog_window)
		self.pad_frame.pack(fill = BOTH, expand = True)

		#Create frame for side bar
		self.side_frame = ttk.Frame(self.pad_frame, relief = 'flat', border = 0)
		self.side_frame.pack(side = 'left', fill = 'y', padx = 0, pady = 3)

		#Create frame for canvas
		self.canvas_frame = ttk.Frame(self.pad_frame, relief = 'groove', border = 1)
		self.canvas_frame.pack(side = 'left', fill = 'both', expand = 'true', padx = 5, pady = 3)

		#Create scrollbar
		self.vbar = ttk.Scrollbar(self.canvas_frame, orient=VERTICAL, style = 'Vertical.TScrollbar')
		self.vbar.pack(side=RIGHT,fill=Y)

		#Create frame for buttons
		self.button_frame = ttk.Frame(self.open_file_dialog_window)
		self.button_frame.pack(fill = X)

		#Create buttons
		self.cancel_ok_button = ttk.Button(self.button_frame, text = _('Cancel'), command = self.open_file_dialog_window.destroy)
		self.cancel_ok_button.pack(side = 'right', pady = 3, padx = 3 )
		self.rename_ok_button = ttk.Button(self.button_frame, text = _('OK'), command = func_command)
		self.rename_ok_button.pack(side = 'right', pady = 3, padx = 3 )

		#Create Side frame buttons
		for folder in launch_paths:
			button_name = folder.split('/')[-1].split(' ')[0]
			if(len(button_name) == 0):
				if(platform.system == 'Windows'):
					#Check for drive letters on windows
					button_name = split_list[0]
				else:
					#Check for root folder on linux
					button_name = 'Root'
			#Assign proper icon
			if(folder in drives):
				button_icon = self.mountpoint_icon_small
			else:
				button_icon = self.folder_icon_small
			#Loop through all the paths and create buttons
			PanelButton(self.side_frame, name = button_name, icon = button_icon, 
						 path = folder, command = self.change_dir_side_bar)
		

		#Bind keyboard shortcuts
		self.open_file_dialog_window.bind('<Control-h>', self.toggle_hidden_files)
		self.open_file_dialog_window.bind('<Control-H>', self.toggle_hidden_files)

		#Create a canvas
		self.canvas = Canvas(self.canvas_frame, bg = 'white', bd=0, highlightthickness=0, relief='ridge')
		self.canvas.pack(fill = BOTH, expand = True)
		self.vbar.config(command = self.canvas.yview)
		self.canvas['yscrollcommand'] = self.vbar.set

		#Bind events, this part of code also tells what some of the functions do
		self.canvas.bind('<Button-4>', self.on_mouse_wheel)
		self.canvas.bind('<Button-5>', self.on_mouse_wheel)
		self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
		self.canvas.bind('<Configure>', self.draw_icons)
		self.canvas.bind('<Motion>', self.update_status_and_mouse)
		self.canvas.bind('<Button-1>', self.mouse_select)
		self.canvas.bind('<Control-Button-1>', self.ctrl_select)
		self.canvas.bind('<Double-Button-1>' , self.change_dir) 
		self.canvas.bind('<B1-Motion>', self.drag_select)
		self.directory_frame.bind('<Motion>', self.stop_highlight)
		self.directory_text.bind('<Return>', self.change_dir_on_enter)
		self.directory_text.bind('<<ComboboxSelected>>', self.change_dir_on_enter)
		self.vbar.bind('<Motion>', self.stop_highlight) 
		self.button_frame.bind('<Motion>', self.stop_highlight)

		#Change to home directory
		if(platform.system() == 'Linux' or platform.system() == 'FreeBSD'):
			home = expanduser('~')
			os.chdir(os.getenv('HOME'))
			self.update_file_list()
		elif(platform.system() == 'Windows'):
			home = expanduser('~')
			os.chdir(home)
			self.update_file_list()

		#Code for handling file/folder drag and drop, uses TkDND_wrapper.py
		#See link: https://mail.python.org/pipermail/tkinter-discuss/2005-July/000476.html
		if(directory_mode):
			self.dnd = TkDND(master)
			self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<Drop>', self.handle_dnd, ('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))
			self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<DragEnter>', self.show_dnd_icon, ('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))
			self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<DragLeave>', lambda action, actions, type, win, X, Y, x, y, data:self.draw_icons(), ('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))

		#Focus on the dialog box, freeze controll of main window
		self.open_file_dialog_window.focus_force()
		while True:
			try:
				self.open_file_dialog_window.grab_set()
				break
			except: continue

	def folder_is_hidden(self, p):
		#See SO question: https://stackoverflow.com/questions/7099290/how-to-ignore-hidden-files-using-os-listdir
		if platform.system() == 'Windows':
			try:
				attrs = windll.kernel32.GetFileAttributesW(p)
				assert attrs != -1
				return bool(attrs & 2)
			except (AttributeError, AssertionError):
				return False
		else:
			return p.startswith('.') 

	def update_file_list(self):
		self.max_len = 0
		self.max_len_name = ''
		self.file_list.clear()
		for file in os.listdir():
			if(self.hidden_files or not self.folder_is_hidden(file)):
				self.file_list.append(file)
				if(len(file) > self.max_len):
					self.max_len = len(file)
					self.max_len_name = file
		#Redraw all icons
		self.draw_icons()
		#Change directory text
		self.directory_text.delete(0, 'end')
		self.directory_text.insert(END, os.getcwd()) 

	def handle_dnd(self, action, actions, type, win, X, Y, x, y, data):
		#Deselect everything
		self.deselect_everything()
		#Get path from text field
		dir_path = self.dnd.parse_uri_list(data)[0]
		#Chack validity and change directory
		if os.path.isdir(dir_path): os.chdir(dir_path)
		#Update file list and redraw icons
		self.update_file_list()

	def show_dnd_icon(self, action, actions, type, win, X, Y, x, y, data):
		self.deselect_everything()
		self.canvas.delete("all")
		self.canvas.create_image(self.canvas_width/2, self.canvas_height/2, image = self.dnd_glow_icon)

	def draw_icons(self, event = None):
		fg = self.theme.lookup("Theme","foreground")
		bg = self.theme.lookup("Theme","background")
		sel_bg = self.theme.lookup("Theme","selectbackground")
		sel_fg = self.theme.lookup("Theme","selectforeground")
		self.cell_width = 70 + self.default_font.measure(self.max_len_name)
		self.canvas_width = self.canvas.winfo_width() - 4
		self.canvas_height = self.canvas.winfo_height()
		if(self.cell_width > self.canvas_width):
			self.cell_width = self.canvas_width
		self.max_width = self.canvas_width - (self.canvas_width % self.cell_width) 
		max_no_cells_x  = self.max_width/self.cell_width 
		#Clear canvas
		self.canvas.delete('all')
		#Redraw all selected-highlight rectangles for selected files
		for file_index in self.selected_file_indices:
			x = file_index%max_no_cells_x
			y = int(file_index/max_no_cells_x)
			self.selected_file_indices[file_index] = self.canvas.create_rectangle(x*self.cell_width+2, y*35+2, (x+1)*self.cell_width-1, (y+1)*35-1, fill = sel_bg, outline = '')
		#Create a rectangle for upsate_status_mouse(self, event) function
		self.rect_id = self.canvas.create_rectangle(-1, -1, -1, -1, fill = '', outline = '')
		#Draw icons
		y = 0
		x = 0
		idx = 0
		for file_name in self.file_list:
			if((x+1)*self.cell_width > self.canvas_width):
				y+=1
				x=0
			#Check types, draw appropriate icon
			image = self.textfile_icon if isfile(file_name) else self.folder_icon
			fill = sel_fg if idx in self.selected_file_indices else fg
			self.canvas.create_image(25+(x*self.cell_width), 18+(y*35), image = image)
			self.canvas.create_text(45+(x*self.cell_width), 13+(y*35), text=file_name, fill=fill, anchor='nw')
			x+=1
			idx+=1
		#Calculate scroll region
		if (y+1)*35 < self.canvas_height:
			scroll_region_y = self.canvas_height - 1
			self.vbar.configure(style = 'Whitehide.TScrollbar')
		else:
			scroll_region_y = ((y+1)*35)+13
			self.vbar.configure(style = 'TScrollbar')
		self.canvas.configure(scrollregion = '-1 -1 ' + str(self.canvas_width) + ' ' + str(scroll_region_y))

	def update_status_and_mouse(self, event):
		#Get absolute mouse position on canvas
		self.mouse_x, self.mouse_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y) 
		#Use index = (y*width)+x to figure out the file index from canvas and mouse position
		self.x_cell_pos, self.y_cell_pos = int(self.mouse_x/self.cell_width),int(self.mouse_y/35)
		#Round canvas's width to nearest multiple of self.cell_width, width of each cell
		self.max_width = self.canvas_width - (self.canvas_width % self.cell_width)
		index = int(((self.max_width/self.cell_width)*self.y_cell_pos) + self.x_cell_pos)
		#Set status only if valid index, draw mouse-hover highlight rectangle
		if(index >= 0 and index < len(self.file_list) and self.mouse_x < self.max_width):
			self.current_file_index = index
			#Configure the rectangle created in draw_icons() to highlight the current folder
			self.canvas.itemconfig(self.rect_id, outline = 'black',dash=(1,1))
			self.canvas.coords(self.rect_id, self.x_cell_pos*self.cell_width+1, self.y_cell_pos*35+1, (self.x_cell_pos+1)*self.cell_width-1, (self.y_cell_pos+1)*35-1) 
		else:
			self.current_file_index = -1
			#Stop mouse-hover highlighting
			self.canvas.itemconfig(self.rect_id, outline = '')
			self.canvas.coords(self.rect_id, -1, -1, -1, -1)  

	def stop_highlight(self, event):
		#Stop mouse-hover highlighting
		self.canvas.itemconfig(self.rect_id, outline = '')
		self.canvas.coords(self.rect_id, -1, -1, -1, -1)

	def toggle_hidden_files(self, event):
		self.hidden_files = not self.hidden_files
		self.deselect_everything()
		self.update_file_list()

	def on_mouse_wheel(self, event):
		self.canvas.yview_scroll(1 if event.num == 5 or event.delta < 0 else -1, 'units')

	def mouse_select(self, event):
		#Check for directory mode
		if(self.directory_mode and self.current_file_index!=-1 and not isfile(self.file_list[self.current_file_index])):
			self.change_dir(event)
			return
		#Store start position for drag select
		self.start_x = self.x_cell_pos
		self.start_y = self.y_cell_pos
		self.deselect_everything()  
		#Set selected only if valid index
		if(self.current_file_index!=-1 and self.mouse_x < self.max_width):   
			self.selected_file_indices[self.current_file_index] = True
			self.draw_icons()

	def ctrl_select(self, event):
		#Check for directory mode
		if(self.directory_mode): return
		if(self.current_file_index!=-1 and self.mouse_x < self.max_width): 
			if(self.current_file_index not in self.selected_file_indices):
				self.selected_file_indices[self.current_file_index] = True
			else:
				del self.selected_file_indices[self.current_file_index]
			#Redraw icons
			self.draw_icons()

	def drag_select(self, event):
		if(self.directory_mode): return
		self.update_status_and_mouse(event)
		start_x_offset, step_x = (1,1) if(self.x_cell_pos <= self.start_x) else (-1,-1)
		start_y_offset, step_y = (1,1) if(self.y_cell_pos <= self.start_y) else (-1,-1)
		for i in range(self.x_cell_pos, self.start_x +start_x_offset, step_x):
			for j in range(self.y_cell_pos, self.start_y +start_y_offset, step_y):
				file_index = int(((self.max_width/self.cell_width)*j) + i)
				#Set selected only if valid index
				if(file_index >= 0 and file_index < len(self.file_list) and i < self.max_width/self.cell_width):
					self.selected_file_indices[file_index] = True
		self.draw_icons()

	def deselect_everything(self):
		self.selected_file_indices.clear()
		self.draw_icons()

	def change_dir(self, event):
		self.selected_file_indices.clear()
		if(self.current_file_index!=-1 and self.mouse_x < self.max_width):
			if(not isfile(self.file_list[self.current_file_index])):
				os.chdir(self.file_list[self.current_file_index])
				self.update_file_list()

	def dir_up(self):
		self.deselect_everything()
		os.chdir('..')
		self.update_file_list()

	def change_dir_on_enter(self, event):
		self.deselect_everything()
		dir_path = self.directory_text.get()
		if os.path.isdir(dir_path): os.chdir(dir_path)
		self.update_file_list()

	def change_dir_side_bar(self, path, event = None):
		self.deselect_everything()
		if os.path.isdir(path): os.chdir(path)
		self.update_file_list()


	def destroy(self):
		self.open_file_dialog_window.destroy()

class App:
	def __init__(self, master):
		#/!\ Although the comments and variable names say 'file_list', or 'items' it inculdes folders also

		#Cell width of each cell
		self.cell_width = 190

		#List to store all item names (including folders) that are currently being displayed and their details
		self.file_list = []
		self.detailed_file_list = []
		#An index that points to current file that the mouse is pointing
		self.current_file_index = -1

		#Variables for drawing and storing cursor position
		self.mouse_x = 0
		self.mouse_y = 0
		self.max_width = 0

		#Variable to store which cell cursor is currently pointing
		self.x_cell_pos = 0
		self.y_cell_pos = 0

		#A dictionary to store indices and highlight rectangle references of selected files
		self.selected_file_indices = {}

		#A list to hold files that have been droped into the window
		self.dnd_file_list = []
		self.dnd_dir = None

		#Things in the clipboard
		self.cut = False
		self.copy = False
		self.clipboard_file_list = []
		self.clipboard_path_list = []
		self.detailed_clipboard_file_list = []
		self.view = "table"
		self.sortby = "name"

		#Variable to store start cell position of drag select
		self.start_x = 0
		self.start_y = 0

		#Variable to tell weather to change status, if false the current message will stay on status bar and status bar will ignore other status messages
		self.change_status = True

		#Variable to tell replace all has been selected
		self.replace_all = False

		#Variable to tell skip all has been selected
		self.skip_all = False

		#Variable to tell weather a search has been performes
		self.search_performed = False

		#Variable to tell weather hidden file are enabled
		self.hidden_files = False

		#Variable to tell a thread weather to replace a file
		self.replace_flag = False

		#For thread syncrhoniztion
		self.thread_lock = threading.Lock()

		#Save reference to the window
		self.master = master

		#Save reference to ftpcontroller
		self.ftpController = ftp_controller()
 
		#Set window title and size
		master.wm_title('PySCP')
		master.minsize(width = 860, height = 560)

		#Variable for holding the font
		self.default_font = font.nametofont("TkDefaultFont")

		#Variable to tell weather to displat updatin file list dialog
		self.float_dialog_destroy = False

		#Set theme and style
		self.theme = ttk.Style()
		self.theme.theme_use('Arc')

		self.theme.configure('Red.TLabel', foreground = 'Red')

		#Create frame for toolbar buttons
		self.toolbar = ttk.Frame(master)
		self.toolbar.pack(fill = X)

		#Create frame for text fields
		self.entry_bar = ttk.Frame(master)
		self.entry_bar.pack(fill = X)

		#Create frame for canvas and scrollbar
		self.pad_frame = ttk.Frame(master)
		self.pad_frame.pack(fill = BOTH, expand = True)
		self.canvas_frame = ttk.Frame(self.pad_frame, relief = 'groove', border = 1)
		self.canvas_frame.pack(fill = BOTH, expand = True, padx = 5, pady = 3)

		#Code for handling file/folder drag and drop, uses TkDND_wrapper.py
		#See link: https://mail.python.org/pipermail/tkinter-discuss/2005-July/000476.html
		self.dnd = TkDND(master)
		self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<Drop>', self.handle_dnd, 
							('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))
		self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<DragEnter>', self.show_dnd_icon, 
							('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))
		self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<Drag>', self.handle_drag, 
							('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))
		self.dnd.bindtarget(self.canvas_frame, 'text/uri-list', '<DragLeave>', lambda action, actions, type, win,
							X, Y, x, y, data:self.draw_icons(), ('%A', '%a', '%T', '%W', '%X', '%Y', '%x', '%y','%D'))

		#Variables to kepp track of wain frame and animation
		self.wait_anim = False
		self.wait_frame_index = 1
		self.continue_wait = False

		#Load all icons
		self.connect_icon = PhotoImage(file=join(dname,'Icons','connect_big.png'))
		self.upload_icon = PhotoImage(file=join(dname,'Icons','upload_big.png'))
		self.download_icon = PhotoImage(file=join(dname,'Icons','download_big.png'))
		self.newfolder_icon = PhotoImage(file=join(dname,'Icons','newfolder_big.png'))
		self.up_icon = PhotoImage(file=join(dname,'Icons','up_big.png'))
		self.info_icon = PhotoImage(file=join(dname,'Icons','info_big.png'))
		self.delete_icon = PhotoImage(file=join(dname,'Icons','delete_big.png'))
		self.properties_icon = PhotoImage(file=join(dname,'Icons','properties_big.png'))
		self.cut_icon = PhotoImage(file=join(dname,'Icons','cut_big.png'))
		self.copy_icon = PhotoImage(file=join(dname,'Icons','copy_big.png'))
		self.paste_icon = PhotoImage(file=join(dname,'Icons','paste_big.png'))
		self.permissions_icon = PhotoImage(file=join(dname,'Icons','permissions_big.png'))
		self.folder_icon = PhotoImage(file=join(dname,'Icons','folder_big.png'))
		self.textfile_icon = PhotoImage(file=join(dname,'Icons','textfile_big.png'))
		self.console_icon = PhotoImage(file=join(dname,'Icons','console_big.png'))
		self.search_icon = PhotoImage(file=join(dname,'Icons','search_big.png'))
		self.rename_icon = PhotoImage(file=join(dname,'Icons','rename_big.png'))
		self.icon = PhotoImage(file=join(dname,'Icons','PySCP_large.png'))
		self.goto_icon = PhotoImage(file=join(dname,'Icons','gotopath_big.png'))

		#Load glow version of icons
		self.connect_glow_icon = PhotoImage(file=join(dname,'Icons_glow','connect_big_glow.png'))
		self.upload_glow_icon = PhotoImage(file=join(dname,'Icons_glow','upload_big_glow.png'))
		self.download_glow_icon = PhotoImage(file=join(dname,'Icons_glow','download_big_glow.png'))
		self.newfolder_glow_icon = PhotoImage(file=join(dname,'Icons_glow','newfolder_big_glow.png'))
		self.up_glow_icon = PhotoImage(file=join(dname,'Icons_glow','up_big_glow.png'))
		self.info_glow_icon = PhotoImage(file=join(dname,'Icons_glow','info_big_glow.png'))
		self.delete_glow_icon = PhotoImage(file=join(dname,'Icons_glow','delete_big_glow.png'))
		self.properties_glow_icon = PhotoImage(file=join(dname,'Icons_glow','properties_big_glow.png'))
		self.cut_glow_icon = PhotoImage(file=join(dname,'Icons_glow','cut_big_glow.png'))
		self.copy_glow_icon = PhotoImage(file=join(dname,'Icons_glow','copy_big_glow.png'))
		self.paste_glow_icon = PhotoImage(file=join(dname,'Icons_glow','paste_big_glow.png'))
		self.console_glow_icon = PhotoImage(file=join(dname,'Icons_glow','console_big_glow.png'))
		self.search_glow_icon = PhotoImage(file=join(dname,'Icons_glow','search_big_glow.png'))
		self.glow_icon = PhotoImage(file=join(dname,'Icons_glow','PySCP_large_glow.png'))
		self.dnd_glow_icon = PhotoImage(file=join(dname,'Icons_glow','upload_large_glow.png'))
		self.goto_glow_icon = PhotoImage(file=join(dname,'Icons_glow','gotopath_big_glow.png'))

		#Load icons from the wait animations
		self.wait_frames = []
		self.wait_frames.append(PhotoImage(file=join(dname,'Icons_glow','wait_anim_frame_one.png')))
		self.wait_frames.append(PhotoImage(file=join(dname,'Icons_glow','wait_anim_frame_two.png')))
		self.wait_frames.append(PhotoImage(file=join(dname,'Icons_glow','wait_anim_frame_three.png')))
		self.wait_frames.append(PhotoImage(file=join(dname,'Icons_glow','wait_anim_frame_four.png')))
		self.problem_icon = PhotoImage(file=join(dname,'Icons_glow','problem.png'))

		self.popup = Menu(self.master, tearoff=0)
		self.popup.add_command(label=_('Cut'),command=self.clipboard_cut)
		self.popup.add_command(label=_('Copy'),command=self.clipboard_copy)
		self.popup.add_command(label=_('Paste'),command=self.clipboard_paste)
		self.popup.add_separator()
		self.popup.add_command(label=_('Delete'),command=self.delete_window)
		self.popup.add_command(label=_('Rename'),command=self.rename_window)
		self.popup.add_command(label=_('Rights'),command=self.change_permissions_window)
		self.popup.add_command(label=_('New directory'),command=self.create_dir_window)
		self.popup.add_separator()
		self.popup.add_command(label=_('Properties'),command=self.file_properties_window)


		#Set window icon
		self.master.iconphoto(True, self.icon)

		#Create the connect button
		self.connect_button = ToolbarButton(self.toolbar, image = self.connect_icon, image_hover = self.connect_glow_icon, command = self.connect_to_ftp)
		self.connect_button.pack(side = 'left', padx = 5)
		#Create the up-directory button
		self.up_button = ToolbarButton(self.toolbar, image = self.up_icon, image_hover = self.up_glow_icon, command = self.dir_up)
		self.up_button.pack(side = 'left', padx = 5)
		#Create the newfolder button
		self.newfolder_button = ToolbarButton(self.toolbar, image = self.newfolder_icon, image_hover = self.newfolder_glow_icon, command = self.create_dir_window)
		self.newfolder_button.pack(side = 'left', padx = 5)
		#Create the info button
		self.info_button = ToolbarButton(self.toolbar, image = self.info_icon, image_hover = self.info_glow_icon, command = self.info)
		self.info_button.pack(side = 'right', padx = 5)
		#Create the search button
		self.search_button = ToolbarButton(self.toolbar, image = self.search_icon, image_hover = self.search_glow_icon, command = self.search_window_ask)
		self.search_button.pack(side = 'right', padx = 5)
		#Create the goto button
		self.goto_button = ToolbarButton(self.toolbar, image = self.goto_icon, image_hover = self.goto_glow_icon, command = self.goto_window_ask)
		self.goto_button.pack(side = 'right', padx = 5)
		#Create the delete button
		self.delete_button = ToolbarButton(self.toolbar, image = self.delete_icon, image_hover = self.delete_glow_icon, command = self.delete_window)
		self.delete_button.pack(side = 'left', padx = 5)
		#Create the properties button
		self.properties_button = ToolbarButton(self.toolbar, image = self.properties_icon, image_hover = self.properties_glow_icon, command = self.file_properties_window)
		self.properties_button.pack(side = 'left', padx = 5)
		#Create the cut button
		self.cut_button = ToolbarButton(self.toolbar, image = self.cut_icon, image_hover = self.cut_glow_icon, command = self.clipboard_cut)
		self.cut_button.pack(side = 'left', padx = 5)
		#Create the copy button
		self.copy_button = ToolbarButton(self.toolbar, image = self.copy_icon, image_hover = self.copy_glow_icon, command = self.clipboard_copy)
		self.copy_button.pack(side = 'left', padx = 5)
		#Create the paste button
		self.paste_button = ToolbarButton(self.toolbar, image = self.paste_icon, image_hover = self.paste_glow_icon, command = self.clipboard_paste_thread_create)
		self.paste_button.pack(side = 'left', padx = 5)
		#Create the upload button
		self.upload_button = ToolbarButton(self.toolbar, image = self.upload_icon, image_hover = self.upload_glow_icon, command = self.upload_window)
		self.upload_button.pack(side = 'left', padx = 5)
		#Create the download button
		self.download_button = ToolbarButton(self.toolbar, image = self.download_icon, image_hover = self.download_glow_icon, command = self.download_window)
		self.download_button.pack(side = 'left', padx = 5)
		#Create label field for hostname
		self.label_hostname = ttk.Label(self.entry_bar, text = _('Host:'))
		self.label_hostname.pack(side = 'left', padx = 2)
		#Create text field for hostname
		self.hostname = StringVar()
		self.hostname_combobox = ttk.Combobox(self.entry_bar, textvariable=self.hostname)
		self.hostname_combobox['values'] = [x["host"] for x in history if x["host"]!=""]
		self.hostname_combobox.pack(side = 'left', expand = True, fill = X)
		self.hostname.set(history[-1]["host"])
		#Create combobox
		self.connection_type = StringVar()
		self.type_combobox = ttk.Combobox(self.entry_bar, textvariable=self.connection_type, width = 5, state = 'readonly')
		self.connection_type.set(history[-1]["type"])
		self.type_combobox['values'] = ('FTP', 'SFTP')
		self.type_combobox.pack(side = 'left')
		#Create label for username
		self.label_usrname = ttk.Label(self.entry_bar, text = _('Username:'))
		self.label_usrname.pack(side = 'left', padx = 2)
		#Create text field for username
		self.usrname_entry = ttk.Entry(self.entry_bar)
		self.usrname_entry.insert(END,history[-1]["user"])
		self.usrname_entry.pack(side = 'left', expand = True, fill = X)
		#Create label for password
		self.label_pass = ttk.Label(self.entry_bar, text = _('Password:'))
		self.label_pass.pack(side = 'left', padx = 2)
		#Create textfield for password
		self.pass_entry = ttk.Entry(self.entry_bar, show = '*')
		self.pass_entry.insert(END,history[-1]["password"])
		self.pass_entry.pack(side = 'left', expand = True, fill = X)
		#Create label for port
		self.label_port = ttk.Label(self.entry_bar, text = _('Port:'))
		self.label_port.pack(side = 'left', padx = 2)
		#Create textfield for port
		self.port_entry = ttk.Entry(self.entry_bar, width = 4)
		self.port_entry.pack(side = 'left', padx = (0, 2))
		self.port_entry.insert(END,str(history[-1]["port"]))
		#Create scrollbar
		self.vbar = ttk.Scrollbar(self.canvas_frame, orient=VERTICAL, style = 'Vertical.TScrollbar')
		self.vbar.pack(anchor = E,side=RIGHT,fill=Y)
		#Create drawing space for all file and folder icons
		self.canvas = Canvas(self.canvas_frame, relief = 'flat', bg = 'white', highlightthickness=0)
		self.canvas.pack(fill = BOTH, expand = True)
		self.vbar.config(command = self.canvas.yview)
		self.canvas['yscrollcommand'] = self.vbar.set
		#Create status text/bar and status sting viraiable
		self.current_status = StringVar()
		self.status_label = ttk.Label(master, textvariable = self.current_status, anchor = 'w')
		self.status_label.pack(fill = X)

		#Bind events
		self.bind_events()



	def bind_events(self):
		#Bind keyboard shortcuts
		self.master.bind('<Control-h>', self.toggle_hidden_files)
		self.master.bind('<Control-H>', self.toggle_hidden_files)
		self.master.bind('<Control-c>', self.clipboard_copy)
		self.master.bind('<Control-C>', self.clipboard_copy)
		self.master.bind('<Control-x>', self.clipboard_cut)
		self.master.bind('<Control-X>', self.clipboard_cut)
		self.master.bind('<Control-v>', self.clipboard_paste_thread_create)
		self.master.bind('<Control-V>', self.clipboard_paste_thread_create) 
		self.master.bind('<Delete>', self.delete_window)

		#Bind events for canvas, this part of code tells what some of the functions do
		self.canvas.bind("<Button-3>", self.show_popup)
		self.canvas.bind('<Button-4>', self.on_mouse_wheel)
		self.canvas.bind('<Button-5>', self.on_mouse_wheel)
		self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
		self.canvas.bind('<Configure>', self.draw_icons)
		self.canvas.bind('<Motion>', self.update_status_and_mouse)
		self.canvas.bind('<Button-1>', self.mouse_select)
		self.canvas.bind('<Double-Button-1>' , self.change_dir)
		self.canvas.bind('<Control-Button-1>', self.ctrl_select)
		self.canvas.bind('<B1-Motion>', self.drag_select)

		#Bind events for statusbar and scroll bar
		self.vbar.bind('<Motion>', lambda event, arg = _('Scrollbar'): self.update_status(event, arg)) 
		self.status_label.bind('<Motion>', lambda event, arg = _('Statusbar'): self.update_status(event, arg)) 

		#Bind events for all buttons
		self.connect_button.bind('<Motion>', lambda event, arg = _('Connection'): self.update_status(event, arg)) 
		self.upload_button.bind('<Motion>', lambda event, arg = _('Upload file(s) or folder(s).'): self.update_status(event, arg)) 
		self.download_button.bind('<Motion>', lambda event, arg = _('Save/Download file(s) or folder(s).'): self.update_status(event, arg)) 
		self.newfolder_button.bind('<Motion>', lambda event, arg = _('New directory'): self.update_status(event, arg)) 
		self.delete_button.bind('<Motion>', lambda event, arg = _('Delete'): self.update_status(event, arg)) 
		self.properties_button.bind('<Motion>', lambda event, arg = _('Properties'): self.update_status(event, arg)) 
		self.cut_button.bind('<Motion>', lambda event, arg = _('Cut'): self.update_status(event, arg)) 
		self.copy_button.bind('<Motion>', lambda event, arg = _('Copy'): self.update_status(event, arg)) 
		self.paste_button.bind('<Motion>', lambda event, arg = _('Paste'): self.update_status(event, arg)) 
		self.search_button.bind('<Motion>', lambda event, arg = _('Find'): self.update_status(event, arg))
		self.goto_button.bind('<Motion>', lambda event, arg = _('Goto'): self.update_status(event, arg)) 
		self.up_button.bind('<Motion>', lambda event, arg = _('Parent directory'): self.update_status(event, arg)) 
		self.info_button.bind('<Motion>', lambda event, arg = _('About'): self.update_status(event, arg)) 

		#Bind events for all labels
		self.toolbar.bind('<Motion>', lambda event, arg = ' ': self.update_status(event, arg)) 
		self.label_usrname.bind('<Motion>', lambda event, arg = ' ': self.update_status(event, arg)) 
		self.label_hostname.bind('<Motion>', lambda event, arg = ' ': self.update_status(event, arg)) 
		self.label_port.bind('<Motion>', lambda event, arg = ' ': self.update_status(event, arg)) 

		#Bind events for all entries/text fields
		self.hostname_combobox.bind('<Motion>', lambda event, arg = _('Enter host address.'): self.update_status(event, arg)) 
		self.hostname_combobox.bind('<<ComboboxSelected>>', self.handle_host)
		self.type_combobox.bind('<Motion>', lambda event, arg = _('Select connection type'): self.update_status(event, arg)) 
		self.type_combobox.bind('<<ComboboxSelected>>', self.handle_combobox)
		self.usrname_entry.bind('<Motion>', lambda event, arg = _('Enter your username.'): self.update_status(event, arg))
		self.pass_entry.bind('<Motion>', lambda event, arg = _('Enter your password.'): self.update_status(event, arg))
		self.port_entry.bind('<Motion>', lambda event, arg = _('Enter port.'): self.update_status(event, arg))

		#Press enter key to connect
		self.hostname_combobox.bind('<Return>', self.connect_to_ftp) 
		self.usrname_entry.bind('<Return>', self.connect_to_ftp)
		self.pass_entry.bind('<Return>', self.connect_to_ftp)
		self.port_entry.bind('<Return>', self.connect_to_ftp)  

	def show_popup(self,event):
		if not len(self.selected_file_indices): self.mouse_select(event)
		self.popup.tk_popup(event.x_root, event.y_root, 0)
		self.popup.grab_release()

	def handle_host(self, event):
		idx  = event.widget.current()
		self.usrname_entry.delete(0, 'end')
		self.pass_entry.delete(0, 'end')
		self.port_entry.delete(0, 'end')
		self.connection_type.set(history[idx]["type"])
		self.usrname_entry.insert(END,history[idx]["user"])
		self.pass_entry.insert(END,history[idx]["password"])
		self.port_entry.insert(END,str(history[idx]["port"]))

	def handle_combobox(self, event):
		#Clear port entry
		self.port_entry.delete(0, 'end') 
		#Set default port   
		if(self.type_combobox.get() == 'FTP'): 
			self.port_entry.insert(END, '21')
		else: 
			self.port_entry.insert(END, '22')

	def connect_to_ftp(self, event = None,uri = None):
		protocols = {
			"FTP":[21,lambda:ftp_controller()],
			"SFTP":[22,lambda:sftp_controller()],
		}
		#Show wait animation
		self.unlock_status_bar()
		self.start_wait()
		#Show 'Connecting' in status bar
		self.update_status(message = _('Connecting...'))
		self.lock_status_bar()
		#Check connection type create appropriate controller
		try:
			self.ftpController.disconnect()
			del self.ftpController
		except:
			pass
		if uri:
			protocol,__,user,password,__,host,port,directory = re.match("(\w+)\:\/\/((\w+)\:?(\w+)?@)?@?(([^\:\/]+)\:?(\d+)?)(.+)?",uri).groups()
			user = user or "Anonumous"
			password = password or "PySCP"
			port = int(port or protocols[protocol.upper()][0])
			self.connection_type.set(protocol.upper())
			self.hostname.set(host)
			self.usrname_entry.insert(END,user)
			self.pass_entry.insert(END,password)
			self.port_entry.insert(END,str(port))
		else:
			protocol,host,user,password,port,directory = self.type_combobox.get(),self.hostname_combobox.get(), self.usrname_entry.get(), self.pass_entry.get(), self.port_entry.get(),None
		self.ftpController = protocols[protocol.upper()][1]()
		self.thread =  threading.Thread(target = self.connect_thread, args = (self.ftpController,host, user, password, int(port),directory))
		global history
		if self.hostname_combobox.get() not in [x["host"]for x in history if x["host"]!=""]:
			if history[-1]["host"]=="": del history[-1]
		else:
			id = [k for k,v in enumerate(history) if v["host"]==host][0]
			del history[id]
		history.append({"host":host, "user":user, "password":password,"type":protocol.upper(), "port":int(port)})
		self.hostname_combobox['values'] = [x["host"] for x in history if x["host"]!=""]
		with open(join(dname,"history.json"),"wb") as fp:
			fp.write(json.dumps(history,ensure_ascii=False).encode("utf-8"))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()
		

	def connect_thread(self, ftpController, host, user, password, port, directory=None):
		try:
			keyfile = None
			passphrase = None
			if os.path.isdir(join(dname,"keys")):
				for key in os.listdir(join(dname,"keys")):
					if host in key and user in key:
						keyfile = join(dname,"keys",key)
						passphrase = password
						password = None
						print(keyfile)
						break
			ftpController.connect_to(host, user, password, port, keyfile, passphrase)
			if directory: ftpController.ftp.cwd(directory)
			thread_request_queue.put(lambda:self.unlock_status_bar())
			thread_request_queue.put(lambda:self.cont_wait())
			thread_request_queue.put(lambda:self.update_file_list())
			thread_request_queue.put(lambda:self.update_status(message = _('Connected.')))
		except:
			thread_request_queue.put(lambda:self.unlock_status_bar())
			thread_request_queue.put(lambda:self.update_status_red(_('Unable to connect, please check what you have entered.')))
			#Make sure unable to connect message stays on status bar
			thread_request_queue.put(lambda:self.lock_status_bar())
		#Need to focus on the main window and the entry due to a bug in ttk/tkinter (entries don't focis properly after creating and destroying windowless messagebox dialog)  
		thread_request_queue.put(lambda:self.hostname_combobox.focus()) 
		thread_request_queue.put(lambda:self.master.focus())

	def update_file_list(self):
		#Disable toolbar
		self.start_wait()
		#Set search to false
		self.search_performed = False
		self.unlock_status_bar()
		self.update_status(message = _('Retrieving file list, Hidden files: {}, Please wait...').format(self.ftpController.hidden_files))
		self.lock_status_bar()
		self.file_list.clear()
		self.detailed_file_list.clear()
		#start thread
		self.thread = threading.Thread(target = self.update_file_list_thread)
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def sort_file_list(self, sort=None):
		self.detailed_file_list.sort(key=sort_func[sort or self.sortby])
		self.file_list = self.ftpController.get_file_list(self.detailed_file_list)

	def update_file_list_thread(self):
		try:
			with self.thread_lock:
				self.detailed_file_list = self.ftpController.get_detailed_file_list()
				self.sort_file_list()
			#Set the window title to current path
			thread_request_queue.put(lambda:self.master.wm_title('PySCP    '+self.ftpController.pwd()))
			thread_request_queue.put(lambda:self.unlock_status_bar())
			thread_request_queue.put(lambda:self.update_status(''))
		except:
			thread_request_queue.put(lambda:self.unlock_status_bar())
			thread_request_queue.put(lambda:self.update_status_red(_('Unable to retrieve file list, connection might be lost.')))
			thread_request_queue.put(lambda:self.lock_status_bar())
		thread_request_queue.put(lambda:self.draw_icons())
		#Enable toolbar
		thread_request_queue.put(lambda:self.end_wait())

	def draw_icons(self, event = None):
		fg = self.theme.lookup("Theme","foreground")
		bg = self.theme.lookup("Theme","background")
		sel_bg = self.theme.lookup("Theme","selectbackground")
		sel_fg = self.theme.lookup("Theme","selectforeground")
		#Calculate cell width
		name_width = 65 + self.default_font.measure(self.ftpController.max_len_name)
		self.cell_width = name_width
		self.canvas_width = self.canvas.winfo_width() - 4
		self.canvas_height = self.canvas.winfo_height()
		#Round canvas's width to nearest multiple of self.cell_width, width of each cell
		if(self.cell_width > self.canvas_width or self.view == "table"):
			self.cell_width = self.canvas_width
			col_width = (self.canvas_width - name_width - 65)/3
		self.max_width = self.canvas_width - (self.canvas_width % self.cell_width) 
		max_no_cells_x  = self.max_width/self.cell_width 
		#Clear canvas
		self.canvas.delete('all')
		#If there are no files, draw watermark
		if len(self.file_list)==0:
			self.canvas.create_image(self.canvas_width/2, self.canvas_height/2, image = self.glow_icon)
		#Redraw all selected-highlight rectangles for selected files
		for file_index in self.selected_file_indices:
			x = file_index%max_no_cells_x
			y = int(file_index/max_no_cells_x)
			self.selected_file_indices[file_index] = self.canvas.create_rectangle(x*self.cell_width+2, y*35+2, (x+1)*self.cell_width-1, (y+1)*35-1, fill = sel_bg, outline = '')
		#Create a rectangle for update_status_mouse(self, event) function
		self.rect_id = self.canvas.create_rectangle(-1, -1, -1, -1, fill = '', outline = '')
		#Draw icons
		y = 0
		x = 0
		id = 0
		for file_name, file_details in zip(self.file_list, self.detailed_file_list):
			if((x+1)*self.cell_width > self.canvas_width):
				y += 1
				x = 0
			#Check types, draw appropriate icon
			image = self.folder_icon if self.ftpController.is_dir(file_details) else self.textfile_icon
			fill = sel_fg if id in self.selected_file_indices else fg
			self.canvas.create_image(25+(x*self.cell_width), 18+(y*35), image = image)
			self.canvas.create_text(45+(x*self.cell_width), 13+(y*35), text=file_name, fill=fill, anchor='nw')
			if self.view == "table":
				p = self.ftpController.get_properties(file_details)
				if len(p)==4:self.canvas.create_text(65+name_width, 13+(y*35), text=p[3], fill=fill, anchor='nw')
				self.canvas.create_text(65+name_width+col_width, 13+(y*35), text=p[1], fill=fill, anchor='nw')
				self.canvas.create_text(65+name_width+col_width*2, 13+(y*35), text=p[2], fill=fill, anchor='nw')
			x += 1
			id += 1
		#Calculate scroll region for scroll bar
		if (y+1)*35 < self.canvas_height:
			scroll_region_y = self.canvas_height - 1
			self.vbar.configure(style = 'Whitehide.TScrollbar')
			self.vbar.bind('<Motion>', lambda event, arg = '': self.update_status(event, arg)) 
		else:
			scroll_region_y = ((y+1)*35)+13
			self.vbar.configure(style = 'TScrollbar')
			self.vbar.bind('<Motion>', lambda event, arg = 'Scrollbar.': self.update_status(event, arg)) 
		self.canvas.configure(scrollregion = '-1 -1 ' + str(self.canvas_width) + ' ' + str(scroll_region_y))

	def update_status_and_mouse(self, event):
		if event.x < 0 or event.y < 0: return
		#Get absolute mouse position on canvas
		self.mouse_x, self.mouse_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y) 
		#Calculate cell row and cell column based on mouse's position
		self.x_cell_pos,self.y_cell_pos = int(self.mouse_x/self.cell_width),int(self.mouse_y/35)
		#Round canvas's width to nearest multiple of self.cell_width, width of each cell
		self.max_width = self.canvas_width - (self.canvas_width % self.cell_width)
		#Use index = (y*width)+x to figure out the file index from canvas and mouse position
		index = int(((self.max_width/self.cell_width)*self.y_cell_pos) + self.x_cell_pos)
		#Set status only if valid index, draw mouse-hover highlight rectangle
		if(index >= 0 and index < len(self.file_list) and self.mouse_x < self.max_width):
			self.current_file_index = index
			self.update_status(event, self.detailed_file_list[self.current_file_index])
			#Configure the rectangle created in draw_icons() to highlight the current folder mose is pointing at
			self.canvas.itemconfig(self.rect_id, outline = 'black', dash=(1,1))
			self.canvas.coords(self.rect_id, self.x_cell_pos*self.cell_width+1, self.y_cell_pos*35+1, (self.x_cell_pos+1)*self.cell_width-1, (self.y_cell_pos+1)*35-1) 
		else:
			self.current_file_index = -1
			#Tell how many files are present and how many are selected in the status bar
			self.update_status(event, _('Total no. of items: {}   Selected: {}').format(len(self.file_list),len(self.selected_file_indices)))
			#Stop mouse-hover highlighting
			self.canvas.itemconfig(self.rect_id, outline = '', dash=[])
			self.canvas.coords(self.rect_id, -1, -1, -1, -1)  
	
	def update_status(self, event = None, message = ' '):
		#Stop mouse-hover highlighting
		self.canvas.itemconfig(self.rect_id, outline = '')
		self.canvas.coords(self.rect_id, -1, -1, -1, -1) 
		#Display message in status bar in black color only if change_status is true else ignore it
		if self.change_status:
			self.status_label.configure(style = 'TLabel')
			self.current_status.set(message)

	def update_status_red(self, message):
		#Stop mouse-hover highlighting
		self.canvas.itemconfig(self.rect_id, outline = '')
		self.canvas.coords(self.rect_id, -1, -1, -1, -1) 
		#Display message in status bar in red color only if change_status is true else ignore it
		if self.change_status:
			self.status_label.configure(style = 'Red.TLabel')
			self.current_status.set(message)
			self.problem()

	def lock_status_bar(self):
		self.change_status = False

	def unlock_status_bar(self):
		self.change_status = True

	def toggle_hidden_files(self, event):
		self.ftpController.toggle_hidden_files()
		self.update_file_list()
		self.deselect_everything()

	def on_mouse_wheel(self, event):
		self.canvas.yview_scroll(1 if event.num == 5 or event.delta < 0 else -1, 'units')

	def mouse_select(self, event):
		self.master.focus()
		self.start_x,self.start_y = self.x_cell_pos, self.y_cell_pos
		self.deselect_everything()  
		if(self.current_file_index!=-1 and self.mouse_x < self.max_width):   
			self.selected_file_indices[self.current_file_index] = True
			self.draw_icons()
			self.update_status(event, _('Total no. of items: {}   Selected: {}').format(len(self.file_list),len(self.selected_file_indices)))

	def ctrl_select(self, event):
		if(self.current_file_index!=-1 and self.mouse_x < self.max_width): 
			if(self.current_file_index not in self.selected_file_indices):
				self.selected_file_indices[self.current_file_index] = True
			else:
				del self.selected_file_indices[self.current_file_index]
			self.draw_icons()
			self.update_status(event, _('Total no. of items: {}   Selected: {}').format(len(self.file_list),len(self.selected_file_indices)))

	def drag_select(self, event):
		if event.x < 0 or event.y < 0: return
		#Update to get current mouse position
		self.update_status_and_mouse(event)
		#Calculate steps and offsets for xy-direction
		start_x_offset,step_x = (1,1) if(self.x_cell_pos <= self.start_x) else (-1,-1)
		start_y_offset,step_y = (1,1) if(self.y_cell_pos <= self.start_y) else (-1,-1)
		#Select items
		for i in range(self.x_cell_pos, self.start_x +start_x_offset, step_x):
			for j in range(self.y_cell_pos, self.start_y +start_y_offset, step_y):
				file_index = int(((self.max_width/self.cell_width)*j) + i)
				#Set selected only if valid index
				if(file_index >= 0 and file_index < len(self.file_list) and i < self.max_width/self.cell_width):   
					#Draw a 'selected' highlighting rectangle and save a reference to the rectangle in selected file dictionary
					self.selected_file_indices[file_index] = True
		self.draw_icons()
		#Tell how many files are present and how many are selected in the status bar
		self.update_status(event, _('Total no. of items: {}   Selected: {}').format(len(self.file_list),len(self.selected_file_indices)))

	def handle_dnd(self, action, actions, type, win, X, Y, x, y, data):
		#If there is another child window, disable dnd
		#if(len(self.master.children) != 4): return
		self.dnd_file_list.clear()
		self.dnd_file_list = self.dnd.parse_uri_list(data)
		if self.ftpController.is_dir(self.detailed_file_list[self.current_file_index]):
			self.dnd_dir = self.file_list[self.current_file_index]
		else:
			self.dnd_dir = None
		self.upload_thread_dnd()
		self.canvas.delete(self.dnd_image)

	def handle_drag(self, action, actions, type, win, X, Y, x, y, data):
		event = Event()
		event.x,event.y=int(X)-self.canvas.winfo_rootx(),int(Y)-self.canvas.winfo_rooty()
		self.update_status_and_mouse(event)

	def show_dnd_icon(self, action, actions, type, win, X, Y, x, y, data):
		#If there is another child window, disable dnd
		#if(len(self.master.children) != 4): return
		self.deselect_everything()
		#self.canvas.delete("all")
		self.dnd_image = self.canvas.create_image(self.canvas_width - self.dnd_glow_icon.width(), self.canvas_height - self.dnd_glow_icon.height(), image = self.dnd_glow_icon)

	def deselect_everything(self):
		self.selected_file_indices.clear()
		self.draw_icons()

	def change_dir(self, event):
		#Delete selected file list
		self.selected_file_indices.clear()
		#Show message box
		if(self.current_file_index!=-1 and self.mouse_x < self.max_width):
			if(self.ftpController.is_dir(self.detailed_file_list[self.current_file_index])):
				try:
					self.ftpController.ftp.cwd(self.file_list[self.current_file_index])
					self.update_file_list()
				except:
					self.update_status_red(_('Unable to open directory, try reconnecting.'))
					self.lock_status_bar()
			else:
				#self.update_status(_('Editiing file...'))
				cwd = os.getcwd()
				if not os.path.isdir(join(dname,'tmp')):os.mkdir(join(dname,'tmp'))
				os.chdir(join(dname,'tmp'))
				old_size = int(self.ftpController.get_properties(self.detailed_file_list[self.current_file_index])[3])
				self.ftpController.download_file(self.file_list[self.current_file_index], old_size, lambda x,y: True, lambda x,y: True)
				os.system('notepad '+self.file_list[self.current_file_index])
				new_size = os.path.getsize(self.file_list[self.current_file_index])
				if old_size!=new_size: self.ftpController.upload_file(self.file_list[self.current_file_index], new_size, lambda x,y: True, lambda x,y: True)
				os.remove(self.file_list[self.current_file_index])
				os.chdir(cwd)

	def goto_window_ask(self):
		self.goto_window = NameDialog(self.master, _('Goto'), self.goto_path, self.goto_icon, _('Enter path:'))

	def goto_path(self):
		path = self.goto_window.rename_entry.get()
		self.goto_window.destroy()
		self.selected_file_indices.clear()
		#Show message box
		try:
			self.ftpController.ftp.cwd(path)
			self.update_file_list()
		except:
			self.update_status_red(_('Unable to open directory, try reconnecting.'))
			self.lock_status_bar()

	def dir_up(self):
		self.selected_file_indices.clear()
		#Update GUI now, before mainloop, the following code takes a long time to execute
		self.master.update_idletasks() 
		try:
			if not self.search_performed:
				self.ftpController.ftp.cwd('..')
			self.update_file_list()
		except:
			self.update_status_red(_('Unable to open directory, try reconnecting.'))
			self.lock_status_bar()

	def file_properties_window(self):
		if self.current_file_index==-1: return
		#Create the string that contains all the properties
		file_details = self.ftpController.get_properties(self.detailed_file_list[self.current_file_index])
		file_name = file_details[0] + '\n'
		file_attribs = file_details[1]+ '\n'
		date_modified = file_details[2]
		if(self.ftpController.is_dir(self.detailed_file_list[self.current_file_index])):
			properties = 'Name: '+ file_name + 'Attributes: ' + file_attribs + 'Date: ' + date_modified
		else:
			file_size = file_details[3] + ' bytes'
			properties = 'Name: '+ file_name + 'Attributes: ' + file_attribs + 'Date: ' + date_modified + '\n' + 'Size: ' + file_size
		#Display the created string in properties dialog
		self.properties_dialog = FilePropertiesDialog(self.master, self, _('Properties'), self.rename_window, self.change_permissions_window, self.properties_icon, self.detailed_file_list[self.current_file_index])

	def rename_window(self):
		if self.current_file_index==-1: return
		self.rename_dialog =  NameDialog(self.master, _('Rename'), self.rename_file_thread, self.rename_icon,message = _('Enter new name:'), name = self.file_list[self.current_file_index])

	def rename_file_thread(self):
		rename_name = self.rename_dialog.rename_entry.get()
		#Destroy rename window
		self.rename_dialog.destroy()
		#Show message box
		self.start_wait()
		#start thread
		self.thread =  threading.Thread(target = self.rename_file, args = (self.ftpController, self.file_list, self.detailed_file_list, self.current_file_index, rename_name))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def rename_file(self, ftpController, file_list, detailed_file_list, current_file_index, rename_name):
		try:
			file_name = ftpController.cwd_parent(file_list[current_file_index])
			if(self.ftpController.is_dir(detailed_file_list[current_file_index])):
				ftpController.rename_dir(file_name, rename_name)
			else:
				ftpController.ftp.rename(file_name, rename_name)
			thread_request_queue.put(lambda:self.selected_file_indices.clear())
			#update file list and redraw icons
			thread_request_queue.put(lambda:self.cont_wait())
			thread_request_queue.put(lambda:self.update_file_list())
		except:
			thread_request_queue.put(lambda:self.update_status_red(_('Unable to rename, try a diffrent name or try reconnecting.')))
			thread_request_queue.put(lambda:self.lock_status_bar())

	def change_permissions_window(self):
		if self.current_file_index==-1: return
		vals = self.detailed_file_list[self.current_file_index].split()[0]
		vals = "01"[vals[0]=="d"]+"".join([str(int("".join(["01"[v!="-"] for v in vals[i:i+3]]),2)) for i in range(1,10,3)])
		self.permission_window = NameDialog(self.master, _('Rights'), self.change_permissions_thread, self.permissions_icon, _('Enter octal notation:'), vals)

	def change_permissions_thread(self):
		octal_notation = int(self.permission_window.rename_entry.get(),8)
		#Destroy permission window
		self.permission_window.destroy()
		#Show message box
		self.start_wait()
		#start thread
		self.thread = threading.Thread(target = self.change_permissions, args = (self.ftpController, self.file_list, self.selected_file_indices, octal_notation))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def change_permissions(self, ftpController, file_list, selected_file_indices, octal_notation):
		try:
			for key in selected_file_indices:
				file_name = ftpController.cwd_parent(file_list[key])
				ftpController.chmod(file_name, int(octal_notation))
			#Deselect everything
			thread_request_queue.put(lambda:self.selected_file_indices.clear())
			#update file list and redraw icons
			thread_request_queue.put(lambda:self.cont_wait())
			thread_request_queue.put(lambda:self.update_file_list())
		except:
			thread_request_queue.put(lambda:self.update_status_red(_('Unable to change permissions.')))
			thread_request_queue.put(lambda:self.lock_status_bar())

	def create_dir_window(self):
		self.create_dir_dialog = NameDialog(self.master, _('New folder'), self.create_dir_thread, self.newfolder_icon)

	def create_dir_thread(self):
		#Create thread
		self.thread = threading.Thread(target = self.create_dir, args = (self.ftpController, self.create_dir_dialog.rename_entry.get()))
		#Destroy rename window
		self.create_dir_dialog.destroy()
		#Show message box
		self.start_wait()
		#Start thread and process requests
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def create_dir(self, ftpController, dir_name):
		try:
			#Deselect everything
			thread_request_queue.put(lambda:self.selected_file_indices.clear())
			ftpController.mkd(dir_name)
			#update file list and redraw icons
			thread_request_queue.put(lambda:self.cont_wait())
			thread_request_queue.put(lambda:self.update_file_list())
		except:
			thread_request_queue.put(lambda:self.update_status_red(_('Unable to create folder, either invalid characters or not having permission may be the reason or directory already exists.')))
			thread_request_queue.put(lambda:self.lock_status_bar())

	def thread_ready(self,thread_request_queue):
		thread_request_queue.put(lambda:self.deselect_everything())
		thread_request_queue.put(lambda:self.update_file_list())
		thread_request_queue.put(lambda:self.update_status(' '))
		thread_request_queue.put(lambda:self.progress(_('You can now close the window'), _('Done')))
		thread_request_queue.put(lambda:self.console_window.enable_close_button())

	def upload_window(self):
		self.upload_dialog = OpenFileDialog(self.master, self.theme, _('Choose file(s) or folder(s) to upload'), self.upload_thread)

	def upload_thread(self):
		#Create console/terminal window
		self.create_progress_window()
		#Destroy upload window
		self.upload_dialog.destroy()
		#Set status
		self.update_status(_('Uploading file(s)...'))
		#start thread
		self.thread =  threading.Thread(target = self.upload, args = (self.ftpController, self.upload_dialog.file_list, self.upload_dialog.selected_file_indices))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()
		
	def upload(self, ftpController, file_list, selected_file_indices):
		#Thread safe progress function
		def progress(file_name, status):
			thread_request_queue.put(lambda:self.progress(file_name, status))
		#Thread safe replace function
		def replace(file_name, status):
			thread_request_queue.put(lambda:self.thread_safe_replace(file_name, status))
			thread_request_queue.join()
			with self.thread_lock:
				return self.replace_flag
		#Loop through selected items and upload them
		for index in selected_file_indices:
			if(isfile(file_list[index])):
				ftpController.upload_file(file_list[index], os.path.getsize(file_list[index]), progress, replace)
			else:
				ftpController.upload_dir(file_list[index], progress, replace)
		#Update file list and redraw icons
		self.thread_ready(thread_request_queue)

	def upload_thread_dnd(self):
		#Create console/terminal window
		self.create_progress_window()
		#Set status
		self.update_status(_('Uploading file(s)...'))
		#start thread
		self.thread =  threading.Thread(target = self.upload_dnd, args = (self.ftpController, self.dnd_file_list, self.dnd_dir))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()
		
	def upload_dnd(self, ftpController, dnd_file_list, dnd_dir = None):
		#Thread safe progress function
		def progress(file_name, status):
			thread_request_queue.put(lambda:self.progress(file_name, status))
		#Thread safe replace function
		def replace(file_name, status):
			thread_request_queue.put(lambda:self.thread_safe_replace(file_name, status))
			thread_request_queue.join()
			with self.thread_lock:
				return self.replace_flag
		#Loop through selected items and upload them
		for file in dnd_file_list:
			os.chdir('/'.join(file.split('/')[:-1]))
			file = ''.join(file.split('/')[-1:])
			if dnd_dir : ftpController.ftp.cwd(dnd_dir)
			if(isfile(file)):
				ftpController.upload_file(file, os.path.getsize(file), progress, replace)
			else:
				ftpController.upload_dir(file, progress, replace)
			if dnd_dir : ftpController.ftp.cwd('..')
		#Update file list and redraw icons
		self.thread_ready(thread_request_queue)

	def download_window(self):
		#Check number of files selected
		if(len(self.selected_file_indices) < 1): return
		self.download_dialog = OpenFileDialog(self.master, self.theme, _('Choose or Drag and Drop folder to download in'), self.download_thread, True)

	def download_thread(self):
		#Destroy download window
		self.download_dialog.destroy()
		#Create console/terminal window
		self.create_progress_window()
		#Set status
		self.update_status(_('Downloading file(s)...'))
		#Create new thread for downloading
		self.thread =  threading.Thread(target = self.download, args = (self.ftpController, self.file_list, self.detailed_file_list, self.selected_file_indices))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def download(self, ftpController, file_list, detailed_file_list, selected_file_indices):
		#Thread safe progress function
		def progress(file_name, status):
			thread_request_queue.put(lambda:self.progress(file_name, status))
		#Thread safe replace function
		def replace(file_name, status):
			thread_request_queue.put(lambda:self.thread_safe_replace(file_name, status))
			thread_request_queue.join()
			with self.thread_lock:
				return self.replace_flag
		#Loop through selected items and download them
		for index in selected_file_indices:
		#Switch to parents 
			file_name = ftpController.cwd_parent(file_list[index])
			#If a file download it to the specified directory
			if(not self.ftpController.is_dir(detailed_file_list[index])):
				ftpController.download_file(file_name, int(self.ftpController.get_properties(detailed_file_list[index])[3]), progress, replace)
			else:
				ftpController.download_dir(file_name, progress, replace)
		#Update file list and redraw icons
		self.thread_ready(thread_request_queue)

	def search_window_ask(self):
		self.search_window =  NameDialog(self.master, _('Search'), self.search_thread, self.search_icon, _('Enter file name:'))

	def search_thread(self):
		#Create console/terminal window
		self.create_progress_window()
		#Create new thread for searching
		self.thread = threading.Thread(target = self.search_file, args = (self.ftpController, self.search_window.rename_entry.get()) )
		self.search_window.destroy()
		self.thread.daemon= True
		self.thread.start()
		self.process_thread_requests()

	def search_file(self, ftpController, search_file_name):
		#Thread safe progress function
		def progress(file_name, status):
			thread_request_queue.put(lambda:self.progress(file_name, status))
		try:
			#Store the current path so that we can return to it after search
			path = ftpController.pwd()
			#Reset file lists
			thread_request_queue.put(lambda:self.selected_file_indices.clear())
			#Start searching
			ftpController.clear_search_list()
			ftpController.search(path, progress, search_file_name)
			#Add the results to file list and redraw icons
			thread_request_queue.put(lambda:self.update_search_files())	
			thread_request_queue.put(lambda:self.update_status(' '))
			#Restore path
			ftpController.ftp.cwd(path)
			#Set search performed
			thread_request_queue.put(lambda:self.search_finished())
		except:
			thread_request_queue.put(lambda:self.update_status_red(_('Unable to search, try reconnecting.')))
			thread_request_queue.put(lambda:self.lock_status_bar())
			thread_request_queue.put(lambda:self.progress(_('Failed'), _('Search')))
		thread_request_queue.put(lambda:self.progress(_('You can now close the window'), _('Done')))
		thread_request_queue.put(lambda:self.console_window.enable_close_button())

	def update_search_files(self):
		#Replace file lists with search results and redraw icons
		self.file_list.clear()
		self.detailed_file_list.clear()
		self.file_list = self.ftpController.get_search_file_list()
		self.detailed_file_list = self.ftpController.get_detailed_search_file_list()
		self.draw_icons()

	def search_finished(self):
		self.search_performed = True



	def delete_window(self, event = None):
		if(len(self.selected_file_indices) < 1): return
		self.delete_warning = WarningDialog(self.master, _('Are you sure?'), self.delete_thread, self.delete_icon, _('Delete selected files/folders?'))

	def delete_thread(self):
		#Create console/terminal window
		self.create_progress_window()
		self.replace = threading.Event()
		self.replace.clear()
		#Destroy warning window
		self.delete_warning.destroy()
		#Set current status
		self.update_status(_('Deleting file(s)...'))
		#Start thread 
		self.thread = threading.Thread(target = self.delete_item, args = (self.ftpController, self.file_list, self.detailed_file_list, self.selected_file_indices))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def delete_item(self, ftpController, file_list, detailed_file_list, selected_file_indices):
		#Thread safe progress function
		def progress(file_name, status):
			thread_request_queue.put(lambda:self.progress(file_name, status))
		#Loop through all selected files and folders
		for index in selected_file_indices:
			file_name = ftpController.cwd_parent(file_list[index])
			#If directory
			if(self.ftpController.is_dir(detailed_file_list[index])):
				ftpController.delete_dir(file_name, progress)
			#If file
			else:
				ftpController.delete_file(file_name, progress)
		#Deselect everything
		thread_request_queue.put(lambda:self.deselect_everything)
		#Update file list and redraw icons
		self.thread_ready(thread_request_queue)

	def clipboard_cut(self, event = None):
		#Check number of files in clipboard
		if(len(self.selected_file_indices) < 1): return
		self.cut = True
		self.clipboard_file_list.clear()
		for index in self.selected_file_indices:
			#If it is a search result get the clipboard path from the search result
			if self.search_performed :
				self.clipboard_path_list.append('/'.join(self.file_list[index].split('/')[:-1]))
				self.clipboard_file_list.append(''.join(self.file_list[index].split('/')[-1:]))
			else:
				self.clipboard_path_list.append(self.ftpController.pwd())
				self.clipboard_file_list.append(self.file_list[index])
			self.detailed_clipboard_file_list.append(self.detailed_file_list[index])
		self.deselect_everything()

	def clipboard_copy(self, event = None):
		#Check number of files in clipboard
		if(len(self.selected_file_indices) < 1): return
		self.copy = True
		self.clipboard_file_list.clear()
		for index in self.selected_file_indices:
			#If it is a search result get the clipboard path from the search result
			if self.search_performed:
				self.clipboard_path_list.append('/'.join(self.file_list[index].split('/')[:-1]))
				self.clipboard_file_list.append(''.join(self.file_list[index].split('/')[-1:]))
			else:
				self.clipboard_path_list.append(self.ftpController.pwd())
				self.clipboard_file_list.append(self.file_list[index])
			self.detailed_clipboard_file_list.append(self.detailed_file_list[index])
		self.deselect_everything()

	def clipboard_paste_thread_create(self, event = None):
		#Check number of files in clipboard
		if(len(self.clipboard_file_list) < 1): return
		#Create console/terminal window
		self.create_progress_window()
		#start thread
		self.thread =  threading.Thread(target = self.clipboard_paste, args = (self.ftpController, self.clipboard_path_list, self.clipboard_file_list,
										self.detailed_clipboard_file_list, self.cut, self.copy))
		self.thread.daemon = True
		self.thread.start()
		self.process_thread_requests()

	def clipboard_paste(self, ftpController, clipboard_path_list, clipboard_file_list, detailed_clipboard_file_list, cut, copy):		
		#Set current status
		thread_request_queue.put(lambda:self.update_status(_('Moving file(s)...')))
		if cut:
			#Loop through all selected files and folders
			for clipboard_path, file_name in zip(clipboard_path_list, clipboard_file_list):
				ftpController.move_dir(clipboard_path +'/'+file_name, ftpController.pwd()+'/'+file_name, self.progress, self.ask_replace)
			thread_request_queue.put(lambda:self.clear_clipboard())
			thread_request_queue.put(lambda:self.progress(_('You can now close the window'), _('Done')))
		elif copy:
			#Set current status
			thread_request_queue.put(lambda:self.update_status(_('Copying file(s)...')))
			#Loop through all selected files and folders
			for clipboard_path, file_name, file_details in zip(clipboard_path_list, clipboard_file_list, detailed_clipboard_file_list):
				#Check for file or directory, use appropriate function
				try:
					if(self.ftpController.is_dir(file_details)):
						ftpController.copy_dir(clipboard_path, file_name, self.progress, self.ask_replace)
					else:
						ftpController.copy_file(clipboard_path, file_name, int(self.ftpController.get_properties(file_details)[3]), self.progress, self.ask_replace)
				except:
					thread_request_queue.put(lambda:self.progress(_('Failed to copy file/folder'), file_name))
			thread_request_queue.put(lambda:self.clear_clipboard())
			thread_request_queue.put(lambda:self.progress(_('You can now close the window'), _('Done')))
		#update file list and redraw icons
		self.thread_ready(thread_request_queue)

	def clear_clipboard(self):
		self.clipboard_file_list.clear()
		self.detailed_clipboard_file_list.clear()
		self.clipboard_path_list.clear()
		self.cut = False
		self.copy = False


	def ask_replace(self, file_name, status):
		#Check if replace all has been selected
		if self.replace_all: return True
		#Check if skip all has been selected
		if self.skip_all: return False
		#Create replace dialog
		self.replace_window = ReplaceDialog(self.console_window.console_dialog_window, _('Conflicting files'), self.copy_icon, file_name+': '+status+', '+_('Replace')+'?')
		#Loop till a button is pressed
		while self.replace_window.command=='':
			self.replace_window.replace_dialog_window.update()
		if (self.replace_window.command=='skip'): return False
		elif (self.replace_window.command=='replace'): return True
		elif (self.replace_window.command=='skip_all'):
			self.skip_all = True
			return False 
		elif (self.replace_window.command=='replace_all'):
			self.replace_all = True
			return True

	def thread_safe_replace(self, file_name, status):
		with self.thread_lock:
			self.replace_flag = self.ask_replace(file_name, status)

	def reset_replace(self):
		#Set replace all and skip all mode to false
		self.replace_all = False
		self.skip_all = False

	def process_thread_requests(self):
		while not thread_request_queue.empty():
			thread_request_queue.get()()
			thread_request_queue.task_done()
		if(self.thread.is_alive()):
			self.master.after(5, self.process_thread_requests)

	def create_progress_window(self):
		self.console_window = ConsoleDialog(self.master, self.console_icon, self.reset_replace)

	def progress(self, file_name, status):
		#If it is a progress
		if('%' in status):
			self.console_window.progress(status)
			return
		if(status == 'newline'):
			self.console_window.insert('')
			return
		#Print to console
		self.console_window.insert(status+': '+file_name)

	def info(self):
		self.info_window = AboutDialog(self.master, _('About'), self.icon, 'PySCP v5.0', '© Vishnu Shankar,\n NeiroN') 

	def disable_toolbar(self, event = None):
		#Disable all buttons
		self.canvas.grab_set()
		#Disable mouse action
		self.canvas.unbind("<Button-1>")
		self.canvas.unbind("<Double-Button-1>")	 
		self.canvas.unbind("<Control-Button-1>")
		self.canvas.unbind("<B1-Motion>")
		self.canvas.unbind("<Motion>")

	def enable_toolbar(self, event = None):
		#Enable all buttons
		self.canvas.grab_release()
		#Enable mouse action
		self.canvas.bind("<Button-1>", self.mouse_select)
		self.canvas.bind("<Double-Button-1>" , self.change_dir)	 
		self.canvas.bind("<Control-Button-1>", self.ctrl_select)
		self.canvas.bind("<B1-Motion>", self.drag_select)
		self.canvas.bind("<Motion>", self.update_status_and_mouse)

	def start_wait(self, event = None):
		if not self.change_status: return
		if self.continue_wait:
			self.continue_wait = False
			return
		self.disable_toolbar()
		self.wait_anim = True
		self.wait_frame_index = 1
		self.master.after(100, self.do_wait)

	def cont_wait(self, event = None):
		self.continue_wait = True

	def do_wait(self, event = None):
		if not self.wait_anim: return
		#make sure frame index is not above 4
		if self.wait_frame_index==4:
			self.wait_frame_index = 0
		#clear and draw the correct frame
		self.canvas.delete('all')
		self.canvas.create_image(self.canvas_width/2, self.canvas_height/2, image = self.wait_frames[self.wait_frame_index])
		#update frame index
		self.wait_frame_index += 1
		#call the do wait function after some time to update the animation
		if(self.wait_frame_index == 1):
			self.master.after(400, self.do_wait)
		else:
			self.master.after(100, self.do_wait)

	def end_wait(self, event = None):
		self.wait_anim = False
		self.enable_toolbar()

	def problem(self, event = None):
		self.end_wait()
		self.canvas.delete('all')
		self.canvas.create_image(self.canvas_width/2, self.canvas_height/2, image = self.problem_icon)

#Program entry point
#Tell windows not to DPI scale this application
if(platform.system()=='Windows' and platform.release() != '7'):
	windll.shcore.SetProcessDpiAwareness(2)
#Create root window
root = Tk()
#Include the theme and tkdnd libraries
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
arc_theme_path = (dname+'/Theme')
tkdnd_path = (dname+'/TkDND')
locale = getdefaultlocale()
translate = {}
history = [{"host":"","user":"","password":"","type":"SFTP","port":22}]
if isfile(join(dname,"history.json")):
	history = json.loads(open(join(dname,"history.json"),"rb").read().decode("utf-8"))
if isfile(join(dname,"language", locale[0]+".json")):
	translate = json.loads(open(join(dname,"language", locale[0]+".json"),"rb").read().decode("utf-8"))
def _(s):
	if s in translate.keys():
		return translate[s]
	else:
		return s
root.tk.eval('lappend auto_path {%s}' % arc_theme_path)
root.tk.eval('lappend auto_path {%s}' % tkdnd_path)
root.tk.eval('package require tkdnd')
#Queue for handling threads
global thread_request_queue
thread_request_queue = queue.Queue()
#Initilize the app
PySCP = App(root)
if len(sys.argv)>=2:
	PySCP.connect_to_ftp(uri=sys.argv[1])
#Initialize mainloop
root.mainloop()

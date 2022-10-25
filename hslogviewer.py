import asyncio
import os
import re
import sys
import threading
import winreg
from ctypes import windll
from enum import IntEnum
from tkinter import *
from tkinter.ttk import *

error_lines = ''
try:
    _win_v = sys.getwindowsversion()
    if _win_v.major == 6 and _win_v.minor == 1:
        windll.user32.SetProcessDPIAware()
    else:
        windll.shcore.SetProcessDpiAwareness(2)
except Exception as e:
    error_lines += str(e) + '\n'

hs_dir = ''
try:
    reg_pos = r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Hearthstone'
    handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_pos)
    hs_dir, _type = winreg.QueryValueEx(handle, 'InstallLocation')
    winreg.CloseKey(handle)
except Exception as e:
    error_lines += str(e) + '\n'
hs_dir += '\\Logs\\'
if not os.path.exists(hs_dir):
    error_lines += '找不到Log文件夹。关闭工具，把所有文件移动到\nHearthstone.exe所在文件夹后再试。'
HS_LOG_PATH = hs_dir + 'Power.log'

APPDATA_DIR = os.getenv('LOCALAPPDATA')
log_config_p0 = APPDATA_DIR + '\\Blizzard\\Hearthstone\\'
log_config_path = APPDATA_DIR + r'\Blizzard\Hearthstone\log.config'
if not os.path.exists(log_config_path):
    try:
        with open(log_config_path, 'w', encoding='utf-8') as ff:
            print("""[Achievements]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=False
[Arena]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=False
[Decks]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=False
[FullScreenFX]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=False
[LoadingScreen]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=False
[Power]
LogLevel=1
FilePrinting=True
ConsolePrinting=False
ScreenPrinting=False
Verbose=True""", file=ff)
            error_lines += '已创建log.config，需重启游戏。\n'
    except Exception as e:
        error_lines += str(e) + '\n'
if not error_lines:
    error_lines = '（检测正常）\n'
R1 = re.compile(r'TAG_CHANGE Entity=\[entityName=(.*) id=(\d*) zone=(.*) zonePos=(\d*) cardId=(.*) player=(\d*)] '
                r'tag=(.*) value=(.*)')
R2 = re.compile(r'FULL_ENTITY - Updating \[entityName=(.*) id=(\d*) zone=(.*) zonePos=(\d*) cardId=(.*) '
                r'player=(\d*)] CardID=(.*)')
R3 = re.compile(r'FULL_ENTITY - Creating ID=(\d*) CardID=(.*)')
R4 = re.compile(r'tag=(.*) value=(.*)')
R5 = re.compile(r'SUB_SPELL_START - SpellPrefabGUID=(.*) Source=(\d*) TargetCount=(\d*)')
R6 = re.compile(r'Targets\[0] = \[entityName=(.*) id=(\d*) zone=(.*) zonePos=(\d*) cardId=(.*) player=(\d*)]')
R7 = re.compile(r'Source = \[entityName=(.*) id=(\d*) zone=(.*) zonePos=(\d*) cardId=(.*) player=(\d*)]')
R8 = re.compile(r'Player EntityID=(\d*) PlayerID=(\d*) GameAccountId=\[hi=(\d*) lo=(\d*)]')
R9 = re.compile(r'TAG_CHANGE Entity=(.*) tag=(.*) value=(.*)')
R10 = re.compile(r'PlayerID=(.*), PlayerName=(.*)')
R11 = re.compile(r'id=(.*) Player=(.*) TaskList=(.*) ChoiceType=(.*) CountMin=(.*) CountMax=(.*)')
R12 = re.compile(r'HIDE_ENTITY - Entity=\[entityName=(.*) id=(\d*) zone=(.*) zonePos=(\d*) cardId=(.*) player=(\d*)] '
                 r'tag=(.*) value=(.*)')
R13 = re.compile(r'SHOW_ENTITY - Updating Entity=\[entityName=(.*) id=(\d*) zone=(.*) zonePos=(\d*) cardId=(.*) '
                 r'player=(\d*)] CardID=(.*)')
R14 = re.compile(r'SHOW_ENTITY - Updating Entity=(\d*) CardID=(.*)')
R15 = re.compile(r'HIDE_ENTITY - Entity=(\d*) tag=(.*) value=(.*)')


class T(IntEnum):
    NONE = 0
    GAME = 1
    GAME_ = 2
    PLAYER = 3
    PLAYER_ = 4
    CREATE = 5
    CREATE_ = 6
    UPDATE = 7
    UPDATE_ = 8
    CHANGE = 9
    CHANGE_ = 10
    HIDE = 11
    HIDE_ = 12


class MainWindow(Tk):
    def __init__(self):
        global error_lines
        super().__init__()
        self.title('炉石日志速查工具 v0.0.2 221026')
        self.geometry('1600x980+100+30')
        self.wm_attributes('-topmost', True)
        self.fontsize = 12
        self.loop = None

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(4, weight=1)

        self.button1 = Button(self, text=f'{error_lines}检测炉石文件夹/Log/Power.log', command=self.main_start1)
        self.button1.grid(row=0, column=0, sticky=NW)
        self.button2 = Button(self, text='检测当前文件夹Power.log', command=self.main_start2)
        self.button2.grid(row=1, column=0, sticky=NW)

        self.configframe = LabelFrame(self, text='设置')
        self.configframe.grid(row=2, column=0, columnspan=3, sticky=NSEW)
        self.widget1 = Label(self.configframe, text='第')
        self.widget1.grid(row=1, column=0)
        self.widget2 = Entry(self.configframe, width=3, justify=RIGHT)
        self.widget2.insert(END, '1')
        self.widget2.grid(row=1, column=1)
        self.widget3 = Label(self.configframe, text='/0 局')
        self.widget3.grid(row=1, column=2)
        self.check1 = IntVar(value='1')
        self.check2 = IntVar(value='1')
        self.check3 = IntVar(value='0')
        self.check4 = IntVar(value='0')
        self.check5 = IntVar(value='0')
        self.check6 = IntVar(value='0')
        self.checki = [self.check1, self.check2, self.check3, self.check4, self.check5, self.check6]
        self.widget4 = Checkbutton(self.configframe, text='创建', variable=self.check1)
        self.widget4.grid(row=1, column=3)
        self.widget5 = Checkbutton(self.configframe, text='更新', variable=self.check2)
        self.widget5.grid(row=1, column=4)
        self.widget6 = Checkbutton(self.configframe, text='改变（慢）', variable=self.check3)
        self.widget6.grid(row=1, column=6)
        self.widget7 = Label(self.configframe, text='　　后面三项基本重复')
        self.widget7.grid(row=1, column=7)
        self.widget8 = Checkbutton(self.configframe, text='创建_', variable=self.check4)
        self.widget8.grid(row=1, column=8)
        self.widget9 = Checkbutton(self.configframe, text='更新_', variable=self.check5)
        self.widget9.grid(row=1, column=9)
        self.widget10 = Checkbutton(self.configframe, text='改变_', variable=self.check6)
        self.widget10.grid(row=1, column=10)
        self.widget11 = Label(self.configframe, text='　　ID=')
        self.widget11.grid(row=1, column=11)
        self.widget12 = Entry(self.configframe, width=4)
        self.widget12.grid(row=1, column=12)
        self.widget13 = Label(self.configframe, text='　CardId≈')
        self.widget13.grid(row=1, column=13)
        self.widget14 = Entry(self.configframe, width=10)
        self.widget14.grid(row=1, column=14)
        self.widget15 = Label(self.configframe, text='　有TAG')
        self.widget15.grid(row=1, column=15)
        self.widget16 = Entry(self.configframe, width=20)
        self.widget16.grid(row=1, column=16)
        self.widget17 = Button(self.configframe, width=8, text='更新设置', command=self.confirm)
        self.widget17.grid(row=1, column=17)
        self.widget18 = Label(self.configframe, text='清空重列')
        self.widget18.grid(row=1, column=18)

        self.treeframe = LabelFrame(self, text='记录')
        self.treeframe.grid(row=3, column=0, columnspan=3, sticky=NSEW)
        self.treeview = Treeview(self.treeframe, columns=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], show='headings',
                                 height=20)
        self.treeview.column('a', width=40, anchor=W)
        self.treeview.column('b', width=40, anchor=W)
        self.treeview.column('c', width=130, anchor=W)
        self.treeview.column('d', width=20, anchor=W)
        self.treeview.column('e', width=110, anchor=W)
        self.treeview.column('f', width=70, anchor=W)
        self.treeview.column('g', width=50, anchor=W)
        self.treeview.column('h', width=1100, anchor=W)
        self.treeview.heading('a', text='序号')
        self.treeview.heading('b', text='ID')
        self.treeview.heading('c', text='牌编号')
        self.treeview.heading('d', text='来源')
        self.treeview.heading('e', text='类型')
        self.treeview.heading('f', text='时间')
        self.treeview.heading('g', text='TAG数')
        self.treeview.heading('h', text='预览')
        # self.treeview.bind('<ButtonRelease-1>', self.treeview_click)
        self.treeview.bind('<<TreeviewSelect>>', self.treeview_click)
        self.scrollbar0 = Scrollbar(self.treeframe, orient="vertical", command=self.treeview.yview)
        self.treeview.grid(row=0, column=0, sticky=NSEW)
        self.scrollbar0.grid(row=0, column=1, sticky=NS)
        self.treeview.configure(yscrollcommand=self.scrollbar0.set)

        self.textlable1 = Label(self, text='上次点击', font=('微软雅黑', self.fontsize), anchor=NW, width=400)
        self.textlable1.grid(row=4, column=0, sticky=NSEW)
        self.textlable2 = Label(self, text='上上次点击', font=('微软雅黑', self.fontsize), anchor=NW, width=400)
        self.textlable2.grid(row=4, column=1, sticky=NSEW)
        self.textlable3 = Label(self, text='上上次点击', font=('微软雅黑', self.fontsize), anchor=NW, width=400)
        self.textlable3.grid(row=4, column=2, sticky=NSEW)

        self.Menu = Menu(self, tearoff=False)
        self.Menu.add_cascade(label='字体大小 +', command=self.font_plus)
        self.Menu.add_cascade(label='字体大小 -', command=self.font_minus)
        self.Menu.add_cascade(label='打开日志配置log.config路径', command=self.pop_dir)
        self.Menu.add_separator()
        self.Menu.add_cascade(label='v0.0.2 221026')
        self.bind('<Button-3>', self.popupmenu)
        self.logviewer = None
        self.game_i = 1
        self.check_i_last = [1, 1, 0, 0, 0, 0]
        self.id_last = None
        self.cardid_last = ''
        self.tag_last = ''
        self.entity_count = 0
        self.mainloop()

    def popupmenu(self, event):
        try:
            self.Menu.post(event.x_root, event.y_root)
        finally:
            self.Menu.grab_release()

    def font_plus(self):
        self.fontsize += 1
        self.textlable1['font'] = ('微软雅黑', self.fontsize)
        self.textlable2['font'] = ('微软雅黑', self.fontsize)
        self.textlable3['font'] = ('微软雅黑', self.fontsize)

    def font_minus(self):
        if self.fontsize > 6:
            self.fontsize -= 1
            self.textlable1['font'] = ('微软雅黑', self.fontsize)
            self.textlable2['font'] = ('微软雅黑', self.fontsize)
            self.textlable3['font'] = ('微软雅黑', self.fontsize)

    def pop_dir(event):
        os.startfile(log_config_p0)

    def get_loop(self, loop):
        self.loop = loop
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def main_start1(self):
        self.logviewer = self.LogViewer(HS_LOG_PATH)
        self.main_start()

    def main_start2(self):
        self.logviewer = self.LogViewer('Power.log')
        self.main_start()

    def main_start(self):
        self.button1.destroy()
        self.button2.destroy()
        coroutine1 = self.handler()
        new_loop = asyncio.new_event_loop()
        t = threading.Thread(target=self.get_loop, args=(new_loop,))
        t.daemon = True
        t.start()
        asyncio.run_coroutine_threadsafe(coroutine1, new_loop)

    def treeview_click(self, event):
        _a = self.treeview.selection()[0]
        _v = self.treeview.item(_a, 'values')
        self.textlable3['text'] = self.textlable2['text']
        self.textlable2['text'] = self.textlable1['text']
        self.textlable1['text'] = '\n'.join(_v[7].split('　|　'))

    def confirm(self):
        changed = False
        new_game_i_str = self.widget2.get()
        if new_game_i_str.isdigit():
            new_game_i_int = int(new_game_i_str)
            if new_game_i_int != self.game_i:
                self.game_i = new_game_i_int
                changed = True
        id_i_str = self.widget12.get()
        if id_i_str == '' and self.id_last is not None:
            self.id_last = None
            changed = True
        if id_i_str.isdigit():
            d_i_int = int(id_i_str)
            if d_i_int != self.id_last:
                self.id_last = d_i_int
                changed = True
        temp_text = self.widget14.get()
        if temp_text != self.cardid_last:
            self.cardid_last = temp_text
            changed = True
        temp_text = self.widget16.get()
        if temp_text != self.tag_last:
            self.tag_last = temp_text
            changed = True
        for i in range(6):
            _v = self.checki[i].get()
            if self.check_i_last[i] != _v:
                self.check_i_last[i] = _v
                changed = True
        if changed and self.logviewer:
            self.logviewer.changed = True

    class LogViewer:
        def __init__(self, path):
            self.path = path
            self.file = None
            self.last_size = 0
            self.pos = 0
            self.complete = True
            self.updated = False
            self.changed = False
            self.players = {}
            self.name2eid = {}
            self.info = []

        def update(self):
            if not self.path:
                return
            if os.path.exists(self.path):
                if self.file is None:
                    self.file = open(self.path, 'r', encoding='utf-8')
                else:
                    size = os.path.getsize(self.path)
                    if size == self.last_size:
                        return
                    if size < self.last_size:
                        self.pos = 0
                    self.last_size = size
                    self.file.seek(self.pos)
                    lines = self.file.readlines()
                    self.pos = self.file.tell()
                    if lines:
                        self.updated = True
                        self.lines_handler(lines)
            else:
                pass

        def lines_handler(self, lines):
            last_item = None
            for line in lines:
                # s_head = line[0]
                s_time = line[2:10]
                line0 = line[19:].strip()
                if '() - ' in line0:
                    source, info0 = line0.split('() - ', 1)
                    info1 = info0.strip()
                    if source == 'GameState.DebugPrintPower' or source == 'PowerTaskList.DebugPrintPower':
                        if last_item is not None:
                            if info1.startswith('tag='):
                                _tag, value = info1.split(' value=', 1)
                                last_item[5].append((_tag[4:], value))
                                continue
                            self.info[-1].append(last_item)
                            last_item = None
                        if info1.startswith('GameEntity'):
                            last_item = (1, '', source, T.GAME if source[0] == 'G' else T.GAME_, s_time, [])
                        elif info1.startswith('Player'):
                            result = R8.match(info1)
                            last_item = (int(result.group(1)), '', source,
                                         T.PLAYER if source[0] == 'G' else T.PLAYER_, s_time,
                                         [('PlayerID', result.group(2)),
                                          ('hi', result.group(3)),
                                          ('lo', result.group(4))])
                        elif info1.startswith('FULL_ENTITY - Creating'):
                            result = R3.match(info1)
                            last_item = (int(result.group(1)), result.group(2), source,
                                         T.CREATE if source[0] == 'G' else T.CREATE_, s_time, [])
                        elif info1.startswith('FULL_ENTITY - Updating'):
                            result = R2.match(info1)
                            self.name2eid[result.group(1)] = result.group(2)
                            last_item = (int(result.group(2)), result.group(7), source,
                                         T.UPDATE if source[0] == 'G' else T.UPDATE_, s_time, [])
                        elif info1.startswith('SHOW_ENTITY - Updating'):
                            result = R13.match(info1)
                            if result:
                                self.name2eid[result.group(1)] = result.group(2)
                                last_item = (int(result.group(2)), result.group(7), source,
                                             T.UPDATE if source[0] == 'G' else T.UPDATE_, s_time, [])
                            else:
                                result = R14.match(info1)
                                last_item = (int(result.group(1)), result.group(2), source,
                                             T.UPDATE if source[0] == 'G' else T.UPDATE_, s_time, [])
                        elif info1.startswith('TAG_CHANGE'):
                            result = R1.match(info1)
                            if result:
                                last_item = (int(result.group(2)), result.group(5), source,
                                             T.CHANGE if source[0] == 'G' else T.CHANGE_,
                                             s_time, [(result.group(7), result.group(8))])
                            else:
                                result = R9.match(info1)
                                _gameentity = result.group(1)
                                if _gameentity == 'GameEntity':
                                    eid = 1
                                    if result.group(2) == 'STATE' and result.group(3) == 'COMPLETE':
                                        self.complete = True
                                elif _gameentity.isdigit():
                                    eid = int(_gameentity)
                                elif _gameentity in self.name2eid:
                                    eid = int(self.name2eid[_gameentity])
                                elif _gameentity in self.players:
                                    eid = int(self.players[_gameentity]) + 1  # 战棋会错
                                else:
                                    eid = 0
                                last_item = (eid, '' if eid > 0 else _gameentity, source,
                                             T.CHANGE if source[0] == 'G' else T.CHANGE_,
                                             s_time, [(result.group(2), result.group(3))])
                        elif info1.startswith('HIDE_ENTITY'):
                            result = R12.match(info1)
                            if result:
                                last_item = (int(result.group(2)), result.group(5), source,
                                             T.CHANGE if source[0] == 'G' else T.CHANGE_,
                                             s_time, [(result.group(7), result.group(8))])
                            else:
                                result = R15.match(info1)
                                last_item = (int(result.group(1)), '', source,
                                             T.CHANGE if source[0] == 'G' else T.CHANGE_,
                                             s_time, [(result.group(2), result.group(3))])
                        elif info1.startswith('BLOCK_START'):
                            ...
                        elif info1.startswith('CREATE_GAME'):
                            if self.complete:
                                self.info.append([])
                                self.complete = False
                        else:
                            ...
                    elif source == 'GameState.DebugPrintGame':
                        if info1.startswith('PlayerID='):
                            result = R10.match(info1)
                            self.players[result.group(2)] = result.group(1)
                    elif source == 'GameState.DebugPrintEntityChoices':
                        if info1.startswith('id='):
                            result = R11.match(info1)
                            self.players[result.group(2)] = result.group(1)
                    elif source == 'PowerTaskList.DebugPrintPower':
                        ...
                    else:
                        ...

        def __del__(self):
            if self.file:
                self.file.close()

    async def handler(self):
        while True:
            try:
                self.logviewer.update()
                if self.logviewer.changed:
                    for i in self.treeview.get_children():
                        self.treeview.delete(i)
                    self.entity_count = 0
                    self.logviewer.changed = False
                    self.logviewer.updated = True
                if self.logviewer.updated:
                    self.widget3['text'] = f'/{len(self.logviewer.info)} 局'
                    if len(self.logviewer.info) >= self.game_i:
                        _entis = self.logviewer.info[self.game_i - 1]
                        for i in range(self.entity_count, len(_entis)):
                            _enti = _entis[i]
                            if _enti[3] == T.CREATE and self.check_i_last[0] == 0:
                                continue
                            if _enti[3] == T.UPDATE and self.check_i_last[1] == 0:
                                continue
                            if _enti[3] == T.CHANGE and self.check_i_last[2] == 0:
                                continue
                            if _enti[3] == T.CREATE_ and self.check_i_last[3] == 0:
                                continue
                            if _enti[3] == T.UPDATE_ and self.check_i_last[4] == 0:
                                continue
                            if _enti[3] == T.CHANGE_ and self.check_i_last[5] == 0:
                                continue
                            if self.id_last and _enti[0] != self.id_last:
                                continue
                            if self.cardid_last and self.cardid_last not in _enti[1]:
                                continue
                            if self.tag_last and self.tag_last not in [x[0] for x in _enti[5]]:
                                continue
                            self.treeview.insert('', END, values=(
                                i + 1,
                                _enti[0],
                                _enti[1],
                                _enti[2],
                                str(_enti[3]),
                                _enti[4],
                                len(_enti[5]),
                                '　|　'.join((f'{x[0]} = {x[1]}' for x in _enti[5]))
                            ))
                        self.entity_count = len(_entis)
                    self.logviewer.updated = False
                await asyncio.sleep(0.005)
            except Exception as ee:
                print(ee)


if __name__ == '__main__':
    MainWindow()

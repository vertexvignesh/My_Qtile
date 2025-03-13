import sys
import os
import re
import socket
import subprocess
import psutil
import time
import RadeonMaster
from threading import Timer , Thread
from typing import List
from libqtile import widget as qwidget 
from libqtile.widget import base
from libqtile import layout, bar, hook, qtile 
from libqtile.config import Click, Drag, Group, Key, Match, Screen, Rule , KeyChord
from libqtile.command import lazy
from libqtile.widget import Spacer
from qtile_extras import widget
from qtile_extras.popup.toolkit import PopupRelativeLayout,PopupImage,PopupText , PopupGridLayout
from qtile_extras.widget.decorations import BorderDecoration , PowerLineDecoration

v_thread = None

def show_volume(qtile,action):

    global v_thread , volume_layout

    subprocess.run(["amixer", "-q", "sset", "Master", action])

    if v_thread and v_thread.is_alive():
        
            volume_layout.kill()
            v_thread.cancel()

    current_volume = subprocess.getoutput(r"amixer get Master | grep -oP '\[\d+%\]' | head -n 1 | sed 's/\[\|\]//g'").replace("%","")
    
    if current_volume == "0":

        controls = [
            PopupText(
            font="FontAwesome",
            row = 0,
            col = 0,
            text = "",
            fontsize = 30,
            foreground = "#000000" ,
            h_align = "center"
            ),
        ]
    
    elif 0 < int(current_volume) < 30 :

        controls = [
            PopupText(
            font="FontAwesome",
            row = 0,
            col = 0,
            text ="",
            fontsize = 40,
            foreground = "#000000" ,
            h_align = "center"
            ),
        ]

    else:
        controls = [
            PopupText(
            font="FontAwesome",
            row = 0,
            col = 0,
            text = "",
            fontsize = 40,
            foreground = "#000000" ,
            h_align = "center"
            ),
        ]

    controls.append(
        PopupText(
            font="FontAwesome",
            row = 0,
            col = 1,
            text = current_volume + "%",
            fontsize = 22,
            foreground = "#000000" ,
            h_align = "center"
            ),
    )

    volume_layout = PopupGridLayout(
        qtile,
        rows=1, cols=2,
        width=120,
        height=50,
        controls=controls,
        background="#33323262",
    )

    volume_layout.show(centered=True)
    v_thread = Timer(2,volume_layout.kill)
    v_thread.start()

class AMDgpu(base.ThreadPoolText):
    """
    A simple widget to display AMD_GPU load and temparature.
    """

    defaults = [
        (
            "format",
            "{GPU_temp} {load_percent}% {vram_usage_percent}% {vram_used} / {vram_total}",
            "GPU display format",
        ),
        ("bus_address",None,"bus address of GPU"),
        ("update_interval", 1.0, "Update interval for the GPU widget"),
    ]

    def __init__(self, **config):
        super().__init__("", **config)
        self.gpus = RadeonMaster.GPU()
        self.add_defaults(AMD_GPU.defaults)

    def poll(self):

        variables = dict()

        if self.bus_address is None:
            gpu_info = self.gpus.get_output(0)
        else:
            gpu_info = self.gpus.get_output(self.bus_address)

        variables["GPU_temp"] = gpu_info["GPU temp"]
        variables["load_percent"] = gpu_info["GPU usage"]
        variables["vram_usage_percent"] = gpu_info["VRAM PERCENTAGE"]
        variables["vram_used"] = gpu_info["VRAM Used"]
        variables["vram_total"] = gpu_info["VRAM Total"]
        return self.format.format(**variables) 

def powerlock(qtile):

   """
    cancel 
    shutdown
    reboot 
    """

mod = "mod4"
mod2 = "control"
home = os.path.expanduser('~')

keys = [

    Key([mod], "a", lazy.window.toggle_fullscreen() , desc = "make the current window as fullscreen"),
    Key([mod], "q", lazy.window.kill() , desc = "close the current window"),
    Key([mod, "shift"], "r", lazy.reload_config(), desc = "restart the qtile"),
    Key([mod],"KP_END",lazy.spawncmd()),

# CHANGE FOCUS
    Key([mod], "Up", lazy.layout.up() ),
    Key([mod], "Down", lazy.layout.down()),
    Key([mod], "Left", lazy.layout.left()),   
    Key([mod], "Right", lazy.layout.right()), 
    Key([mod], "space", lazy.next_layout(),desc="change the tilling mode"),

#GROUP SHORTCUT

    Key([mod],"KP_Insert",lazy.group["0"].toscreen()),
    Key([mod],"KP_End",lazy.group["1"].toscreen()),
    Key([mod],"KP_Down",lazy.group["2"].toscreen()),
    Key([mod],"KP_Next",lazy.group["3"].toscreen()),
    Key([mod],"KP_Left",lazy.group["4"].toscreen()),
    Key([mod],"KP_Begin",lazy.group["5"].toscreen()),
    Key([mod],"KP_Right",lazy.group["6"].toscreen()),
    Key([mod],"KP_Home",lazy.group["7"].toscreen()),
    Key([mod],"KP_Up",lazy.group["8"].toscreen()),
    Key([mod],"KP_Prior",lazy.group["9"].toscreen()),


    Key(["mod1"], "Right",
        lazy.layout.grow_right(),
        lazy.layout.grow(),
        lazy.layout.increase_ratio(),
        lazy.layout.delete(),
        ),
    Key(["mod1"], "Left",
        lazy.layout.grow_left(),
        lazy.layout.shrink(),
        lazy.layout.decrease_ratio(),
        lazy.layout.add(),
        ),
    Key(["mod1"], "Up",
        lazy.layout.grow_up(),
        lazy.layout.grow(),
        lazy.layout.decrease_nmaster(),
        ),
    Key(["mod1"], "Down",
        lazy.layout.grow_down(),
        lazy.layout.shrink(),
        lazy.layout.increase_nmaster(),
        ),

    Key([mod], "f", lazy.layout.flip() , desc = "Flip the window invertly"),
    Key([mod, "shift"], "space", lazy.window.toggle_floating()),
    Key([mod], "s", lazy.spawn("rofi -show drun") , desc = "open the rofi drun for search apps"),
    Key([mod],"Print",lazy.spawn("flameshot gui")),
    Key([mod],"f",lazy.spawn("thunar")),
    Key([mod],"KP_Enter",lazy.spawn("firefox")),
    Key([mod],"t",lazy.spawn("telegram-dekstop")),
    Key([mod],"z",lazy.spawncmd()),
    Key([mod],"KP_Add",lazy.function(lambda qtile: show_volume(qtile, "5%+"))),
    Key([mod],"KP_Subtract",lazy.function(lambda qtile: show_volume(qtile, "5%-"))),
    Key([mod],"KP_Decimal",lazy.function(lambda qtile: show_volume(qtile, "toggle")))
    ]

groups = []
group_names = ["0","1","2", "3", "4", "5", "6", "7", "8", "9",]
group_labels = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9",]

for i in range(len(group_names)):
    groups.append(
        Group(
            name=group_names[i],
            layout="Mondatall",
            label=group_labels[i],
        ))

for i in groups:
    keys.extend([

        #CHANGE WORKSPACES
        Key([mod], "Tab", lazy.screen.next_group()),
        Key([mod], "BackSpace", lazy.screen.prev_group()),

    ])

layout_theme = {"margin":5,
                "border_width":2,
                "border_focus": "#40704C",
                "border_normal": "#4c566a"
                }

layouts = [
    layout.MonadTall(**layout_theme),
    layout.Max(**layout_theme),
]

colors = [  "#2F343F", # color 0
            "#2F343F", # color 1
            "#c0c5ce", # color 2
            "#fba922", # color 3
            "#3384d0", # color 4
            "#f3f4f5", # color 5
            "#cd1f3f", # color 6
            "#62FF00", # color 7
            "#6682C0", # color 8
            "#a9a9a9"] # color 9

powerline_l = {"decorations":[PowerLineDecoration(path="arrow_left")]}

widgets_list = [
            widget.GroupBox(font="FontAwesome",
                    fontsize = 20,
                    margin_y = 0,
                    margin_x = 0,
                    padding_y = 5,
                    padding_x = 5,
                    borderwidth = 0,
                    disable_drag = True,
                    active = colors[9],
                    inactive = colors[5],
                    highlight_method = "text",
                    this_current_screen_border = colors[3],
                    foreground = colors[5],
                    background = "#3FA361",
                    decorations = [

                        PowerLineDecoration(path= "arrow_left")
                    ]
                    ),
            widget.Prompt( 
                background = "#68B644" , 
                foreground = "#ffffff" , 
                fontsize = 14 ,
                decorations = [

                        PowerLineDecoration(path= "arrow_left")
                    ]
                ),
            widget.Sep(
                        linewidth = 1,
                        padding = 10,
                        foreground = colors[1],
                        background = colors[1]
                        ),
            widget.WindowName(
                    font="FontAwesome",
                    fmt='<b>{}</b>',
                    fontsize = 14,
                    empty_group_string="          CONSISTENCY > MOTIVATION   ",
                    max_chars=40,
                    foreground = colors[5],
                    background = colors[1],
                    ),
            widget.TextBox(
                        font="FontAwesome",
                        text=":",
                        foreground="#6130D4",
                        background=colors[1],
                        fontsize=16,
                        decorations = [
                            BorderDecoration(
                                group = True,
                                colour="#6130D4",
                                border_width = [0,0,2,0],
                                padding_y = 2
                                )
                                ]
                        ),
            widget.ThermalSensor(
                        foreground = "#6130D4",
                        background = colors[1],
                        tag_sensor="Package id 0",
                        fontsize = 14,
                        metric = True,
                        padding = 3,
                        threshold = 80,
                        decorations = [
                            BorderDecoration(
                                group = True,
                                colour="#6130D4",
                                border_width = [0,0,2,0],
                                padding_y = 2
                                )
                                ]
                        ),
            #qwidget.Test(),
            widget.Sep(
                        linewidth = 0,
                        padding = 10,
                        foreground = colors[1],
                        background = colors[1]
                        ),
            widget.TextBox(
                        font="FontAwesome",
                        text="",
                        foreground="#A530D4",
                        background=colors[1],
                        fontsize=16,
                        decorations = [
                            BorderDecoration(
                                group = True,
                                colour="#A530D4",
                                border_width = [0,0,2,0],
                                padding_y = 2
                                )
                                ]
                        ),
            widget.Memory(
                        font="Noto Sans",
                        format=":{MemUsed:.2f}MB/{MemTotal:.2f}MB",
                        update_interval = 1,
                        fontsize = 12,
                        foreground = "#A530D4",
                        background = colors[1],
                        decorations = [
                            BorderDecoration(
                                group = True,
                                colour="#A530D4",
                                border_width = [0,0,2,0],
                                padding_y = 2
                            )
                        ]
                    ),
            widget.Sep(
                    linewidth = 1,
                    padding = 10,
                    foreground = colors[1],
                    background = colors[1]
                        ),
            widget.Clock(
                    foreground = "#D43082",
                    background = colors[1],
                    fontsize = 12,
                    format="%a %d-%m-%Y %I:%M %p",
                    decorations = [
                            BorderDecoration(
                                group = True,
                                colour="#D43082",
                                border_width = [0,0,2,0],
                                padding_y = 2
                                )
                                ]
                    ),
            widget.Sep(
                    linewidth = 1,
                    padding = 10,
                    foreground = colors[1],
                    background = colors[1],
                    decorations = [
                            PowerLineDecoration(
                                path = "forward_slash"
                            )
                            ]
                    ),
            widget.Systray(
                    icon_size=20,
                    padding = 4,
                    background = "#853B3F",
                    ),
            widget.Sep(
                    linewidth = 1,
                    padding = 10,
                    foreground = "#853B3F",
                    background ="#853B3F"
                        ),
            ]

screens = [Screen(
    wallpaper = "/home/vicky/.config/qtile/wallpaper/astronaut 2.jpg",
    wallpaper_mode='fill' ,
    top=bar.Bar(widgets_list, size=27))]


# MOUSE CONFIGURATION
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []

# ASSIGN APPLICATIONS TO A SPECIFIC GROUPNAME
# BEGIN

#########################################################
################ assgin apps to groups ##################
#########################################################
# @hook.subscribe.client_new
# def assign_app_group(client):
#     d = {}
#     #####################################################################################
#     ### Use xprop fo find  the value of WM_CLASS(STRING) -> First field is sufficient ###
#     #####################################################################################
#     d[group_names[0]] = ["Navigator", "Firefox", "Vivaldi-stable", "Vivaldi-snapshot", "Chromium", "Google-chrome", "Brave", "Brave-browser",
#               "navigator", "firefox", "vivaldi-stable", "vivaldi-snapshot", "chromium", "google-chrome", "brave", "brave-browser", ]
#     d[group_names[1]] = [ "Atom", "Subl", "Geany", "Brackets", "Code-oss", "Code", "TelegramDesktop", "Discord",
#                "atom", "subl", "geany", "brackets", "code-oss", "code", "telegramDesktop", "discord", ]
#     d[group_names[2]] = ["Inkscape", "Nomacs", "Ristretto", "Nitrogen", "Feh",
#               "inkscape", "nomacs", "ristretto", "nitrogen", "feh", ]
#     d[group_names[3]] = ["Gimp", "gimp" ]
#     d[group_names[4]] = ["Meld", "meld", "org.gnome.meld" "org.gnome.Meld" ]
#     d[group_names[5]] = ["Vlc","vlc", "Mpv", "mpv" ]
#     d[group_names[6]] = ["VirtualBox Manager", "VirtualBox Machine", "Vmplayer",
#               "virtualbox manager", "virtualbox machine", "vmplayer", ]
#     d[group_names[7]] = ["Thunar", "Nemo", "Caja", "Nautilus", "org.gnome.Nautilus", "Pcmanfm", "Pcmanfm-qt",
#               "thunar", "nemo", "caja", "nautilus", "org.gnome.nautilus", "pcmanfm", "pcmanfm-qt", ]
#     d[group_names[8]] = ["Evolution", "Geary", "Mail", "Thunderbird",
#               "evolution", "geary", "mail", "thunderbird" ]
#     d[group_names[9]] = ["Spotify", "Pragha", "Clementine", "Deadbeef", "Audacious",
#               "spotify", "pragha", "clementine", "deadbeef", "audacious" ]
#     ######################################################################################
#
# wm_class = client.window.get_wm_class()[0]
#
#     for i in range(len(d)):
#         if wm_class in list(d.values())[i]:
#             group = list(d.keys())[i]
#             client.toscreen(group)
#             client.group.cmd_toscreen(toggle=False)

# END
# ASSIGN APPLICATIONS TO A SPECIFIC GROUPNAME

main = None

# hides the top bar when the archlinux-logout widget is opened
@hook.subscribe.client_new
def new_client(window):
    if window.name == "ArchLinux Logout":
        qtile.hide_show_bar()

# shows the top bar when the archlinux-logout widget is closed
@hook.subscribe.client_killed
def logout_killed(window):
    if window.name == "ArchLinux Logout":
        qtile.hide_show_bar()

@hook.subscribe.startup_once
def start_once():
    home = os.path.expanduser('~')
    subprocess.call([home + '/.config/qtile/scripts/autostart.sh'])

@hook.subscribe.startup
def start_always():
    # Set the cursor to something sane in X
    subprocess.Popen(['xsetroot', '-cursor_name', 'left_ptr'])

@hook.subscribe.client_new
def set_floating(window):
    if (window.window.get_wm_transient_for()
            or window.window.get_wm_type() in floating_types):
        window.floating = True

floating_types = ["notification", "toolbar", "splash", "dialog"]


follow_mouse_focus = False
#bring_front_click = False
#cursor_warp = False
floating_layout = layout.Floating(float_rules=[
    # Run the utility of `xprop` to see the wm class and name of an X client.
    *layout.Floating.default_float_rules,
    Match(wm_class='confirmreset'),  # gitk
    Match(wm_class='makebranch'),  # gitk
    Match(wm_class='maketag'),  # gitk
    Match(wm_class='ssh-askpass'),  # ssh-askpass
    Match(title='branchdialog'),  # gitk
    Match(title='pinentry'),  # GPG key password entry
    Match(wm_class='Arcolinux-welcome-app.py'),
    Match(wm_class='Arcolinux-calamares-tool.py'),
    Match(wm_class='confirm'),
    Match(wm_class='dialog'),
    Match(wm_class='download'),
    Match(wm_class='error'),
    Match(wm_class='file_progress'),
    Match(wm_class='notification'),
    Match(wm_class='splash'),
    Match(wm_class='toolbar'),
    Match(wm_class='Arandr'),
    Match(wm_class='feh'),
    Match(wm_class='Galculator'),
    Match(wm_class='archlinux-logout'),
    Match(wm_class='xfce4-terminal'),

],  fullscreen_border_width = 0, border_width = 0)
#auto_fullscreen = True

#focus_on_window_activation = "smart" 

#wmname = "LG3D"

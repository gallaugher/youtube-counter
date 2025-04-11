# code.py for MatrixPortal S3 with Multi-Channel YouTube Stats
# This code will not work with a MatrixPortal M4 (not enough memory)
# Use the file format for settings.toml you'll find in multi-channel-settings.toml in the github repo, just be sure to rename it settings.toml on your CIRCUITPY board.

import board, time, terminalio, displayio, os
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# === CONFIG ===
DEFAULT_SUBS = 300
DEFAULT_VIEWS = 1000
SCROLL_SPEED = 0.05
SCROLL_RESET_PAUSE = 0.5
CHANNEL_SWITCH_SCROLLS = 3

FALLBACK_COLOR = 0x55FF55
ERROR_COLOR = 0xFFFF55
NORMAL_COLOR = 0xFFFFFF

WIFI_RETRY_INTERVAL = 10
ERROR_RETRY_INTERVAL = 30
NORMAL_REFRESH_INTERVAL = 5 * 60
CHAR_SPACING = 1
FADE_STEPS = 10
FADE_DELAY = 0.03

# === Load multiple channels ===
channels = []
index = 1
while True:
    suffix = f"{index}" if index > 1 else ""
    api_key = os.getenv(f"YOUTUBE_API_KEY{suffix}")
    channel_id = os.getenv(f"CHANNEL_ID{suffix}")
    channel_name = os.getenv(f"CHANNEL_NAME{suffix}")
    sub_adjust = int(os.getenv(f"SUB_ADJUST{suffix}") or "0")
    view_adjust = int(os.getenv(f"VIEW_ADJUST{suffix}") or "0")
    if not api_key or not channel_id or not channel_name:
        break
    channels.append({
        "api_key": api_key,
        "channel_id": channel_id,
        "channel_name": channel_name,
        "sub_adjust": sub_adjust,
        "view_adjust": view_adjust
    })
    index += 1
if not channels:
    raise ValueError("No YouTube channels found in settings.toml")

# === MatrixPortal Setup ===
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, bit_depth=6, debug=True)
display_width = matrixportal.graphics.display.width
visible_x_start = 15
visible_x_end = display_width
main_group = displayio.Group()
matrixportal.graphics.display.root_group = main_group

# === YouTube Logo ===
youtube_red = 0xFC0D1B
logo_bitmap = displayio.Bitmap(13, 9, 2)
logo_palette = displayio.Palette(2)
logo_palette[0] = 0x000000
logo_palette[1] = youtube_red
for x in range(13):
    for y in range(9):
        if ((x == 0 and y == 0) or (x == 0 and y == 8) or (x == 12 and y == 0) or (x == 12 and y == 8)):
            logo_bitmap[x, y] = 0
        else:
            logo_bitmap[x, y] = 1
play_bitmap = displayio.Bitmap(5, 5, 2)
play_palette = displayio.Palette(2)
play_palette[0] = youtube_red
play_palette[1] = 0xFFFFFF
for x, y in [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (3, 2)]:
    play_bitmap[x, y] = 1
main_group.append(displayio.TileGrid(logo_bitmap, pixel_shader=logo_palette, x=1, y=1))
main_group.append(displayio.TileGrid(play_bitmap, pixel_shader=play_palette, x=5, y=3))

# === Fonts ===
try:
    channel_font = bitmap_font.load_font("/fonts/Rockbox-Propfont.bdf")
    y_position = 4
except:
    channel_font = terminalio.FONT
    y_position = 6
try:
    subs_value_font = bitmap_font.load_font("/fonts/helvB08.bdf")
except:
    subs_value_font = terminalio.FONT
try:
    views_value_font = bitmap_font.load_font("/fonts/helvB08.bdf")
except:
    views_value_font = terminalio.FONT
try:
    label_font = bitmap_font.load_font("/fonts/Rockbox-Propfont.bdf")
except:
    label_font = terminalio.FONT

# === Labels ===
sub_label = Label(label_font, text="sub", color=NORMAL_COLOR, x=2, y=14)
sub_value = Label(subs_value_font, text="", color=NORMAL_COLOR, anchored_position=(64, 16), anchor_point=(1.0, 0.5))
views_label = Label(label_font, text="view", color=NORMAL_COLOR, x=2, y=25)
views_value = Label(views_value_font, text="", color=NORMAL_COLOR, anchored_position=(64, 27), anchor_point=(1.0, 0.5))
main_group.append(sub_label)
main_group.append(sub_value)
main_group.append(views_label)
main_group.append(views_value)
scrolling_chars_group = displayio.Group()
main_group.append(scrolling_chars_group)

# === Functions ===
def format_stat(value):
    if value >= 100_000_000:
        return f"{value // 1_000_000}m"
    elif value >= 10_000_000:
        return f"{value / 1_000_000:.1f}m"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f} mil"
    else:
        return f"{value:,}"

def show_stats(subs, views, color):
    sub_label.color = sub_value.color = views_label.color = views_value.color = color
    sub_value.text = format_stat(subs)
    views_value.text = format_stat(views)

def scroll_label_setup(name):
    char_labels.clear()
    while scrolling_chars_group:
        scrolling_chars_group.pop()
    x_offset = 0
    for c in name:
        label = Label(channel_font, text=c, color=NORMAL_COLOR)
        label.y = y_position
        width = label.bounding_box[2]
        char_labels.append((label, x_offset))
        x_offset += width + CHAR_SPACING
    return x_offset

def fetch_stats_for(channel):
    api_url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel['channel_id']}&key={channel['api_key']}"
    try:
        print("Fetching stats for:", channel['channel_name'])
        response = matrixportal.network.fetch(api_url)
        data = response.json() if hasattr(response, 'json') else response
        stats = data['items'][0]['statistics']
        subs = int(stats.get("subscriberCount", "0")) + channel.get("sub_adjust", 0)
        views = int(stats.get("viewCount", "0")) + channel.get("view_adjust", 0)
        show_stats(subs, views, NORMAL_COLOR)
        return True
    except Exception as e:
        print("API error:", e)
        show_stats(DEFAULT_SUBS, DEFAULT_VIEWS, ERROR_COLOR)
        return False

def fade_out():
    for i in range(FADE_STEPS, -1, -1):
        brightness = int((i / FADE_STEPS) * 255)
        color = (brightness, brightness, brightness)
        sub_value.color = views_value.color = sub_label.color = views_label.color = color
        time.sleep(FADE_DELAY)

def fade_in():
    for i in range(0, FADE_STEPS + 1):
        brightness = int((i / FADE_STEPS) * 255)
        color = (brightness, brightness, brightness)
        sub_value.color = views_value.color = sub_label.color = views_label.color = color
        time.sleep(FADE_DELAY)

char_labels = []
current_channel = 0
scroll_x = visible_x_end
pause_at_end = False
pause_start_time = 0
last_scroll_time = 0
scroll_cycles = 0
last_api_refresh = 0
interval = NORMAL_REFRESH_INTERVAL
last_wifi_attempt = 0

channel = channels[current_channel]
text_pixel_width = scroll_label_setup(channel['channel_name'])

# === Network Info ===
def print_network_info():
    try:
        if matrixportal.network.is_connected:
            print("IP:", matrixportal.network.ip_address)
    except:
        print("IP unavailable")

try:
    matrixportal.network.connect()
    print("Connected to Wi-Fi")
    print_network_info()
except Exception as e:
    print("Wi-Fi error:", e)

# Initial fetch
fetch_stats_for(channel)
last_api_refresh = time.monotonic()

# === Main Loop ===
while True:
    now = time.monotonic()

    # === Scroll Text ===
    if not pause_at_end and now - last_scroll_time >= SCROLL_SPEED:
        scroll_x -= 1
        while scrolling_chars_group:
            scrolling_chars_group.pop()
        for label, char_x in char_labels:
            screen_x = char_x + scroll_x
            if visible_x_start <= screen_x < visible_x_end:
                label.x = screen_x
                scrolling_chars_group.append(label)
        if scroll_x <= -text_pixel_width:
            pause_at_end = True
            pause_start_time = now
            scroll_cycles += 1
        last_scroll_time = now
    elif pause_at_end and now - pause_start_time >= SCROLL_RESET_PAUSE:
        scroll_x = visible_x_end
        pause_at_end = False
        last_scroll_time = now

    # === Switch Channel ===
    if scroll_cycles >= CHANNEL_SWITCH_SCROLLS:
        fade_out()
        current_channel = (current_channel + 1) % len(channels)
        channel = channels[current_channel]
        text_pixel_width = scroll_label_setup(channel['channel_name'])
        scroll_cycles = 0
        print(f"Switching to: {channel['channel_name']}")
        fetch_stats_for(channel)
        fade_in()
        last_api_refresh = now

    # === Periodic API Refresh ===
    if now - last_api_refresh >= interval:
        fetch_stats_for(channel)
        last_api_refresh = now

    time.sleep(0.01)

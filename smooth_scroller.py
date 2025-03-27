import board
import time
import terminalio
import displayio
import os
import json
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# ==== USER-CONFIGURABLE CONSTANTS ====
DEFAULT_SUBS = 300
DEFAULT_VIEWS = 1000

SUB_ADJUST = 0
VIEW_ADJUST = 251495  # as of March 27, 2025

FALLBACK_COLOR = 0x55FF55  # subtle green
ERROR_COLOR = 0xFFFF55  # subtle yellow
NORMAL_COLOR = 0xFFFFFF  # white

ERROR_RETRY_INTERVAL = 30  # in seconds
NORMAL_REFRESH_INTERVAL = 5 * 60  # 5 minutes

# ==== MatrixPortal setup ====
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
    bit_depth=6,
)

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

YOUTUBE_API_URL = (
    "https://www.googleapis.com/youtube/v3/channels"
    f"?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
)

main_group = displayio.Group()

# ==== YouTube logo ====
youtube_red = 0xFC0D1B

logo_bitmap = displayio.Bitmap(13, 9, 2)
logo_palette = displayio.Palette(2)
logo_palette[0] = 0x000000
logo_palette[1] = youtube_red

for x in range(13):
    for y in range(9):
        if ((x == 0 and y == 0) or (x == 0 and y == 8) or
                (x == 12 and y == 0) or (x == 12 and y == 8)):
            logo_bitmap[x, y] = 0
        else:
            logo_bitmap[x, y] = 1

play_bitmap = displayio.Bitmap(5, 5, 2)
play_palette = displayio.Palette(2)
play_palette[0] = youtube_red
play_palette[1] = 0xFFFFFF

play_bitmap[1, 0] = 1
play_bitmap[1, 1] = 1
play_bitmap[1, 2] = 1
play_bitmap[1, 3] = 1
play_bitmap[1, 4] = 1
play_bitmap[2, 1] = 1
play_bitmap[2, 2] = 1
play_bitmap[2, 3] = 1
play_bitmap[3, 2] = 1

main_group.append(displayio.TileGrid(logo_bitmap, pixel_shader=logo_palette, x=1, y=1))
main_group.append(displayio.TileGrid(play_bitmap, pixel_shader=play_palette, x=5, y=3))

# ==== Fonts ====
channel_name = "YouTube.com/profgallaugher"
channel_font_name = "profont10_clean.bdf"
subs_value_font_name = "helvB08.bdf"
views_value_font_name = "helvB08.bdf"
label_font_name = "profont10_clean.bdf"

try:
    channel_font = bitmap_font.load_font(f"/fonts/{channel_font_name}")
    y_position = 4
except:
    channel_font = terminalio.FONT
    y_position = 6

try:
    subs_value_font = bitmap_font.load_font(f"/fonts/{subs_value_font_name}")
except:
    subs_value_font = terminalio.FONT

try:
    views_value_font = bitmap_font.load_font(f"/fonts/{views_value_font_name}")
except:
    views_value_font = terminalio.FONT

try:
    label_font = bitmap_font.load_font(f"/fonts/{label_font_name}")
except:
    label_font = terminalio.FONT

# ==== Labels ====
sub_label = Label(label_font, text="sub", color=NORMAL_COLOR, x=2, y=14)
sub_value = Label(subs_value_font, text="Loading...", color=NORMAL_COLOR,
                  anchored_position=(64, 16), anchor_point=(1.0, 0.5))
views_label = Label(label_font, text="view", color=NORMAL_COLOR, x=2, y=25)
views_value = Label(views_value_font, text="Loading...", color=NORMAL_COLOR,
                    anchored_position=(64, 27), anchor_point=(1.0, 0.5))

main_group.append(sub_label)
main_group.append(sub_value)
main_group.append(views_label)
main_group.append(views_value)

# ==== Scrolling Setup ====
display_width = matrixportal.graphics.display.width
visible_x_start = 15
visible_x_end = display_width
char_width = 4
text_pixel_width = len(channel_name) * char_width

char_labels = []
for i, c in enumerate(channel_name):
    label = Label(channel_font, text=c, color=NORMAL_COLOR)
    label.y = y_position
    char_labels.append((label, i * char_width))

scrolling_chars_group = displayio.Group()
main_group.append(scrolling_chars_group)

matrixportal.graphics.display.root_group = main_group


def format_stat(value):
    if value >= 100_000_000:
        return f"{value // 1_000_000}m"
    elif value >= 10_000_000:
        return f"{value / 1_000_000:.1f}m"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f} mil"
    else:
        return f"{value:,}"


def fetch_youtube_stats():
    try:
        response = matrixportal.network.fetch(YOUTUBE_API_URL)
        data = response.json()
        stats = data["items"][0]["statistics"]

        raw_subs = int(stats.get("subscriberCount", "0"))
        raw_views = int(stats.get("viewCount", "0"))

        subscribers = raw_subs + SUB_ADJUST
        views = raw_views + VIEW_ADJUST

        print("YouTube API stats fetched:")
        print(f"  Raw subs: {raw_subs:,}")
        print(f"  Raw views: {raw_views:,}")
        print(f"  Adjusted subs: {subscribers:,} → {format_stat(subscribers)}")
        print(f"  Adjusted views: {views:,} → {format_stat(views)}\n")

        return subscribers, views, NORMAL_COLOR, NORMAL_REFRESH_INTERVAL
    except Exception as e:
        print(f"API error: {e}")
        return None, None, ERROR_COLOR, ERROR_RETRY_INTERVAL


def show_stats(subs, views, color):
    sub_value.color = views_value.color = sub_label.color = views_label.color = color
    sub_value.text = format_stat(subs)
    views_value.text = format_stat(views)


# ==== Init Stats ====
subs, views, color, interval = fetch_youtube_stats()
if subs and views:
    show_stats(subs, views, color)
else:
    show_stats(DEFAULT_SUBS, DEFAULT_VIEWS, FALLBACK_COLOR)
    interval = ERROR_RETRY_INTERVAL

# ==== Scrolling state ====
SCROLL_SPEED = 0.05
SCROLL_RESET_PAUSE = 0.5
scroll_x = visible_x_end
pause_at_end = False
pause_start_time = 0
last_scroll_time = time.monotonic()
last_api_refresh = time.monotonic()

# ==== Main loop ====
while True:
    now = time.monotonic()

    # API refresh
    if now - last_api_refresh >= interval:
        subs, views, color, interval = fetch_youtube_stats()
        if subs and views:
            show_stats(subs, views, color)
        else:
            show_stats(DEFAULT_SUBS, DEFAULT_VIEWS, FALLBACK_COLOR)
        last_api_refresh = now

    # Scrolling logic
    if not pause_at_end:
        if now - last_scroll_time >= SCROLL_SPEED:
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
            last_scroll_time = now
    else:
        if now - pause_start_time >= SCROLL_RESET_PAUSE:
            scroll_x = visible_x_end
            pause_at_end = False
            last_scroll_time = now

    time.sleep(0.01)

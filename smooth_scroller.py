# This version scrolls the channel name one pixel at a time and avoids extreme flashing. It also has the YouTube logo in red with no black spots around the triangle
import board
import time
import terminalio
import displayio
import os
import json
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# ---- MatrixPortal setup ----
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

# ---- YouTube logo setup ----
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
# play_palette[0] = 0x000000
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

logo_grid = displayio.TileGrid(logo_bitmap, pixel_shader=logo_palette, x=1, y=1)
play_grid = displayio.TileGrid(play_bitmap, pixel_shader=play_palette, x=5, y=3)

main_group.append(logo_grid)
main_group.append(play_grid)

# ---- Fonts ----
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

# ---- Stats labels ----
sub_label = Label(label_font, text="sub", color=0xFFFFFF, x=2, y=14)
sub_value = Label(subs_value_font, text="Loading...", color=0xFFFFFF,
                  anchored_position=(64, 16), anchor_point=(1.0, 0.5))
views_label = Label(label_font, text="view", color=0xFFFFFF, x=2, y=25)
views_value = Label(views_value_font, text="Loading...", color=0xFFFFFF,
                    anchored_position=(64, 27), anchor_point=(1.0, 0.5))

main_group.append(sub_label)
main_group.append(sub_value)
main_group.append(views_label)
main_group.append(views_value)

# ---- Scrolling Setup ----
display_width = matrixportal.graphics.display.width
visible_x_start = 15  # Do not draw anything left of this!
visible_x_end = display_width

char_width = 4  # For profont10_clean.bdf
text_pixel_width = len(channel_name) * char_width

# Pre-create Labels for each character
char_labels = []
for i, c in enumerate(channel_name):
    label = Label(channel_font, text=c, color=0xFFFFFF)
    label.y = y_position
    char_labels.append((label, i * char_width))

# Add labels to main group only if visible
scrolling_chars_group = displayio.Group()
main_group.append(scrolling_chars_group)

# ---- Set display root group ----
matrixportal.graphics.display.root_group = main_group

# ---- API fetch function ----
def fetch_youtube_stats():
    try:
        response = matrixportal.network.fetch(YOUTUBE_API_URL)
        data = response.json()
        stats = data["items"][0]["statistics"]
        subscribers = int(stats.get("subscriberCount", "0"))
        views = int(stats.get("viewCount", "0"))
        return f"{subscribers:,}", f"{views:,}"
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return None, None

# ---- Scrolling state ----
SCROLL_SPEED = 0.05
SCROLL_RESET_PAUSE = 0.5
scroll_x = visible_x_end  # Start just offscreen to the right
pause_at_end = False
pause_start_time = 0
last_scroll_time = time.monotonic()

# ---- API refresh ----
API_REFRESH_INTERVAL = 5 * 60
last_api_refresh = time.monotonic()

# ---- Initial stats ----
subs, views = fetch_youtube_stats()
if subs and views:
    sub_value.text = subs
    views_value.text = views
else:
    sub_value.text = "8,920"
    views_value.text = "757,696"

# ---- Main loop ----
while True:
    now = time.monotonic()

    # Refresh API
    if now - last_api_refresh >= API_REFRESH_INTERVAL:
        subs, views = fetch_youtube_stats()
        if subs and views:
            sub_value.text = subs
            views_value.text = views
        last_api_refresh = now

    # Scrolling logic
    if not pause_at_end:
        if now - last_scroll_time >= SCROLL_SPEED:
            scroll_x -= 1
            while len(scrolling_chars_group):
                scrolling_chars_group.pop()

            # Add only visible characters
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

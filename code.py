# Code by Prof. John Gallaugher. Updated for robust Wi-Fi/API error handling.
# YouTube: https://YouTube.com/@BuildWithProfG
# SwiftUI: https://YouTube.com/profgallaugher

import board
import time
import terminalio
import displayio
import os
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# ==== USER-CONFIGURABLE CONSTANTS ====
DEFAULT_SUBS = 300
DEFAULT_VIEWS = 1000
SUB_ADJUST = 0
VIEW_ADJUST = 0 # NOTE: Stats from yt app are higher, API ignores  views from retired videos no longer public.

FALLBACK_COLOR = 0x55FF55  # Green
ERROR_COLOR = 0xFFFF55  # Gold
NORMAL_COLOR = 0xFFFFFF  # White

WIFI_RETRY_INTERVAL = 10
ERROR_RETRY_INTERVAL = 30
NORMAL_REFRESH_INTERVAL = 5 * 60

CHAR_SPACING = 1

# ==== Load from settings.toml ====
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
channel_name = os.getenv("CHANNEL_NAME")

# Print configuration
print(f"YouTube API Key: {API_KEY}")
print(f"Channel ID: {CHANNEL_ID}")
print(f"Channel Name: {channel_name}")

# ==== MatrixPortal setup ====
print("Setting up MatrixPortal...")
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, bit_depth=6, debug=True)

# Get MAC address in proper order
try:
    # Access the ESP object from the existing MatrixPortal instance
    esp = matrixportal.network._wifi.esp
    if esp:
        mac_bytes = esp.MAC_address
        # Display MAC address in correct order (reversed)
        mac = ":".join(["{:02X}".format(b) for b in reversed(mac_bytes)])
        print(f"MAC Address: {mac}")
except Exception as e:
    print(f"Error getting MAC address: {e}")

YOUTUBE_API_URL = (
    "https://www.googleapis.com/youtube/v3/channels"
    f"?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
)
print(f"API URL: {YOUTUBE_API_URL}")

main_group = displayio.Group()

# ==== YouTube Logo ====
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

for x, y in [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3), (3, 2)]:
    play_bitmap[x, y] = 1

main_group.append(displayio.TileGrid(logo_bitmap, pixel_shader=logo_palette, x=1, y=1))
main_group.append(displayio.TileGrid(play_bitmap, pixel_shader=play_palette, x=5, y=3))

# ==== Fonts ====
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

# ==== Labels ====
sub_label = Label(label_font, text="sub", color=NORMAL_COLOR, x=2, y=14)
sub_value = Label(subs_value_font, text="Loading", color=NORMAL_COLOR, anchored_position=(64, 16),
                  anchor_point=(1.0, 0.5))
views_label = Label(label_font, text="view", color=NORMAL_COLOR, x=2, y=25)
views_value = Label(views_value_font, text="Loading", color=NORMAL_COLOR, anchored_position=(64, 27),
                    anchor_point=(1.0, 0.5))

main_group.append(sub_label)
main_group.append(sub_value)
main_group.append(views_label)
main_group.append(views_value)

# ==== Scrolling Setup ====
display_width = matrixportal.graphics.display.width
visible_x_start = 15
visible_x_end = display_width
char_labels = []
x_offset = 0
text_pixel_width = 0
for c in channel_name:
    label = Label(channel_font, text=c, color=NORMAL_COLOR)
    label.y = y_position
    width = label.bounding_box[2]
    char_labels.append((label, x_offset))
    x_offset += width + CHAR_SPACING
    text_pixel_width += width + CHAR_SPACING

scrolling_chars_group = displayio.Group()
main_group.append(scrolling_chars_group)

matrixportal.graphics.display.root_group = main_group


# ==== Functions ====
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


def print_network_info():
    """Print the network connection details including IP address"""
    if not matrixportal.network.is_connected:
        print("Not connected to WiFi")
        return

    try:
        ip_address = matrixportal.network.ip_address
        print(f"Connected to WiFi with IP address: {ip_address}")

        # Additional network info if available
        try:
            netmask = matrixportal.network._wifi.netmask
            gateway = matrixportal.network._wifi.gateway
            print(f"Netmask: {netmask}")
            print(f"Gateway: {gateway}")
        except:
            # Don't break if these attributes aren't available
            pass
    except Exception as e:
        print(f"Error getting network info: {e}")


# Initiate WiFi connection at startup
print("Initial WiFi connection attempt...")
try:
    matrixportal.network.connect()
    print("Successfully connected to WiFi")
    # Print IP address after successful connection
    print_network_info()
except Exception as e:
    print(f"Initial WiFi connection issue: {e}")

# ==== State ====
last_subs = DEFAULT_SUBS
last_views = DEFAULT_VIEWS
last_color = NORMAL_COLOR
last_api_refresh = 0
last_wifi_attempt = 0
interval = NORMAL_REFRESH_INTERVAL

# ==== Main loop ====
SCROLL_SPEED = 0.05
SCROLL_RESET_PAUSE = 0.5
scroll_x = visible_x_end
pause_at_end = False
pause_start_time = 0
last_scroll_time = time.monotonic()

while True:
    now = time.monotonic()

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

    # Connectivity and API handling
    if now - last_api_refresh >= interval:
        try:
            # Modified WiFi checking - don't raise an error immediately
            if now - last_wifi_attempt >= WIFI_RETRY_INTERVAL:
                try:
                    # Check connection status - but don't immediately fail
                    # if matrixportal.network._wifi.is_connected returns False
                    print("Checking WiFi connection...")
                    if not matrixportal.network.is_connected:
                        print("Attempting to reconnect WiFi...")
                        matrixportal.network.connect()
                        # Print IP address after reconnection
                        print_network_info()
                    else:
                        print("WiFi already connected")
                        # Print current IP address when checking connection
                        print_network_info()
                    last_wifi_attempt = now
                except Exception as e:
                    print(f"WiFi connection issue: {e}")

            print("Fetching YouTube stats...")
            response = matrixportal.network.fetch(YOUTUBE_API_URL)
            print(f"Response type: {type(response)}")

            # Handle different response types
            if hasattr(response, 'json'):
                print("Got Response object, parsing JSON...")
                data = response.json()
            elif isinstance(response, dict):
                print("Got dictionary response...")
                data = response
            else:
                print(f"Raw response: {response}")
                raise ValueError(f"Unexpected response type: {type(response)}")

            stats = data["items"][0]["statistics"]

            # Print detailed statistics
            print("YouTube Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            raw_subs = int(stats.get("subscriberCount", "0"))
            raw_views = int(stats.get("viewCount", "0"))

            last_subs = raw_subs + SUB_ADJUST
            last_views = raw_views + VIEW_ADJUST
            last_color = NORMAL_COLOR
            interval = NORMAL_REFRESH_INTERVAL
            print(f"Fetched stats successfully: {last_subs} subscribers, {last_views} views")

        except Exception as e:
            print(f"Error: {e}")
            # Don't immediately assume WiFi issue, check connection state
            wifi_status = "unknown"
            try:
                wifi_status = "connected" if matrixportal.network.is_connected else "disconnected"
            except:
                pass

            print(f"WiFi status check: {wifi_status}")

            if wifi_status == "disconnected":
                last_color = FALLBACK_COLOR
                last_subs = DEFAULT_SUBS
                last_views = DEFAULT_VIEWS
                interval = WIFI_RETRY_INTERVAL
            else:
                last_color = ERROR_COLOR
                interval = ERROR_RETRY_INTERVAL

        show_stats(last_subs, last_views, last_color)
        last_api_refresh = now

    time.sleep(0.01)

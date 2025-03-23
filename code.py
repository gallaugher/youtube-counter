import board
import time
import terminalio
import displayio
import os
import json
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# Initialize the Matrix Portal with network capability
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
    bit_depth=6,
)

# Grab API credentials from settings.toml
API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# YouTube Data API URL to get subscriber and view counts
YOUTUBE_API_URL = (
    "https://www.googleapis.com/youtube/v3/channels"
    f"?part=statistics&id={CHANNEL_ID}&key={API_KEY}"
)

# Create a display group for our screen objects
main_group = displayio.Group()

# YouTube logo colors
youtube_red = 0xFC0D1B  # YouTube red color

# Create a bitmap for the logo (13x9 pixels) - adjusted for symmetry
logo_bitmap = displayio.Bitmap(13, 9, 2)
logo_palette = displayio.Palette(2)
logo_palette[0] = 0x000000  # Black background/transparent
logo_palette[1] = youtube_red  # YouTube red

# Draw the YouTube rounded rectangle with rounded corners
for x in range(13):
    for y in range(9):
        # Fill rectangle with red but make corners rounded
        if ((x == 0 and y == 0) or  # Top-left corner
                (x == 0 and y == 8) or  # Bottom-left corner
                (x == 12 and y == 0) or  # Top-right corner
                (x == 12 and y == 8)):  # Bottom-right corner
            logo_bitmap[x, y] = 0  # Make corners transparent/black
        else:
            logo_bitmap[x, y] = 1  # Fill the rest with red

# Draw the white play triangle
# Create a bitmap for the play button with symmetric positioning
play_bitmap = displayio.Bitmap(5, 5, 2)
play_palette = displayio.Palette(2)
play_palette[0] = 0x000000  # Transparent/Black
play_palette[1] = 0xFFFFFF  # White

# Draw a simple triangle for the play button
play_bitmap[1, 0] = 1
play_bitmap[1, 1] = 1
play_bitmap[1, 2] = 1
play_bitmap[1, 3] = 1
play_bitmap[1, 4] = 1
play_bitmap[2, 1] = 1
play_bitmap[2, 2] = 1
play_bitmap[2, 3] = 1
play_bitmap[3, 2] = 1

# Create TileGrid objects for the logo and play button
logo_grid = displayio.TileGrid(logo_bitmap, pixel_shader=logo_palette, x=1, y=2)
play_grid = displayio.TileGrid(play_bitmap, pixel_shader=play_palette, x=5, y=4)

# Add the YouTube logo and play button to the main group
main_group.append(logo_grid)
main_group.append(play_grid)

# Channel name
channel_name = "YouTube.com/profgallaugher"

# Try to load the Tom Thumb font (smaller font)
small_font = None
try:
    print("Attempting to load Tom Thumb font...")
    # Try Tom Thumb Tall first, then regular
    try:
        small_font = bitmap_font.load_font("/fonts/tom-thumb-tall.bdf")
        print("Successfully loaded Tom Thumb Tall font")
    except Exception as e:
        print("Tom Thumb Tall failed, trying regular version")
        small_font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
        print("Successfully loaded regular Tom Thumb font")

    font_to_use = small_font
    y_position = 5

except Exception as e:
    print("Couldn't load either Tom Thumb font")
    print("Falling back to built-in font")
    font_to_use = terminalio.FONT
    y_position = 6

# Try to load font for the stats
stats_font = None
try:
    font_name = "helvR08.bdf"  # Use the font you specified
    stats_font = bitmap_font.load_font(f"/fonts/{font_name}")
    print(f"Successfully loaded {font_name} font for stats")
except Exception as e:
    print(f"Couldn't load {font_name}")
    stats_font = terminalio.FONT
    print("Using built-in font for stats")

# Create a label for subscriber label (left-aligned)
sub_label = Label(
    stats_font,
    text="sub:",
    color=0xFFFFFF,
    x=2,  # Left side of screen
    y=16  # Position in the middle, nudged up one pixel as requested
)

# Create a label for subscriber value (right-aligned)
sub_value = Label(
    stats_font,
    text="Loading...",
    color=0xFFFFFF,
    anchored_position=(64, 16),  # Right edge of screen, same y as sub_label
    anchor_point=(1.0, 0.5)  # Right-aligned, vertically centered
)

# Create a label for views label (left-aligned)
views_label = Label(
    stats_font,
    text="v:",
    color=0xFFFFFF,
    x=2,  # Left side of screen
    y=28  # Bottom area
)

# Create a label for views value (right-aligned)
views_value = Label(
    stats_font,
    text="Loading...",
    color=0xFFFFFF,
    anchored_position=(64, 28),  # Right edge, bottom area
    anchor_point=(1.0, 0.5)  # Right-aligned, vertically centered
)

# Add stats labels to the main group
main_group.append(sub_label)
main_group.append(sub_value)
main_group.append(views_label)
main_group.append(views_value)

# Create the channel label - initially empty
# It will always stay fixed at x=17
channel_label = Label(
    font_to_use,
    text="",  # Start empty, we'll update this
    color=0xFFFFFF,
    x=16,  # Position to the right of the logo (adjusted for new logo width)
    y=y_position
)
main_group.append(channel_label)

# Set the display's root group
matrixportal.graphics.display.root_group = main_group

print(f"Display dimensions: {matrixportal.graphics.display.width}x{matrixportal.graphics.display.height}")
print("Portal code running...")

# Calculate approximately how many characters fit in the display
# This is a rough estimate - may need adjustment based on font
char_width = 6  # Average width of a character in pixels for most fonts
if small_font is not None:  # If we know we have the small font
    char_width = 4  # Tom Thumb is about 4 pixels per character

# How many full characters can be shown at once
logo_width = 16  # The space taken by the YouTube logo (adjusted for new width)
display_width = matrixportal.graphics.display.width
max_visible_chars = (display_width - logo_width) // char_width
print(f"Max visible characters: ~{max_visible_chars}")


# Function to fetch YouTube statistics
def fetch_youtube_stats():
    try:
        print("Fetching YouTube stats...")
        response = matrixportal.network.fetch(YOUTUBE_API_URL)
        data = response.json()
        stats = data["items"][0]["statistics"]
        subscribers = int(stats.get("subscriberCount", "0"))
        views = int(stats.get("viewCount", "0"))

        # Format with commas
        subscribers_formatted = f"{subscribers:,}"
        views_formatted = f"{views:,}"

        print(f"Fetched stats: {subscribers_formatted} subscribers, {views_formatted} views")
        return subscribers_formatted, views_formatted
    except Exception as e:
        print(f"Error fetching YouTube stats: {e}")
        return None, None


# Variables for scrolling
SCROLL_STATIC_TIME = 1.0  # Seconds to show the non-scrolling name
SCROLL_PAUSE_TIME = 0.5  # Seconds to pause after scrolling
SCROLL_INTERVAL = 0.2  # Seconds between character scrolls

# Variables for API refresh
API_REFRESH_INTERVAL = 5 * 60  # Refresh stats every 5 minutes (300 seconds)
last_api_refresh = time.monotonic()

# State management
scroll_state = "static"  # Can be "static", "scrolling", or "pause"
state_start_time = time.monotonic()
last_scroll_time = time.monotonic()
scroll_position = 0

# Initial stats fetch
print("Fetching initial YouTube stats...")
subs, views = fetch_youtube_stats()
if subs and views:
    sub_value.text = subs
    views_value.text = views
    print(f"Updated display with: {subs} subscribers, {views} views")
else:
    print("Failed to get initial stats, using placeholder values")
    sub_value.text = "10,000"
    views_value.text = "1,000,000"

# Main loop
while True:
    now = time.monotonic()

    # Check if it's time to refresh YouTube stats
    if now - last_api_refresh >= API_REFRESH_INTERVAL:
        print("Time to refresh YouTube stats...")
        subs, views = fetch_youtube_stats()
        if subs and views:
            sub_value.text = subs
            views_value.text = views
            print(f"Updated display with: {subs} subscribers, {views} views")
        last_api_refresh = now

    # Handle text scrolling
    if scroll_state == "static":
        # Display the full text up to max visible characters
        visible_text = channel_name[:max_visible_chars]
        channel_label.text = visible_text

        # Wait for static display time to elapse
        if now - state_start_time >= SCROLL_STATIC_TIME:
            scroll_state = "scrolling"
            state_start_time = now
            scroll_position = 0
            print("Starting to scroll text")

    elif scroll_state == "scrolling":
        # Update scroll position at regular intervals
        if now - last_scroll_time >= SCROLL_INTERVAL:
            scroll_position += 1

            # If we've scrolled past all characters, pause
            if scroll_position >= len(channel_name):
                scroll_state = "pause"
                state_start_time = now
                # Display empty text
                channel_label.text = ""
                print("Text scrolled off, pausing")
            else:
                # Display the appropriate substring based on scroll position
                # This shows the text "sliding" to the left
                visible_text = channel_name[scroll_position:scroll_position + max_visible_chars]
                channel_label.text = visible_text

            last_scroll_time = now

    elif scroll_state == "pause":
        # Wait during pause state with no text showing
        if now - state_start_time >= SCROLL_PAUSE_TIME:
            scroll_state = "static"
            state_start_time = now
            print("Resetting to starting position")

    time.sleep(0.01)  # Small delay to prevent CPU hogging
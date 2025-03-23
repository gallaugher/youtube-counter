# This code can be used to quickly test fonts, replacing names for various fonts.
# I created this so I didn't have to wait for the networking before I saw fonts.
import board
import time
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

# Initialize the Matrix Portal without network capability
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
    bit_depth=6,
)

# Constants for subscriber and view counts
SUBSCRIBER_COUNT = "8,920"
VIEW_COUNT = "757,696"

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
# Logo moved up 1 pixel (from y=2 to y=1)
logo_grid = displayio.TileGrid(logo_bitmap, pixel_shader=logo_palette, x=1, y=1)
# Play button also moved up 1 pixel (from y=4 to y=3)
play_grid = displayio.TileGrid(play_bitmap, pixel_shader=play_palette, x=5, y=3)

# Add the YouTube logo and play button to the main group
main_group.append(logo_grid)
main_group.append(play_grid)

# Channel name
channel_name = "YouTube.com/profgallaugher"

# Define font file names
# channel_font_name = "helvR08.bdf"    # Too Big
# channel_font_name = "t0-11-uni.bdf"    # Not bad
# channel_font_name = "spleen-5x8.bdf"    # Not bad
# channel_font_name = "ib8x8u.bdf"    # Cool & bold but wide
# channel_font_name = "ic8x8u.bdf"    # Cool & bold but wide
# channel_font_name = "icl8x8u.bdf"     # single pixel, but wide
channel_font_name = "profont10_clean.bdf"    # Cool & bold but wide

subs_value_font_name = "helvB08.bdf"   # Font for subscriber count
# subs_value_font_name = "ic8x8u.bdf"   # Too thick
views_value_font_name = "helvB08.bdf"  # Font for view count
# label_font_name = "t0-11-uni.bdf"      # Too Wide
# label_font_name = "spleen-5x8.bdf"      # Raised up a bit.
# label_font_name = "helvR08.bdf"      # Font for "sub:" and "view:" labels
label_font_name = "profont10_clean.bdf"      # Font for "sub:" and "view:" labels


# Load channel font (for scrolling channel name)
channel_font = None
try:
    print(f"Attempting to load channel font: {channel_font_name}...")
    channel_font = bitmap_font.load_font(f"/fonts/{channel_font_name}")
    print(f"Successfully loaded {channel_font_name} font")
    y_position = 4
except Exception as e:
    print(f"Couldn't load channel font: {channel_font_name}, {e}")
    print("Falling back to built-in font for channel name")
    channel_font = terminalio.FONT
    y_position = 6

# Load font for subscriber value
subs_value_font = None
try:
    print(f"Loading subscriber value font: {subs_value_font_name}...")
    subs_value_font = bitmap_font.load_font(f"/fonts/{subs_value_font_name}")
    print(f"Successfully loaded {subs_value_font_name} font")
except Exception as e:
    print(f"Couldn't load subscriber value font: {e}")
    subs_value_font = terminalio.FONT
    print("Using built-in font for subscriber value")

# Load font for views value
views_value_font = None
try:
    print(f"Loading views value font: {views_value_font_name}...")
    views_value_font = bitmap_font.load_font(f"/fonts/{views_value_font_name}")
    print(f"Successfully loaded {views_value_font_name} font")
except Exception as e:
    print(f"Couldn't load views value font: {e}")
    views_value_font = terminalio.FONT
    print("Using built-in font for views value")

# Load font for labels ("sub:" and "view:")
label_font = None
try:
    print(f"Loading label font: {label_font_name}...")
    label_font = bitmap_font.load_font(f"/fonts/{label_font_name}")
    print(f"Successfully loaded {label_font_name} font")
except Exception as e:
    print(f"Couldn't load label font: {e}")
    label_font = terminalio.FONT
    print("Using built-in font for labels")

# Create a label for subscriber label (left-aligned)
# Moved up one more pixel (from y=15 to y=14)
sub_label = Label(
    label_font,  # Using the dedicated label font
    text="sub",
    color=0xFFFFFF,
    x=2,  # Left side of screen
    y=14  # Moved up one pixel for better alignment
)

# Create a label for subscriber value (right-aligned)
# Moved up one more pixel (from y=17 to y=16)
sub_value = Label(
    subs_value_font,  # Using dedicated subscriber value font
    text=SUBSCRIBER_COUNT,  # Using the constant
    color=0xFFFFFF,
    anchored_position=(64, 16),  # Right edge of screen, same y as sub_label
    anchor_point=(1.0, 0.5)  # Right-aligned, vertically centered
)

# Create a label for views label (left-aligned)
# Moved up one more pixel (from y=26 to y=25)
views_label = Label(
    label_font,  # Using the dedicated label font
    text="view",
    color=0xFFFFFF,
    x=2,  # Left side of screen
    y=25  # Moved up one pixel for better alignment
)

# Create a label for views value (right-aligned)
# Moved up one more pixel (from y=28 to y=27)
views_value = Label(
    views_value_font,  # Using dedicated views value font
    text=VIEW_COUNT,  # Using the constant
    color=0xFFFFFF,
    anchored_position=(64, 27),  # Right edge, bottom area
    anchor_point=(1.0, 0.5)  # Right-aligned, vertically centered
)

# Add stats labels to the main group
main_group.append(sub_label)
main_group.append(sub_value)
main_group.append(views_label)
main_group.append(views_value)

# Create the channel label - initially empty
# It will always stay fixed at x=16
channel_label = Label(
    channel_font,  # Using the dedicated channel font
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
if channel_font != terminalio.FONT:  # If we're using a custom channel font
    char_width = 4  # Estimate for smaller fonts

# How many full characters can be shown at once
logo_width = 16  # The space taken by the YouTube logo (adjusted for new width)
display_width = matrixportal.graphics.display.width
max_visible_chars = (display_width - logo_width) // char_width
print(f"Max visible characters: ~{max_visible_chars}")

# Variables for scrolling
SCROLL_STATIC_TIME = 1.0  # Seconds to show the non-scrolling name
SCROLL_PAUSE_TIME = 0.5  # Seconds to pause after scrolling
SCROLL_INTERVAL = 0.2  # Seconds between character scrolls

# State management
scroll_state = "static"  # Can be "static", "scrolling", or "pause"
state_start_time = time.monotonic()
last_scroll_time = time.monotonic()
scroll_position = 0

# Main loop
while True:
    now = time.monotonic()

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


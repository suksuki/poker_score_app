
import sys
import os

# Set headless for Kivy
os.environ['KIVY_NO_WINDOW'] = '1'
os.environ['KIVY_NO_ARGS'] = '1'

try:
    print("Importing main...")
    import main
    print("Importing theme...")
    import theme
    print("Importing widgets...")
    import widgets
    print("Importing screens...")
    import setup_screen
    import input_screen
    import score_screen
    
    print("Checking ThemeManager...")
    from theme import theme_manager
    print(f"Current theme: {theme_manager.current_theme}")
    theme_manager.switch_theme('dark')
    print(f"Switched theme: {theme_manager.current_theme}")
    
    print("SUCCESS: usage verification passed.")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

from PIL import Image, ImageDraw, ImageFont
import os

def create_banner():
    # Create banner.bmp (493x58)
    banner = Image.new('RGB', (493, 58), '#0078D7')
    draw = ImageDraw.Draw(banner)
    
    # Add text
    font = ImageFont.truetype('arial.ttf', 24)
    draw.text((10, 10), "Logbook Installer", fill='white', font=font)
    
    banner.save('icons/banner.bmp')

def create_dialog():
    # Create dialog.bmp (493x312)
    dialog = Image.new('RGB', (493, 312), '#F0F0F0')
    draw = ImageDraw.Draw(dialog)
    
    # Add background gradient
    for y in range(312):
        color = (240 - (y // 3), 240 - (y // 3), 240 - (y // 3))
        draw.line([(0, y), (493, y)], fill=color)
    
    dialog.save('icons/dialog.bmp')

def create_icon():
    # Create Logbook.ico
    icon = Image.new('RGBA', (256, 256), (255, 255, 255, 0))
    draw = ImageDraw.Draw(icon)
    
    # Draw a simple logo
    draw.rectangle([50, 50, 206, 206], outline='#0078D7', width=10)
    draw.text((70, 80), "L", fill='#0078D7', font=ImageFont.truetype('arial.ttf', 120))
    
    # Save in different sizes
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon.save('icons/Logbook.ico', sizes=sizes)

def main():
    os.makedirs('icons', exist_ok=True)
    create_banner()
    create_dialog()
    create_icon()
    print("Icons and images generated successfully!")

if __name__ == '__main__':
    main()

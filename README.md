# 📱 QRConnect

QRConnect is a lightweight, efficient QR code generator tool built in Python. This utility allows you to quickly create high-quality QR codes from custom data such as URLs, text, or contact information, and save them as image files for easy sharing and scanning.

## ✨ Features

- **Simple QR Generation**: Creates high-quality QR codes from any user-inputted data
- **Custom File Output**: Saves QR codes as PNG images with optimal 300x300 pixel resolution
- **User-Friendly Interface**: Clean command-line prompts guide users through the generation process
- **Versatile Data Support**: Handles URLs, plain text, contact information, and more
- **Instant Results**: Generates QR codes in seconds with minimal configuration

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Required Python packages:
  - [qrcode](https://pypi.org/project/qrcode/)
  - [Pillow](https://pypi.org/project/Pillow/)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/who0xac/qrconnect.git
   cd qrconnect
   ```

2. Install required packages
   ```
   pip install qrcode[pil]
   ```

## 📋 Usage

### Basic Usage

Run the script from the command line:
```
python qrconnect.py
```

Follow the prompts to:
1. Enter the data you want to encode in the QR code
2. Specify a filename for your QR code image
3. Retrieve your generated QR code from the output directory

### Example

```
$ python qrconnect.py
Enter data for QR code: https://example.com
Enter filename to save QR code (without extension): example_site
QR code successfully generated and saved as example_site.png
```

## 🔧 Configuration Options

QRConnect offers several optional configuration settings:

- **Custom Size**: Adjust the size of the generated QR code (default: 300x300 pixels)
- **Error Correction**: Set the error correction level for better scan reliability
- **Custom Colors**: Modify foreground and background colors for branded QR codes

Example with options:
```
python qrconnect.py --size 400 --error-correction H --fg-color "#000000" --bg-color "#FFFFFF"
```

## 📊 Use Cases

- Add QR codes to business cards linking to your website or portfolio
- Create scannable links for promotional materials
- Generate QR codes for Wi-Fi network access
- Share contact information via vCard QR codes
- Link to app download pages from physical marketing materials

## 🛠️ Technical Details

QRConnect is built using:
- Python's qrcode library for QR generation
- Pillow (PIL) for image processing and saving
- Command-line interface for ease of use

## 🤝 Contributing

Contributions to QRConnect are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

[Include your license information here]

## 📞 Contact

who0xac - [GitHub Profile](https://github.com/who0xac)

Project Link: [https://github.com/who0xac/qrconnect](https://github.com/who0xac/qrconnect)

---

*QRConnect - Bridging the Physical and Digital Worlds Through QR Codes*

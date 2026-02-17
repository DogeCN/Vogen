# Vogen

AI-powered text-to-speech tool with voice selection and speed control.

## Features

- 8 different voice characters to choose from
- Adjustable speech speed
- Real-time audio playback
- Save generated audio to file
- Interactive menu interface

## Requirements

- Python 3.12
- Windows 10/11

## Installation

```bash
# Install dependencies
pdm install

# Build executable
install.bat
```

## Usage

Run the executable:
```bash
dist\main\Vogen.exe
```

Or run from source:
```bash
pdm run python main.py
```

### Controls

- **Arrow Keys**: Navigate voice selection
- **Enter**: Confirm selection
- **ESC**: Exit

### Voice Characters

- Alba
- Marius
- Javert
- Jean
- Fantine
- Cosette
- Eponine
- Azelma

## Development

### Project Structure

```
Vogen/
├── main.py           # Main application
├── dialog.py         # File dialog module
├── main.spec         # PyInstaller configuration
├── install.bat       # Build script
├── cleanup.bat       # Post-build cleanup
└── auto_cleanup.py   # Automatic cleanup optimizer
```

### Building

```bash
# Build with PyInstaller
install.bat

# Optimize build size
python auto_cleanup.py
cleanup_auto.bat
```

## Aknowledgement

[Pocket TTS](https://kyutai.org/pocket-tts)

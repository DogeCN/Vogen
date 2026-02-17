import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from miniaudio import PlaybackDevice, stream_file
from pocket_tts import TTSModel
from pathlib import Path
import scipy.io.wavfile
import torch, time, msvcrt
from shutil import copy2
from dialog import get

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.align import Align

TEMP = Path(os.environ["TEMP"]) / "Vogen"
TEMP.mkdir(exist_ok=True)
VOICES = [
    "Alba",
    "Marius",
    "Javert",
    "Jean",
    "Fantine",
    "Cosette",
    "Eponine",
    "Azelma",
]


console = Console()


class Model:
    def __init__(self):
        self.model = TTSModel.load_model()
        self.states = {}

    def switch(self, index: int):
        self.index = index
        if (TEMP / f"{index}.vts").exists():
            with open(TEMP / f"{index}.vts", "rb") as f:
                data = torch.load(f)
        else:
            data = self.model.get_state_for_audio_prompt(VOICES[index].lower())
            with open(TEMP / f"{index}.vts", "wb") as f:
                torch.save(data, f)
        self.states[index] = data

    def generate(self, path: Path, text: str, speed: float = 1.0):
        audio = self.model.generate_audio(self.states[self.index], text)
        rate = int(self.model.sample_rate * speed)
        with open(path, "wb") as f:
            scipy.io.wavfile.write(f, rate, audio.numpy())

    def speak(self, text: str, speed: float = 1.0):
        path = TEMP / f"temp_{time.time_ns()}.wav"
        self.generate(path, text, speed=speed)
        return path

    def greet(self):
        path = TEMP / f"{self.index}.wav"
        if not path.exists():
            with console.status(
                f"[green] Generating greeting from [bold cyan]{VOICES[self.index]}[/bold cyan] ...[/green]"
            ):
                self.generate(
                    path,
                    f"Hello, I'm {VOICES[self.index]}. I hope you can understand me clearly. Thanks!",
                )
        return path


class Menu:
    def __init__(self, options, title, index=0, callback=None):
        self.options = options
        self.title = title
        self.index = index
        self.callback = callback
        self.running = True
        self.result = None

    def draw(self):
        lines = []
        for i, opt in enumerate(self.options):
            template = "[bold cyan]👉 %s[/bold cyan]" if self.index == i else "   %s"
            lines.append(template % opt)
        return Panel(
            Align.center("\n".join(lines)),
            title=self.title,
            title_align="left",
            border_style="bright_blue",
            padding=(1, 2),
        )

    def run(self):
        with Live(self.draw(), console=console, refresh_per_second=10) as live:
            while self.running:
                key = msvcrt.getch()
                if key == b"\r":
                    self.result = self.index
                    break
                elif key == b"\x1b":
                    self.result = None
                    break
                elif key == b"\xe0":
                    arrow = msvcrt.getch()
                    if arrow in (b"H", b"P"):
                        self.index = (self.index + {b"H": -1, b"P": 1}[arrow]) % len(
                            self.options
                        )
                        live.update(self.draw())
                        if self.callback:
                            self.callback(self.index)
        return self.result


with console.status("[bold green] Loading ...[/bold green]"):
    model = Model()
    current: PlaybackDevice = None

    def selecting(index):
        global current
        model.switch(index)
        if current:
            current.close()
        device = PlaybackDevice()
        device.start(stream_file(model.greet()))
        current = device

    selecting(0)


while True:
    try:
        menu = Menu(
            VOICES,
            title="🎙️  Select a voice character",
            index=model.index,
            callback=selecting,
        )
        selected = menu.run()
        if selected is None:
            break

        if current:
            current.close()
            current = None

        selected_voice = VOICES[selected]
        console.print(
            f"[green]✅ Selected:[/green] [bold cyan]{selected_voice}[/bold cyan]"
        )

        text = console.input("[cyan]📝 Text to synthesize: [/cyan]").strip()
        if not text:
            console.print("[dim]Returning ...[/dim]\n")
            continue

        speed = console.input("[dark_orange]⚡ Speed (1.0): [/dark_orange]").strip()
        if speed:
            try:
                speed = float(speed)
            except ValueError:
                console.print("[red]⚠️  Invalid speed[/red]\n")
                continue
        else:
            speed = 1.0

        with console.status("[bold green] Generating ...[/bold green]"):
            path = model.speak(text, speed)

        rate, audio = scipy.io.wavfile.read(path)
        duration = len(audio) / rate
        console.print(f"[cyan]⏱️  Duration: {duration:.2f} s[/cyan]")

        stream = stream_file(path)
        device = PlaybackDevice()
        device.start(stream)

        start = time.time()
        while time.time() - start < duration:
            if msvcrt.kbhit() and msvcrt.getch() == b"\r":
                break
            time.sleep(0.01)
        device.close()

        dst = get()
        if dst:
            copy2(path, dst)
            console.print("[green]✅ Completed[/green]\n")
        else:
            console.print("[yellow]⚠️  Cancelled[/yellow]\n")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]\n")

if current:
    current.close()

import os
import re
import sys
import time
import threading
from pathlib import Path
from typing import Final, Optional

import qrcode
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class QRConnectError(Exception):
    pass

class InputValidator:
    MAX_DATA_LENGTH: Final[int] = 4096
    MAX_FILENAME_LENGTH: Final[int] = 255
    ALLOWED_EXTENSIONS: Final[tuple] = ('.png', '.jpg', '.jpeg')
    DANGEROUS_PATTERNS: Final[tuple] = (
        r'\.\.',
        r'[<>:"|?*]',
        r'^\/|\\',
        r'\0'
    )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        if not filename or len(filename) > InputValidator.MAX_FILENAME_LENGTH:
            raise QRConnectError("Invalid filename length")
        
        filename = filename.strip()
        
        for pattern in InputValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, filename):
                raise QRConnectError("Filename contains invalid characters")
        
        path = Path(filename)
        if path.suffix.lower() not in InputValidator.ALLOWED_EXTENSIONS:
            filename = f"{path.stem}.png"
        
        if path.is_absolute() or '..' in path.parts:
            raise QRConnectError("Absolute paths not allowed")
        
        return filename
    
    @staticmethod
    def validate_data(data: str) -> str:
        if not data or not data.strip():
            raise QRConnectError("Data cannot be empty")
        
        if len(data) > InputValidator.MAX_DATA_LENGTH:
            raise QRConnectError(f"Data exceeds maximum length of {InputValidator.MAX_DATA_LENGTH}")
        
        if '\0' in data:
            raise QRConnectError("Data contains null bytes")
        
        return data.strip()

class SecureFileEraser:
    VSITR_PASSES: Final[int] = 7
    VSITR_PATTERNS: Final[tuple] = (
        b'\x00',
        b'\xFF',
        b'\x00',
        b'\xFF',
        b'\x00',
        b'\xFF',
        b'\xAA'
    )
    
    @staticmethod
    def secure_erase(filepath: Path) -> bool:
        try:
            if not filepath.exists() or not filepath.is_file():
                return False
            
            file_size = filepath.stat().st_size
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Securely erasing file (VSITR)...", total=None)
                
                for pass_num in range(SecureFileEraser.VSITR_PASSES):
                    pattern = SecureFileEraser.VSITR_PATTERNS[pass_num]
                    
                    with open(filepath, 'r+b') as f:
                        f.seek(0)
                        
                        chunk_size = 65536
                        remaining = file_size
                        
                        while remaining > 0:
                            write_size = min(chunk_size, remaining)
                            f.write(pattern * write_size)
                            remaining -= write_size
                        
                        f.flush()
                        os.fsync(f.fileno())
                    
                    progress.update(task, description=f"VSITR pass {pass_num + 1}/{SecureFileEraser.VSITR_PASSES}")
            
            filepath.unlink()
            
            console.print(f"\n File securely erased: {filepath.name}\n")
            return True
            
        except Exception as e:
            console.print(f"\n Error during secure erasure: {str(e)}\n")
            return False

class AutoEraseTimer:
    def __init__(self, filepath: Path, delay_seconds: int = 30):
        self.filepath = filepath
        self.delay_seconds = delay_seconds
        self.timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()
        self.cancelled = False
    
    def start(self) -> None:
        with self.lock:
            if self.timer is not None:
                self.timer.cancel()
            
            self.cancelled = False
            self.timer = threading.Timer(self.delay_seconds, self._erase_callback)
            self.timer.daemon = True
            self.timer.start()
            
            console.print(f"Auto-erase timer started: {self.delay_seconds} seconds\n")
    
    def reset(self) -> None:
        with self.lock:
            if not self.cancelled and self.timer is not None:
                self.timer.cancel()
                self.start()
                console.print(f"Timer reset: {self.delay_seconds} seconds remaining\n")
    
    def cancel(self) -> None:
        with self.lock:
            self.cancelled = True
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None
    
    def _erase_callback(self) -> None:
        with self.lock:
            if self.cancelled:
                return
            
            console.print("\n initiating secure erasure\n")
            SecureFileEraser.secure_erase(self.filepath)

class QRConnect:
    DEFAULT_SIZE: Final[tuple] = (300, 300)
    MIN_SIZE: Final[int] = 100
    MAX_SIZE: Final[int] = 2000
    
    def __init__(self, data: str, filename: str = "qrcode.png", size: tuple = DEFAULT_SIZE):
        self.data = InputValidator.validate_data(data)
        self.filename = InputValidator.sanitize_filename(filename)
        self.size = self._validate_size(size)
        self.erase_timer: Optional[AutoEraseTimer] = None
    
    def _validate_size(self, size: tuple) -> tuple:
        if not isinstance(size, tuple) or len(size) != 2:
            raise QRConnectError("Size must be a tuple of two integers")
        
        width, height = size
        if not all(isinstance(dim, int) for dim in [width, height]):
            raise QRConnectError("Size dimensions must be integers")
        
        if not (self.MIN_SIZE <= width <= self.MAX_SIZE and self.MIN_SIZE <= height <= self.MAX_SIZE):
            raise QRConnectError(f"Size must be between {self.MIN_SIZE} and {self.MAX_SIZE}")
        
        return size
    
    def _generate_ascii_qr(self) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=1,
            border=2,
        )
        qr.add_data(self.data)
        qr.make(fit=True)
        
        return qr.get_matrix()
    
    def display_ascii_qr(self) -> None:
        matrix = self._generate_ascii_qr()
        
        ascii_art = []
        for row in matrix:
            line = ''.join('██' if cell else '  ' for cell in row)
            ascii_art.append(line)
        
        qr_content = '\n'.join(ascii_art)
        
        panel = Panel(
            qr_content,
            title="[bold cyan]Scannable QR Code[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        console.print("\n")
        console.print(panel)
        console.print("\n")
    
    def generate_qr_code(self) -> None:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(self.data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            img = img.resize(self.size, Image.Resampling.LANCZOS)
            
            output_path = Path(self.filename)
            if output_path.exists():
                console.print(f"[yellow]Warning: File '{self.filename}' already exists[/yellow]")
                overwrite = Prompt.ask(
                    "Overwrite?",
                    choices=["y", "n"],
                    default="n"
                )
                if overwrite.lower() != 'y':
                    raise QRConnectError("Operation cancelled by user")
            
            img.save(str(output_path), optimize=True)
            
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_row(" Status", "Success")
            table.add_row(" File", f"{self.filename}")
            table.add_row(" Size", f"{self.size[0]}x{self.size[1]}px")
            table.add_row(" Security", "Auto-erase enabled")
            
            console.print("\n")
            console.print(Panel(table, title="[bold green]QR Code Generated[/bold green]", border_style="green"))
            
            self.display_ascii_qr()
            
            self.erase_timer = AutoEraseTimer(output_path, delay_seconds=30)
            self.erase_timer.start()
            
            self._monitor_scans()
            
        except OSError as e:
            raise QRConnectError(f"File system error: {str(e)}")
        except Exception as e:
            raise QRConnectError(f"Unexpected error: {str(e)}")
    
    def _monitor_scans(self) -> None:
        console.print("[dim]Commands: [bold]r[/bold]=reset timer | [bold]e[/bold]=erase now | [bold]q[/bold]=quit without erase[/dim]\n")
        
        try:
            while True:
                user_input = console.input("[cyan]>[/cyan] ").strip().lower()
                
                if user_input == 'r':
                    if self.erase_timer:
                        self.erase_timer.reset()
                    
                elif user_input == 'e':
                    if self.erase_timer:
                        self.erase_timer.cancel()
                    
                    output_path = Path(self.filename)
                    if output_path.exists():
                        SecureFileEraser.secure_erase(output_path)
                    break
                    
                elif user_input == 'q':
                    if self.erase_timer:
                        self.erase_timer.cancel()
                    console.print("\n[yellow]Exiting without erasure[/yellow]\n")
                    break
                    
                else:
                    console.print("[dim]Invalid command. Use: r (reset) | e (erase) | q (quit)[/dim]")
                    
        except KeyboardInterrupt:
            if self.erase_timer:
                self.erase_timer.cancel()
            console.print("\n\n[yellow]Monitoring interrupted[/yellow]\n")

def main() -> None:
    try:
        console.print("\n[bold cyan]QR Code Generator[/bold cyan]\n", style="bold")
        
        data = Prompt.ask("[yellow]Enter data to encode[/yellow] (URL, text, etc.)")
        
        filename = Prompt.ask(
            "[yellow]Enter filename[/yellow]",
            default="qrcode.png"
        )
        
        qr_connect = QRConnect(data, filename)
        qr_connect.generate_qr_code()
        
    except QRConnectError as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled by user[/yellow]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/bold red] {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

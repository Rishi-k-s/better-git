#!/usr/bin/env python3
"""
Simple LogSeq Directory Selector - A cute terminal-based LogSeq folder picker
"""

import os
import stat
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, Center
from textual.widgets import (
    Header, 
    Footer, 
    Static, 
    DataTable,
    Input,
    Button
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message
from textual import events


class LogSeqValidator:
    """Validates LogSeq directory structure"""
    
    @staticmethod
    def validate_logseq_structure(directory: Path) -> Tuple[bool, List[str]]:
        """
        Validate if directory follows LogSeq structure
        Returns (is_valid, summary_list)
        """
        if not directory.exists() or not directory.is_dir():
            return False, ["📁 Path doesn't exist or isn't a directory"]
        
        summary = []
        is_valid = True
        
        # Check for essential LogSeq items
        required_items = ["logseq", "pages", "journals"]
        
        for item in required_items:
            item_path = directory / item
            if item_path.exists() and item_path.is_dir():
                summary.append(f"✅ {item}/")
            else:
                summary.append(f"❌ {item}/")
                is_valid = False
        
        # Quick check for content
        try:
            pages_dir = directory / "pages"
            if pages_dir.exists():
                md_count = len(list(pages_dir.glob("*.md")))
                summary.append(f"📄 {md_count} pages")
            
            journals_dir = directory / "journals"
            if journals_dir.exists():
                journal_count = len(list(journals_dir.glob("*.md")))
                summary.append(f"📅 {journal_count} journals")
        except:
            pass
        
        return is_valid, summary


class FileTable(DataTable):
    """Cute file table for navigation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_directory: Optional[Path] = None
        self.directory_history: List[Path] = []
        self.setup_table()
    
    def setup_table(self):
        """Setup the table columns"""
        self.add_column("📁 Name", key="name", width=50)
        self.add_column("📊 Type", key="type", width=8)
        self.add_column("📏 Size", key="size", width=12)
    
    def load_directory(self, directory: Path, add_to_history: bool = True):
        """Load files from directory into table"""
        if add_to_history and self.current_directory and self.current_directory != directory:
            self.directory_history.append(self.current_directory)
        
        self.current_directory = directory
        self.clear()
        
        if not directory.exists() or not directory.is_dir():
            return
            
        try:
            entries = []
            
            # Add back button if we have history
            if self.directory_history:
                entries.append(("🔙 Back", "NAV", ""))
            
            # Add parent directory if not root
            if directory.parent != directory:
                entries.append(("⬆️ Up", "NAV", ""))
            
            # Get directory contents
            directories = []
            files = []
            
            for item in directory.iterdir():
                try:
                    # Skip some hidden files but keep important ones
                    if item.name.startswith('.') and item.name not in ['.logseq']:
                        continue
                    
                    stat_info = item.stat()
                    
                    if item.is_dir():
                        try:
                            item_count = len(list(item.iterdir()))
                            size = f"{item_count} items"
                        except:
                            size = "folder"
                        directories.append((f"📁 {item.name}", "DIR", size))
                    else:
                        size = self._format_size(stat_info.st_size)
                        files.append((f"📄 {item.name}", "FILE", size))
                        
                except (PermissionError, OSError):
                    if item.is_dir():
                        directories.append((f"📁 {item.name}", "DIR", "locked"))
                    else:
                        files.append((f"📄 {item.name}", "FILE", "locked"))
            
            # Sort and combine
            directories.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())
            
            entries.extend(directories)
            entries.extend(files)
            
            # Add rows to table
            for entry in entries:
                self.add_row(*entry)
                
        except PermissionError:
            self.add_row("🔒 Permission denied", "ERROR", "")
    
    def go_back(self) -> Optional[Path]:
        """Go back to previous directory"""
        if self.directory_history:
            return self.directory_history.pop()
        return None
    
    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.0f}{unit}"
            size /= 1024.0
        return f"{size:.0f}TB"


class LogSeqStatus(Static):
    """Cute status widget for LogSeq validation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_path: Optional[Path] = None
        self.is_valid = False
    
    def check_logseq_structure(self, path: Path):
        """Check and display LogSeq structure validation"""
        self.current_path = path
        
        is_valid, summary = LogSeqValidator.validate_logseq_structure(path)
        self.is_valid = is_valid
        
        if is_valid:
            header = "🎉 Valid LogSeq Directory!"
            header_style = "bold green"
        else:
            header = "❌ Not a LogSeq Directory"
            header_style = "bold red"
        
        status_text = f"[{header_style}]{header}[/{header_style}]\n\n"
        
        # Show summary
        for item in summary:
            status_text += f"{item}\n"
        
        # Show path
        status_text += f"\n📂 [dim]{str(path)}[/dim]"
        
        self.update(status_text)


class LogSeqDirectorySelector(App):
    """Simple and cute LogSeq Directory Selector"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #header-container {
        height: 6;
        background: $primary;
        color: $text;
        padding: 1;
        margin-bottom: 1;
    }
    
    #main-container {
        height: 1fr;
        layout: horizontal;
        margin-bottom: 1;
    }
    
    #files-panel {
        width: 2fr;
        background: $surface;
        border: solid $primary;
        padding: 1;
        margin-right: 1;
    }
    
    #status-panel {
        width: 1fr;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    #path-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #buttons-container {
        height: 4;
        layout: horizontal;
        align: center middle;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
        min-width: 15;
    }
    
    FileTable {
        height: 1fr;
    }
    
    LogSeqStatus {
        height: 1fr;
    }
    
    .title {
        text-align: center;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("ctrl+l", "focus_path", "Focus Path"),
        Binding("enter", "open_selected", "Open"),
        Binding("backspace", "go_back", "Back"),
        Binding("ctrl+s", "select_current", "Select"),
    ]
    
    current_directory = reactive(Path.cwd())
    selected_directory: Optional[Path] = None
    
    def __init__(self):
        super().__init__()
        self.title = "LogSeq Directory Selector"
        self.sub_title = "Find your LogSeq folder 📁"
    
    def compose(self) -> ComposeResult:
        """Compose the cute UI"""
        yield Header(show_clock=True)
        
        with Container(id="header-container"):
            yield Static("[bold]🔍 LogSeq Directory Selector[/bold]", classes="title")
            yield Input(
                placeholder="🏠 Enter path or browse below...",
                value=str(self.current_directory),
                id="path-input"
            )
        
        with Container(id="main-container"):
            with Container(id="files-panel"):
                yield Static("📂 [bold]Files & Folders[/bold]")
                yield FileTable(id="file-table")
            
            with Container(id="status-panel"):
                yield Static("✅ [bold]LogSeq Check[/bold]")
                yield LogSeqStatus(id="logseq-status")
        
        with Center(id="buttons-container"):
            yield Button("🔙 Back", id="back-btn", variant="default")
            yield Button("🔄 Refresh", id="refresh-btn", variant="primary")
            yield Button("✅ Select This Folder", id="select-btn", variant="success")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the cute app"""
        self.refresh_all()
    
    def on_file_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle cute file selection"""
        table = self.query_one("#file-table", FileTable)
        
        if table.current_directory and event.row_key is not None:
            row_data = table.get_row(event.row_key)
            filename = row_data[0]
            
            # Handle navigation
            if filename == "🔙 Back":
                self.action_go_back()
            elif filename == "⬆️ Up":
                self.current_directory = table.current_directory.parent
                self.refresh_all()
            elif row_data[1] == "DIR":
                # Remove emoji and get actual folder name
                folder_name = filename.replace("📁 ", "")
                selected_path = table.current_directory / folder_name
                self.check_logseq_structure(selected_path)
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle path input"""
        if event.input.id == "path-input":
            try:
                new_path = Path(event.value).expanduser().resolve()
                if new_path.exists() and new_path.is_dir():
                    self.current_directory = new_path
                    self.refresh_all()
                else:
                    self.notify("🚫 Invalid path or not a directory", severity="error")
            except Exception as e:
                self.notify(f"❌ Error: {str(e)}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cute button presses"""
        if event.button.id == "select-btn":
            self.action_select_current()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "back-btn":
            self.action_go_back()
    
    def action_open_selected(self) -> None:
        """Open selected folder"""
        table = self.query_one("#file-table", FileTable)
        
        if table.cursor_row is not None and table.current_directory:
            row_data = table.get_row(table.cursor_row)
            filename = row_data[0]
            
            if filename == "🔙 Back":
                self.action_go_back()
            elif filename == "⬆️ Up":
                self.current_directory = table.current_directory.parent
                self.refresh_all()
            elif row_data[1] == "DIR":
                folder_name = filename.replace("📁 ", "")
                new_path = table.current_directory / folder_name
                self.current_directory = new_path
                self.refresh_all()
    
    def action_go_back(self) -> None:
        """Go back cutely"""
        table = self.query_one("#file-table", FileTable)
        previous_dir = table.go_back()
        
        if previous_dir:
            self.current_directory = previous_dir
            self.refresh_all()
        else:
            self.notify("🏠 Already at the starting point!")
    
    def action_select_current(self) -> None:
        """Select current directory as LogSeq folder"""
        status_widget = self.query_one("#logseq-status", LogSeqStatus)
        
        if hasattr(status_widget, 'is_valid') and status_widget.is_valid:
            self.selected_directory = self.current_directory
            self.notify(f"🎉 Selected: {self.current_directory.name}", title="LogSeq Directory Selected!", severity="information")
            # You could add code here to save the selection or exit
            print(f"Selected LogSeq directory: {self.current_directory}")
        else:
            self.notify("❌ Can't select: Not a valid LogSeq directory", severity="error")
    
    def action_refresh(self) -> None:
        """Refresh cutely"""
        self.refresh_all()
        self.notify("🔄 Refreshed!")
    
    def action_focus_path(self) -> None:
        """Focus the path input"""
        self.query_one("#path-input").focus()
    
    def check_logseq_structure(self, path: Optional[Path] = None) -> None:
        """Check LogSeq structure"""
        target_path = path or self.current_directory
        logseq_status = self.query_one("#logseq-status", LogSeqStatus)
        logseq_status.check_logseq_structure(target_path)
    
    def refresh_all(self) -> None:
        """Refresh everything cutely"""
        self.sub_title = f"📂 {self.current_directory.name}"
        
        # Update path input
        path_input = self.query_one("#path-input", Input)
        path_input.value = str(self.current_directory)
        
        # Update file table
        table = self.query_one("#file-table", FileTable)
        table.load_directory(self.current_directory)
        
        # Check current directory
        self.check_logseq_structure()


def main():
    """Run the cute LogSeq directory selector"""
    app = LogSeqDirectorySelector()
    app.run()


if __name__ == "__main__":
    main()
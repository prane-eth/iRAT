#!/usr/bin/env python3
"""
Interactive DataFrame Viewer
Allows viewing each row of a dataframe one by one with proper newline formatting.
"""

import pandas as pd
import json
import os
from typing import Optional


class InteractiveDataFrameViewer:
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the viewer with a dataframe.
        
        Args:
            df: The pandas DataFrame to view
        """
        self.df = df
        self.current_index = 0
        self.total_rows = len(df)
        
    def format_text(self, text: str) -> str:
        """
        Replace \\n characters with actual newlines and format the text.
        
        Args:
            text: The text to format
            
        Returns:
            Formatted text with proper newlines
        """
        if isinstance(text, str):
            return text.replace('\\n', '\n')
        return str(text)
    
    def display_row(self, index: int) -> None:
        """
        Display a specific row with proper formatting.
        
        Args:
            index: The row index to display
        """
        if index < 0 or index >= self.total_rows:
            print(f"Invalid index. Please use a value between 0 and {self.total_rows - 1}")
            return
            
        print("=" * 80)
        print(f"ROW {index + 1} of {self.total_rows} (Index: {index})")
        print("=" * 80)
        
        row = self.df.iloc[index]
        
        for column, value in row.items():
            print(f"\n📋 {column.upper()}:")
            print("-" * (len(column) + 6))
            formatted_value = self.format_text(str(value))
            print(formatted_value)
        
        print("\n" + "=" * 80)
    
    def navigate(self) -> None:
        """
        Interactive navigation through the dataframe.
        """
        print(f"🔍 Interactive DataFrame Viewer")
        print(f"📊 Dataset contains {self.total_rows} rows with columns: {list(self.df.columns)}")
        print("\nCommands:")
        print("  - 'n' or 'next': Go to next row")
        print("  - 'p' or 'prev': Go to previous row")
        print("  - 'g <number>': Go to specific row number (1-based)")
        print("  - 'i <index>': Go to specific index (0-based)")
        print("  - 'f' or 'first': Go to first row")
        print("  - 'l' or 'last': Go to last row")
        print("  - 'info': Show dataframe info")
        print("  - 'columns': Show column names")
        print("  - 'search <column> <text>': Search for text in a column")
        print("  - 'q' or 'quit': Exit")
        print("-" * 80)
        
        # Display first row initially
        self.display_row(self.current_index)
        
        while True:
            try:
                command = input(f"\n[Row {self.current_index + 1}/{self.total_rows}] Enter command: ").strip().lower()
                
                if command in ['q', 'quit']:
                    print("👋 Goodbye!")
                    break
                    
                elif command in ['n', 'next']:
                    if self.current_index < self.total_rows - 1:
                        self.current_index += 1
                        self.display_row(self.current_index)
                    else:
                        print("Already at the last row!")
                        
                elif command in ['p', 'prev']:
                    if self.current_index > 0:
                        self.current_index -= 1
                        self.display_row(self.current_index)
                    else:
                        print("Already at the first row!")
                        
                elif command in ['f', 'first']:
                    self.current_index = 0
                    self.display_row(self.current_index)
                    
                elif command in ['l', 'last']:
                    self.current_index = self.total_rows - 1
                    self.display_row(self.current_index)
                    
                elif command.startswith('g '):
                    try:
                        row_number = int(command.split()[1])
                        if 1 <= row_number <= self.total_rows:
                            self.current_index = row_number - 1
                            self.display_row(self.current_index)
                        else:
                            print(f"Please enter a row number between 1 and {self.total_rows}")
                    except (ValueError, IndexError):
                        print("Invalid format. Use 'g <row_number>' (e.g., 'g 5')")
                        
                elif command.startswith('i '):
                    try:
                        index = int(command.split()[1])
                        if 0 <= index < self.total_rows:
                            self.current_index = index
                            self.display_row(self.current_index)
                        else:
                            print(f"Please enter an index between 0 and {self.total_rows - 1}")
                    except (ValueError, IndexError):
                        print("Invalid format. Use 'i <index>' (e.g., 'i 4')")
                        
                elif command == 'info':
                    print("\n📊 DataFrame Info:")
                    print(f"Shape: {self.df.shape}")
                    print(f"Columns: {list(self.df.columns)}")
                    print(f"Data types:\n{self.df.dtypes}")
                    
                elif command == 'columns':
                    print(f"\n📋 Columns: {list(self.df.columns)}")
                    
                elif command.startswith('search '):
                    try:
                        parts = command.split(' ', 2)
                        if len(parts) >= 3:
                            column = parts[1]
                            search_text = parts[2]
                            
                            if column in self.df.columns:
                                mask = self.df[column].astype(str).str.contains(search_text, case=False, na=False)
                                matching_indices = self.df[mask].index.tolist()
                                
                                if matching_indices:
                                    print(f"\n🔍 Found {len(matching_indices)} matches in column '{column}':")
                                    for i, idx in enumerate(matching_indices[:10]):  # Show first 10
                                        print(f"  Row {idx + 1} (Index {idx})")
                                    if len(matching_indices) > 10:
                                        print(f"  ... and {len(matching_indices) - 10} more")
                                    
                                    # Go to first match
                                    if matching_indices:
                                        self.current_index = matching_indices[0]
                                        print(f"\n📍 Jumping to first match:")
                                        self.display_row(self.current_index)
                                else:
                                    print(f"No matches found for '{search_text}' in column '{column}'")
                            else:
                                print(f"Column '{column}' not found. Available columns: {list(self.df.columns)}")
                        else:
                            print("Invalid format. Use 'search <column> <text>' (e.g., 'search prompt def')")
                    except Exception as e:
                        print(f"Search error: {e}")
                        
                else:
                    print("Unknown command. Type 'q' to quit or use the commands listed above.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def load_dataframe_from_jsonl(file_path: str) -> pd.DataFrame:
    """
    Load a dataframe from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        Pandas DataFrame
    """
    with open(file_path, 'r') as f:
        data = [json.loads(line) for line in f]
    return pd.DataFrame(data)


def main():
    """
    Main function to run the interactive viewer.
    """
    print("🔍 Interactive DataFrame Viewer")
    print("=" * 50)
    
    default_path = 'irat/data/human_eval.jsonl'
    
    if os.path.exists(default_path):
        print(f"📁 Loading default dataset: {default_path}")
        df = load_dataframe_from_jsonl(default_path)
    else:
        # Ask user for file path
        file_path = input("Enter the path to your JSONL file (or press Enter to use sample data): ").strip()
        
        if not file_path:
            # Create sample data for demonstration
            print("Creating sample data for demonstration...")
            sample_data = [
                {
                    "task_id": "Sample/0",
                    "prompt": "def hello_world():\\n    '''Print hello world message'''\\n    pass",
                    "entry_point": "hello_world",
                    "canonical_solution": "print('Hello, World!')\\n",
                    "test": "assert hello_world() is None\\n"
                },
                {
                    "task_id": "Sample/1", 
                    "prompt": "def add_numbers(a, b):\\n    '''Add two numbers together'''\\n    pass",
                    "entry_point": "add_numbers",
                    "canonical_solution": "return a + b\\n",
                    "test": "assert add_numbers(2, 3) == 5\\n"
                }
            ]
            df = pd.DataFrame(sample_data)
        else:
            if file_path.endswith('.jsonl'):
                df = load_dataframe_from_jsonl(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                print("Unsupported file format. Please use .jsonl, .csv, or .json files.")
                return
    
    # Start the interactive viewer
    viewer = InteractiveDataFrameViewer(df)
    viewer.navigate()


if __name__ == "__main__":
    main() 
from typing import Any
from pathlib import Path
from io import BytesIO
import pandas as pd

class SpreadsheetViewException(ValueError):
    """
    Error raised for problems with loading or accessing spreadsheet data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class SpreadsheetView:
    """
    Read an Excel file and provide simple helpers to access its data.

    The first row of each sheet is treated as column headers.
    """

    def __init__(self, file: str | Path | bytes):
        """
        Create a view bound to the given Excel file path or blob.
        """

        self.__file: str | Path | bytes = file
        self.__sheets: list[str] = []
        self.__data_frames: dict[str, pd.DataFrame] = {}

    def load_data(self):
        """
        Read all sheets from the Excel file into internal pandas DataFrames.
        """

        try:
            self.__sheets.clear()
            self.__data_frames.clear()
            self.__data_frames.update(pd.read_excel(
                Path(self.__file) if isinstance(self.__file, (str, Path)) else BytesIO(self.__file),
                sheet_name=None,
                header=0
            ))
            self.__sheets.extend(self.__data_frames.keys())
        except FileNotFoundError:
            raise SpreadsheetViewException(f"Table '{self.__file_path}' does not exist or is not a file!") 
        except PermissionError:
            raise SpreadsheetViewException(
                f"Table '{self.__file_path}' is not readable, please change its permissions in your file browser!"
            ) 
        except ValueError as e:
            raise SpreadsheetViewException(f"Table '{self.__file_path}' is not a valid Excel file ({e})")
        except ImportError:
            raise SpreadsheetViewException("Required libraries are missing, please run 'install'")
        except Exception as e:
            raise SpreadsheetViewException(f"Error while loading spreadsheet file '{self.__file_path}' ({e})")
    
    def __compute_sheet_name(self, sheet: str | int):
        """
        Convert a sheet identifier (name or index) into an existing sheet name.
        """

        key = None
        if isinstance(sheet, str):
            if key in self.__sheets:
                key = sheet
            else:
                raise SpreadsheetViewException(
                    f"Sheet {sheet} was not found in '{self.__file_path}'!"
                )
        elif isinstance(sheet, (int, float)):
            if sheet >= 0 and len(self.__sheets) > sheet:
                key = self.__sheets[int(sheet)]
            else:
                raise SpreadsheetViewException(
                    f"Sheet index {sheet} is out of range for '{self.__file_path}'!"
                )
        else:
            raise SpreadsheetViewException(
                f"Type '{type(sheet)}' is not supported as a sheet identifier!"
            )

        return key

    def get_column_names(self, sheet: str | int) -> list[str]:
        """
        Return all column names for the specified sheet.
        """

        return self.__data_frames[self.__compute_sheet_name(sheet)].columns.tolist()

    def get_all_rows(self, sheet: str | int) -> list[dict[str, Any]]:
        """
        Return all rows of the sheet as dictionaries keyed by column name.
        """

        return self.__data_frames[self.__compute_sheet_name(sheet)].to_dict("records")
    
    def get_all_rows_as_array(self, sheet: str | int) -> list[list[Any]]:
        """
        Return all rows of the sheet as lists of values in column order.
        """

        df = self.__data_frames[self.__compute_sheet_name(sheet)]
        return df.values.tolist()

    def get_row_by_index(self, sheet: str | int, index: int) -> dict[str, Any]:
        """
        Return one row by index as a dictionary keyed by column name.
        """

        df = self.__data_frames[self.__compute_sheet_name(sheet)]
        if index < 0 or index >= len(df):
            raise SpreadsheetViewException(
                f"Row index {index} is out of range for sheet {sheet} in '{self.__file_path}'!"
            )
        return df.iloc[index].to_dict()
    
    def get_row_by_index_as_array(self, sheet: str | int, index: int) -> list[Any]:
        """
        Return one row by index as a list of values in column order.
        """

        df = self.__data_frames[self.__compute_sheet_name(sheet)]

        if index < 0 or index >= len(df):
            raise SpreadsheetViewException(
                f"Row index {index} is out of range for sheet {sheet} in '{self.__file_path}'!"
            )

        return df.iloc[index].tolist()
    
    def get_column(self, sheet: str | int, column: str | int) -> list[Any]:
        """
        Return one column from the sheet as a list of cell values.
        """

        df = self.__data_frames[self.__compute_sheet_name(sheet)]

        if isinstance(column, int):
            if column < 0 or column >= len(df.columns):
                raise SpreadsheetViewException(
                    f"Column index {column} is out of range for sheet {sheet} in '{self.__file_path}'!"
                )
            return df.iloc[:, column].tolist()

        if isinstance(column, str):
            if column not in df.columns:
                raise SpreadsheetViewException(
                    f"Column '{column}' is not present in sheet {sheet} in '{self.__file_path}'!"
                )
            return df[column].tolist()

        raise SpreadsheetViewException(
            f"Type of column identifier '{type(column).__name__}' is not supported!"
        )

    def get_unique_values(self, sheet: str | int) -> dict[str, list[Any]]:
        """
        Return unique non-null values for every column of the sheet.
        """

        df = self.__data_frames[self.__compute_sheet_name(sheet)]
        res: dict[str, list[Any]] = {}

        for column_name in df.columns.tolist():
            res[column_name] = df[column_name].dropna().unique().tolist()

        return res
    
    def get_data_frame(self, sheet: str | int, deep: bool = True) -> pd.DataFrame:
        """
        Return the pandas DataFrame for the sheet, optionally as a deep copy.
        """

        return self.__data_frames[self.__compute_sheet_name(sheet)].copy(deep)
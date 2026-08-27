from __future__ import annotations
from typing import Any

class DataView:
    """
    Represents a data view for convenient parsing in the UI.

    Contains a label (title), rows (for data table), and sections (nested DataView instances representing subsections).
    """

    def __init__(self, label: str, original: Any = None):
        """
        Initializes the structure with a label and an original object from which this structure was parsed.
        """

        self.__label: str = label
        self.__rows: list[dict[str, Any]] = []
        self.__sections: list[DataView] = []
        self.__original = original
    
    def add_row(self, row: dict[str, Any]):
        """
        Adds a row to the data view.
        """

        self.__rows.append(row)
    
    def add_section(self, section: DataView):
        """
        Adds a subsection (section) to the data view.
        """

        self.__sections.append(section)
    
    @property
    def label(self):
        """
        Returns the label (title) of the data view.
        """

        return self.__label
    
    @property
    def has_label(self):
        """
        Returns True if the data view has a non-empty label.
        """

        return self.__label and len(self.__label)

    @property
    def rows(self):
        """
        Returns the list of rows in the data view.
        """

        return self.__rows
    
    @property
    def rows_length(self):
        """
        Returns the number of rows in the data view.
        """

        return len(self.__rows)

    @property
    def sections(self):
        """
        Returns the list of subsections (nested DataView instances).
        """

        return self.__sections
    
    @property
    def sections_length(self):
        """
        Returns the number of subsections in the data view.
        """

        return len(self.__sections)
    
    @property
    def original(self):
        """
        Returns the original data object associated with this view, if any.
        """

        return self.__original
    
    @property
    def has_original(self):
        """
        Returns True if there is an original data object associated with this view.
        """

        return self.__original is not None

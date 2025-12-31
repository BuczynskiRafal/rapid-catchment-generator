import math
import shutil
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Union, Generator, List
from types import TracebackType

import pandas as pd
import swmmio

from rcg.fuzzy.engine import Prototype
from rcg.fuzzy.categories import LandForm, LandCover
from swmmio.utils.modify_model import replace_inp_section


@dataclass
class SubcatchmentConfig:
    """
    Configuration for a subcatchment with parameters.

    Attributes
    ----------
    area : float
        Subcatchment area in hectares
    land_form : Union[str, LandForm]
        Land form category (str or Enum)
    land_cover : Union[str, LandCover]
        Land cover category (str or Enum)
    prototype : Optional[Prototype]
        Calculated fuzzy prototype
    subcatchment_id : Optional[str]
        Generated unique ID
    """
    area: float
    land_form: Union[str, LandForm]
    land_cover: Union[str, LandCover]
    prototype: Optional[Prototype] = field(default=None, init=False)
    subcatchment_id: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        """
        Minimal validation after initialization.

        Raises
        ------
        ValueError
            If area is not positive
        """
        if self.area <= 0:
            raise ValueError(f"Area must be positive, got: {self.area}")


@dataclass
class ModelParameters:
    """
    Default parameters for different land use types.
    """
    manning_coefficients: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "urban": (0.013, 0.15),
        "suburban": (0.013, 0.24),
        "rural": (0.013, 0.41),
        "forests": (0.40, 0.80),
        "meadows": (0.15, 0.41),
        "arable": (0.06, 0.17),
        "mountains": (0.013, 0.05),
    })

    depression_storage: Dict[str, Tuple[float, float, int]] = field(default_factory=lambda: {
        "urban": (0.05, 0.20, 50),
        "suburban": (0.05, 0.20, 40),
        "rural": (0.05, 0.20, 35),
        "forests": (0.05, 0.30, 5),
        "meadows": (0.05, 0.20, 10),
        "arable": (0.05, 0.20, 10),
        "mountains": (0.05, 0.20, 10),
    })

    infiltration_defaults: Dict[str, Union[float, int]] = field(default_factory=lambda: {
        "Suction": 3.5,
        "Ksat": 0.5,
        "IMD": 0.25,
        "Param4": 7,
        "Param5": 0,
    })


class BuildCatchments:
    """
    Class for creating and managing catchment areas in a SWMM model.

    Provides backup/restore functionality for safe file operations.

    Attributes
    ----------
    file_path : Path
        The file path of the SWMM input file.
    model : swmmio.Model
        The SWMM model object.
    parameters : ModelParameters
        Default parameters for different land use types.
    backup_enabled : bool
        Whether automatic backups are enabled.
    backup_path : Optional[Path]
        Path to the current backup file, if any.
    """

    def __init__(self, file_path: str, backup: bool = True) -> None:
        """
        Initialize with a SWMM model file.

        Parameters
        ----------
        file_path : str
            Path to the SWMM input file.
        backup : bool, optional
            Whether to enable automatic backups (default: True).
        """
        self.file_path = Path(file_path)
        self.model: swmmio.Model = swmmio.Model(str(self.file_path))
        self.parameters = ModelParameters()
        self.backup_enabled = backup
        self.backup_path: Optional[Path] = None
        self._backup_history: List[Path] = []

    def __enter__(self) -> 'BuildCatchments':
        if self.backup_enabled:
            self._create_backup()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        if exc_type is not None:
            print(f"Error occurred: {exc_val}")
            if self.backup_enabled and self.backup_path:
                print(f"Backup available at: {self.backup_path}")

    def _create_backup(self) -> Path:
        """
        Create a timestamped backup of the current INP file.

        Returns
        -------
        Path
            Path to the created backup file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.file_path.stem}_backup_{timestamp}{self.file_path.suffix}"
        backup_dir = self.file_path.parent / ".rcg_backups"
        backup_dir.mkdir(exist_ok=True)

        self.backup_path = backup_dir / backup_name
        shutil.copy2(self.file_path, self.backup_path)
        self._backup_history.append(self.backup_path)

        return self.backup_path

    def restore_backup(self, backup_path: Optional[Path] = None) -> None:
        """
        Restore the INP file from a backup.

        Parameters
        ----------
        backup_path : Optional[Path]
            Path to the backup file to restore. If None, uses the most recent backup.

        Raises
        ------
        FileNotFoundError
            If no backup is available or the specified backup doesn't exist.
        """
        restore_from = backup_path or self.backup_path

        if restore_from is None:
            raise FileNotFoundError("No backup available to restore.")

        if not restore_from.exists():
            raise FileNotFoundError(f"Backup file not found: {restore_from}")

        shutil.copy2(restore_from, self.file_path)
        # Reload the model after restoration
        self.model = swmmio.Model(str(self.file_path))

    def get_backup_history(self) -> List[Path]:
        """
        Get list of all backup files created during this session.

        Returns
        -------
        List[Path]
            List of paths to backup files.
        """
        return self._backup_history.copy()

    def cleanup_backups(self, keep_latest: int = 1) -> int:
        """
        Remove old backup files, keeping only the specified number of latest backups.

        Parameters
        ----------
        keep_latest : int
            Number of latest backups to keep (default: 1).

        Returns
        -------
        int
            Number of backup files removed.
        """
        if not self._backup_history:
            return 0

        # Sort by modification time (newest first)
        sorted_backups = sorted(
            self._backup_history,
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True
        )

        removed_count = 0
        for backup in sorted_backups[keep_latest:]:
            if backup.exists():
                backup.unlink()
                removed_count += 1
                self._backup_history.remove(backup)

        return removed_count

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """
        Context manager for atomic operations on the INP file.

        Creates a backup before operations and restores it if an exception occurs.

        Example
        -------
        >>> with builder.transaction():
        ...     builder.add_subcatchment(10.0, "flats_and_plateaus", "urban_moderately_impervious")
        ...     # If this fails, the file will be restored to its original state
        """
        backup = self._create_backup()
        try:
            yield
        except Exception:
            # Restore on any error
            self.restore_backup(backup)
            raise

    def save(self, output_path: Optional[Path] = None) -> None:
        """
        Save the modified model to the specified path or original file.

        Args:
            output_path: Path to save (defaults to self.file_path)
        """
        save_path = output_path or self.file_path
        self.model.inp.save(str(save_path))
        print(f"Model saved to {save_path}")  # Or use logging

    def _get_new_subcatchment_id(self, counter: int = 1) -> str:
        """Generate a unique subcatchment ID."""
        while True:
            name = f"S{len(self.model.inp.subcatchments) + counter}"
            if name not in self.model.inp.subcatchments.index:
                return name
            counter += 1

    def _add_timeseries(self) -> None:
        """Add a predefined time series to the model."""
        timeseries = pd.DataFrame(
            {
                "Date": [None] * 12,
                "Time": ["1:00", "2:00", "3:00", "4:00", "5:00", "6:00", "7:00", "8:00", "9:00", "10:00", "11:00", "12:00"],
                "Value": ["1", "2", "4", "4", "12", "13", "11", "20", "15", "10", "5", "3"],
            },
            index=["generator_series"] * 12,
        )
        timeseries.index.names = ["Name"]
        self.model.inp.timeseries = pd.concat([self.model.inp.timeseries, timeseries])

    def _get_timeseries(self) -> str:
        """Get or add the first time series name."""
        if len(self.model.inp.timeseries) == 0:
            self._add_timeseries()
        return self.model.inp.timeseries.index[0]

    def _add_raingage(self) -> None:
        """Add a predefined raingage to the model."""
        raingage = pd.DataFrame(
            {
                "RainType": ["INTENSITY"],
                "TimeIntrvl": ["0:01"],
                "SnowCatch": ["1.0"],
                "DataSource": ["TIMESERIES"],
                "DataSourceName": [self._get_timeseries()],
            },
            index=["RG1"],
        )
        raingage.index.names = ["Name"]
        self.model.inp.raingages = raingage

    def _get_raingage(self) -> str:
        """Get or add the first raingage name."""
        if len(self.model.inp.raingages) == 0:
            self._add_raingage()
        return self.model.inp.raingages.index[0]

    def _get_outlet(self, subcatchment_id: str) -> str:
        """Get the outlet (last outfall or junction, or self)."""
        if len(self.model.inp.outfalls) > 0:
            return self.model.inp.outfalls.index[-1]
        if len(self.model.inp.junctions) > 0:
            return self.model.inp.junctions.index[-1]
        return subcatchment_id

    def _add_subcatchment(self, config: SubcatchmentConfig) -> None:
        """Add a new subcatchment to the model."""
        outlet = self._get_outlet(config.subcatchment_id)
        width = round((config.area * 10_000) / (2 * math.sqrt(config.area * 10_000)), 2)

        subcatchment_data = {
            "Raingage": self._get_raingage(),
            "Outlet": outlet,
            "Area": config.area,
            "PercImperv": round(config.prototype.impervious_result, 2),
            "Width": width,
            "PercSlope": round(config.prototype.slope_result, 2),
            "CurbLength": 0,
        }

        self.model.inp.subcatchments.loc[config.subcatchment_id] = subcatchment_data
        replace_inp_section(self.model.inp.path, "[SUBCATCHMENTS]", self.model.inp.subcatchments)

    def _add_subarea(self, config: SubcatchmentConfig) -> None:
        """Add a new subarea to the model."""
        populate_key = config.prototype.get_linguistic(config.prototype.catchment_result)
        manning_coeffs = self.parameters.manning_coefficients[populate_key]
        depression_params = self.parameters.depression_storage[populate_key]

        subarea_data = {
            "N-Imperv": manning_coeffs[0],
            "N-Perv": manning_coeffs[1],
            "S-Imperv": depression_params[0] * 25.4,
            "S-Perv": depression_params[1] * 25.4,
            "PctZero": depression_params[2],
            "RouteTo": "OUTLET",
        }

        self.model.inp.subareas.loc[config.subcatchment_id] = subarea_data
        replace_inp_section(self.model.inp.path, "[SUBAREAS]", self.model.inp.subareas)

    def _add_coords(self, config: SubcatchmentConfig) -> None:
        """Add coordinates for a square-shaped subcatchment."""
        side_length = math.sqrt(config.area * 10000)
        base_x, base_y = (0, 0) if len(self.model.inp.polygons) == 0 else (self.model.inp.polygons["X"].iloc[-1], self.model.inp.polygons["Y"].iloc[-1])

        coords = pd.DataFrame(
            {
                "X": [base_x, base_x + side_length, base_x + side_length, base_x],
                "Y": [base_y, base_y, base_y - side_length, base_y - side_length],
            },
            index=[config.subcatchment_id] * 4,
        )
        coords.index.names = ["Name"]
        self.model.inp.polygons = pd.concat([self.model.inp.polygons, coords])
        replace_inp_section(self.model.inp.path, "[POLYGONS]", self.model.inp.polygons)

    def _add_infiltration(self, config: SubcatchmentConfig) -> None:
        """Add infiltration parameters for the subcatchment."""
        infiltration_parameters = self.parameters.infiltration_defaults
        self.model.inp.infiltration.loc[config.subcatchment_id] = infiltration_parameters
        self.model.inp.infiltration.index.names = ["Subcatchment"]
        replace_inp_section(self.model.inp.path, "[INFILTRATION]", self.model.inp.infiltration)


    def add_subcatchment(
        self, area: float, land_form: Union[str, LandForm], land_cover: Union[str, LandCover]
    ) -> None:
        """
        Add a new subcatchment to the model (for CLI/GUI use).

        Args:
            area: Subcatchment area in hectares
            land_form: Land form type as string or LandForm enum
            land_cover: Land cover type as string or LandCover enum
        """
        # Convert to Enum for Prototype (already validated in CLI/runner)
        land_form_enum = getattr(LandForm, land_form)
        land_cover_enum = getattr(LandCover, land_cover)

        config = SubcatchmentConfig(
            area=area,
            land_form=land_form_enum,
            land_cover=land_cover_enum
        )
        config.subcatchment_id = self._get_new_subcatchment_id()
        config.prototype = Prototype(land_form=land_form_enum, land_cover=land_cover_enum)

        self._add_subcatchment(config)
        self._add_subarea(config)
        self._add_coords(config)
        self._add_infiltration(config)

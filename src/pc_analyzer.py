"""Analyzer for calculating Personal Conveyance (PC) duration from HOS clocks."""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass


@dataclass
class PCAnalysisResult:
    """Result of PC duration analysis for a driver."""
    driver_id: str
    driver_name: str
    is_currently_in_pc: bool
    consecutive_pc_hours: float
    pc_start_time: Optional[datetime]
    exceeds_threshold: bool
    threshold_hours: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "driver_id": self.driver_id,
            "driver_name": self.driver_name,
            "is_currently_in_pc": self.is_currently_in_pc,
            "consecutive_pc_hours": round(self.consecutive_pc_hours, 2),
            "pc_start_time": self.pc_start_time.isoformat() if self.pc_start_time else None,
            "exceeds_threshold": self.exceeds_threshold,
            "threshold_hours": self.threshold_hours
        }


class PCAnalyzer:
    """Analyzes HOS clocks for Personal Conveyance duration.
    
    Uses the /fleet/hos/clocks endpoint which provides:
    - currentDutyStatus.hosStatusType: Current status
    - currentDutyStatus.hosStatusStartTime: When status started
    
    See: https://developers.samsara.com/reference/gethosclocks
    """
    
    PC_STATUS = "personalConveyance"
    
    def __init__(self, threshold_hours: float = 16.0):
        """Initialize the analyzer.
        
        Args:
            threshold_hours: Alert threshold for consecutive PC hours
        """
        self.threshold_hours = threshold_hours
    
    def analyze_clock(
        self,
        hos_clock: dict,
        current_time: Optional[datetime] = None
    ) -> PCAnalysisResult:
        """Analyze a driver's HOS clock for PC duration.
        
        Args:
            hos_clock: HOS clock entry from /fleet/hos/clocks endpoint
            current_time: Current time for calculating ongoing PC duration
            
        Returns:
            PCAnalysisResult with analysis details
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Extract driver info
        driver = hos_clock.get("driver", {})
        driver_id = driver.get("id", "unknown")
        driver_name = driver.get("name", "Unknown Driver")
        
        # Get current duty status
        current_duty_status = hos_clock.get("currentDutyStatus", {})
        status_type = current_duty_status.get("hosStatusType", "")
        status_start_str = current_duty_status.get("hosStatusStartTime", "")
        
        is_currently_in_pc = status_type == self.PC_STATUS
        
        if not is_currently_in_pc or not status_start_str:
            return PCAnalysisResult(
                driver_id=driver_id,
                driver_name=driver_name,
                is_currently_in_pc=False,
                consecutive_pc_hours=0.0,
                pc_start_time=None,
                exceeds_threshold=False,
                threshold_hours=self.threshold_hours
            )
        
        # Parse the PC start time
        try:
            pc_start_time = datetime.fromisoformat(
                status_start_str.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            return PCAnalysisResult(
                driver_id=driver_id,
                driver_name=driver_name,
                is_currently_in_pc=True,
                consecutive_pc_hours=0.0,
                pc_start_time=None,
                exceeds_threshold=False,
                threshold_hours=self.threshold_hours
            )
        
        # Calculate duration from PC start to now
        duration = current_time - pc_start_time
        consecutive_pc_hours = duration.total_seconds() / 3600
        
        return PCAnalysisResult(
            driver_id=driver_id,
            driver_name=driver_name,
            is_currently_in_pc=True,
            consecutive_pc_hours=consecutive_pc_hours,
            pc_start_time=pc_start_time,
            exceeds_threshold=consecutive_pc_hours >= self.threshold_hours,
            threshold_hours=self.threshold_hours
        )
    
    def analyze_all_clocks(
        self,
        hos_clocks: list[dict],
        current_time: Optional[datetime] = None
    ) -> list[PCAnalysisResult]:
        """Analyze all HOS clocks for PC duration.
        
        Args:
            hos_clocks: List of HOS clock entries
            current_time: Current time for calculations
            
        Returns:
            List of PCAnalysisResult for each driver
        """
        results = []
        for clock in hos_clocks:
            result = self.analyze_clock(clock, current_time)
            results.append(result)
        return results
    
    def get_alerts(self, results: list[PCAnalysisResult]) -> list[PCAnalysisResult]:
        """Filter results to only those exceeding the threshold.
        
        Args:
            results: List of analysis results
            
        Returns:
            List of results that exceed the threshold
        """
        return [r for r in results if r.exceeds_threshold]

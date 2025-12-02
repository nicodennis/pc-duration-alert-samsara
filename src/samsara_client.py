"""Samsara API client for fetching drivers and HOS clocks."""

import requests
from datetime import datetime, timezone
from typing import Optional


class SamsaraClient:
    """Client for interacting with Samsara API."""
    
    BASE_URL = "https://api.samsara.com"
    
    def __init__(self, api_token: str):
        """Initialize the Samsara client.
        
        Args:
            api_token: Samsara API token for authentication
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })
    
    def get_drivers(self, tag_ids: Optional[list[str]] = None) -> list[dict]:
        """Fetch all drivers, optionally filtered by tag IDs.
        
        Args:
            tag_ids: Optional list of tag IDs to filter drivers
            
        Returns:
            List of driver objects
        """
        drivers = []
        params = {}
        
        if tag_ids:
            params["tagIds"] = ",".join(tag_ids)
        
        # Handle pagination
        has_next_page = True
        after_cursor = None
        
        while has_next_page:
            if after_cursor:
                params["after"] = after_cursor
            
            response = self.session.get(
                f"{self.BASE_URL}/fleet/drivers",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            drivers.extend(data.get("data", []))
            
            # Check for pagination
            pagination = data.get("pagination", {})
            after_cursor = pagination.get("endCursor")
            has_next_page = pagination.get("hasNextPage", False)
        
        return drivers
    
    def get_hos_clocks(
        self,
        driver_ids: Optional[list[str]] = None,
        tag_ids: Optional[list[str]] = None
    ) -> list[dict]:
        """Fetch current HOS clocks/status for drivers.
        
        This endpoint returns the current duty status including:
        - hosStatusType: Current status (offDuty, driving, personalConveyance, etc.)
        - hosStatusStartTime: When the driver entered this status
        
        See: https://developers.samsara.com/reference/gethosclocks
        
        Args:
            driver_ids: Optional list of driver IDs to fetch clocks for
            tag_ids: Optional list of tag IDs to filter drivers
            
        Returns:
            List of HOS clock entries with current duty status
        """
        clocks = []
        params = {}
        
        if driver_ids:
            params["driverIds"] = ",".join(driver_ids)
        
        if tag_ids:
            params["tagIds"] = ",".join(tag_ids)
        
        # Handle pagination
        has_next_page = True
        after_cursor = None
        
        while has_next_page:
            if after_cursor:
                params["after"] = after_cursor
            
            response = self.session.get(
                f"{self.BASE_URL}/fleet/hos/clocks",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            clocks.extend(data.get("data", []))
            
            # Check for pagination
            pagination = data.get("pagination", {})
            after_cursor = pagination.get("endCursor")
            has_next_page = pagination.get("hasNextPage", False)
        
        return clocks

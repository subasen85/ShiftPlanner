import datetime
from typing import List, Dict, Tuple, Optional

# Shift Types
SHIFT1 = "Shift1 (07:00 - 15:00)"
SHIFT2 = "Shift2 (12:00 - 20:00)"
WEEKOFF = "Weekoff"

class ShiftSolver:
    def __init__(self, employees: List[str]):
        self.employees = sorted(list(set(employees)))
        self.n = len(self.employees)
        
    def solve_week(self, week_start_date: datetime.date) -> Optional[List[Dict[str, any]]]:
        """
        Solves the shift schedule for a single week (Monday to Sunday).
        Returns a list of daily schedule records, or None if no solution is found.
        """
        # Map employee name to index
        emp_map = {name: idx for idx, name in enumerate(self.employees)}
        
        # Grid to store schedule: grid[emp_idx][day_idx]
        # day_idx: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
        grid = [[None for _ in range(7)] for _ in range(self.n)]
        
        # Weekday bounds for weekoffs
        # Total weekoffs to distribute on Mon-Sat = 2 * N - (N - 2) = N + 2
        total_weekday_offs = self.n + 2
        min_off_per_weekday = total_weekday_offs // 6
        max_off_per_weekday = (total_weekday_offs + 5) // 6
        
        def is_valid(emp_idx: int, day_idx: int, val: str) -> bool:
            # Temporarily set value
            grid[emp_idx][day_idx] = val
            
            # Check Employee Constraints
            # 1. Total weekoffs for this employee in the week must be <= 2
            off_count = sum(1 for d in range(7) if grid[emp_idx][d] == WEEKOFF)
            if off_count > 2:
                grid[emp_idx][day_idx] = None
                return False
                
            # If we are at Sunday, they must have exactly 2 weekoffs
            if day_idx == 6:
                if off_count != 2:
                    grid[emp_idx][day_idx] = None
                    return False
                    
            # 2. Total Shift1 and Shift2 must be <= 3 (enforce balance: either 2 Shift1 & 3 Shift2, or vice versa)
            s1_count = sum(1 for d in range(7) if grid[emp_idx][d] == SHIFT1)
            s2_count = sum(1 for d in range(7) if grid[emp_idx][d] == SHIFT2)
            if s1_count > 3 or s2_count > 3:
                grid[emp_idx][day_idx] = None
                return False
            
            # Check Day Constraints for the current day_idx (checking up to the current emp_idx)
            day_assignments = [grid[e][day_idx] for e in range(self.n) if grid[e][day_idx] is not None]
            assigned_count = len(day_assignments)
            
            day_s1 = sum(1 for a in day_assignments if a == SHIFT1)
            day_s2 = sum(1 for a in day_assignments if a == SHIFT2)
            day_off = sum(1 for a in day_assignments if a == WEEKOFF)
            
            if day_idx == 6:  # Sunday
                # Sunday off days count must be <= N - 2
                if day_off > self.n - 2:
                    grid[emp_idx][day_idx] = None
                    return False
                if day_s1 > 1 or day_s2 > 1:
                    grid[emp_idx][day_idx] = None
                    return False
                # If all employees assigned for Sunday
                if assigned_count == self.n:
                    if day_s1 != 1 or day_s2 != 1 or day_off != self.n - 2:
                        grid[emp_idx][day_idx] = None
                        return False
            else:  # Weekday
                # Off count on weekday must be <= max_off_per_weekday
                if day_off > max_off_per_weekday:
                    grid[emp_idx][day_idx] = None
                    return False
                
                # If all employees are assigned for this weekday
                if assigned_count == self.n:
                    if not (min_off_per_weekday <= day_off <= max_off_per_weekday):
                        grid[emp_idx][day_idx] = None
                        return False
                    # Balanced coverage: Shift1 and Shift2 should be as equal as possible
                    working_count = self.n - day_off
                    target_s1 = working_count // 2
                    target_s2 = (working_count + 1) // 2
                    # The actual counts should match target_s1 and target_s2 in some order
                    if not (day_s1 == target_s1 and day_s2 == target_s2) and not (day_s1 == target_s2 and day_s2 == target_s1):
                        grid[emp_idx][day_idx] = None
                        return False
                else:
                    # Partial assignments must not violate the max possible counts
                    max_possible_working = self.n - min_off_per_weekday
                    max_possible_s1_or_s2 = (max_possible_working + 1) // 2
                    if day_s1 > max_possible_s1_or_s2 or day_s2 > max_possible_s1_or_s2:
                        grid[emp_idx][day_idx] = None
                        return False
                        
            grid[emp_idx][day_idx] = None
            return True

        def backtrack(emp_idx: int, day_idx: int) -> bool:
            if emp_idx == self.n:
                emp_idx = 0
                day_idx += 1
                
            if day_idx == 7:
                return True
                
            # Try values
            for val in [SHIFT1, SHIFT2, WEEKOFF]:
                if is_valid(emp_idx, day_idx, val):
                    grid[emp_idx][day_idx] = val
                    if backtrack(emp_idx + 1, day_idx):
                        return True
                    grid[emp_idx][day_idx] = None
            return False
            
        if backtrack(0, 0):
            # Construct result
            records = []
            for d in range(7):
                date_val = week_start_date + datetime.timedelta(days=d)
                day_name = date_val.strftime("%A")
                for e in range(self.n):
                    records.append({
                        "Date": date_val.strftime("%Y-%m-%d"),
                        "Day": day_name,
                        "Employee": self.employees[e],
                        "Assignment": grid[e][d]
                    })
            return records
        return None

    def generate_schedule(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, any]]:
        """
        Generates schedule for the entire range.
        Assumes start_date is a Monday.
        """
        current_date = start_date
        full_schedule = []
        
        while current_date <= end_date:
            # Solve for the week starting at current_date
            week_schedule = self.solve_week(current_date)
            if week_schedule is None:
                raise ValueError(f"Could not find a valid shift allocation for the week starting {current_date}")
            full_schedule.extend(week_schedule)
            current_date += datetime.timedelta(days=7)
            
        return full_schedule

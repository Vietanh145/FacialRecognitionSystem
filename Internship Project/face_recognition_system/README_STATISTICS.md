# Detailed Statistics Feature - Admin UI

## Description
The detailed statistics feature allows Admin to view detailed attendance data of employees in the last 30 days, including:
- Number of times on time
- Number of times late
- Number of times absent with leave (with reasons)
- Number of times absent without leave

## How to Use

### 1. Access Admin UI
- Run `test_statistics.py` or `src/admin_interface.py`
- Login with HR role account

### 2. Open Statistics Feature
- In Admin UI, click **"Detailed Statistics"** button on the right toolbar
- Statistics window will open

### 3. View Statistics
- Select employee from dropdown menu
- Click **"View Statistics"** or select employee to automatically load data

## Information Tabs

### "Summary" Tab
Displays summary statistics:
- Total days: 30 days
- Number of times on time
- Number of times late
- Number of times absent with leave
- Number of times absent without leave
- Percentage of each type

### "Daily Details" Tab
Displays detailed table for each day in 30 days:
- Date
- Status (On Time/Late/Leave with Permission/Leave without Permission)
- Time In
- Time Out
- Notes (leave reason if applicable)

### "Leave Requests" Tab
Displays list of leave requests in 30 days:
- Start Date
- End Date
- Reason
- Status

## Data Structure

### logs table
- `user_id`: Employee ID
- `date`: Attendance date
- `time_in`: Time in
- `time_out`: Time out
- `status`: Status (ON_TIME/LATE)

### leave_requests table
- `user_id`: Employee ID
- `start_date`: Leave start date
- `end_date`: Leave end date
- `reason`: Leave reason
- `status`: Request status

## Key Features

1. **Automatic Calculation**: System automatically calculates indicators based on actual data
2. **User-friendly Interface**: Uses tabs to clearly separate information
3. **Real-time Data**: Gets data directly from database
4. **Percentage Display**: Shows percentages for easy performance evaluation
5. **Daily Details**: View specific status of each day

## Technical Notes

- Feature requires PostgreSQL database connection
- Need data in `logs` and `leave_requests` tables
- Calculation period: Last 30 days from current date
- Supports displaying leave reasons from `reason` field in database

## Sample Data

The system includes sample data for testing:
- **Nguyen Van A**: 20 days on time, 5 days late, 5 days absent
- **Tran Thi B**: 15 days on time, 8 days late, 7 days absent  
- **Le Van C**: 25 days on time, 3 days late, 2 days absent
- **Nguyen Viet Anh**: 22 days on time, 6 days late, 2 days absent

Run `sample_data.sql` in PostgreSQL to create test data 
-- Sample data for testing detailed statistics feature
-- Run this file in PostgreSQL to create test data

-- Add sample data for users table (if not exists)
INSERT INTO users (user_name, email, phone_number, role, ip_address) 
VALUES 
('Nguyen Van A', 'nguyenvana@company.com', '0123456789', 'EMPLOYEE', '192.168.1.100'),
('Tran Thi B', 'tranthib@company.com', '0987654321', 'EMPLOYEE', '192.168.1.101'),
('Le Van C', 'levanc@company.com', '0111222333', 'EMPLOYEE', '192.168.1.102'),
('Nguyen Viet Anh', 'nguyenvietanh@company.com', '0999888777', 'EMPLOYEE', '192.168.1.103')
ON CONFLICT (user_name) DO NOTHING;

-- Add sample data for logs table (last 30 days)
-- Assuming today is 2024-01-15, we will create data from 2023-12-16 to 2024-01-15

-- Get user IDs
DO $$
DECLARE
    user_a_id INTEGER;
    user_b_id INTEGER;
    user_c_id INTEGER;
    user_anh_id INTEGER;
    current_date DATE := '2023-12-16';
    end_date DATE := '2024-01-15';
BEGIN
    -- Get employee IDs
    SELECT id INTO user_a_id FROM users WHERE user_name = 'Nguyen Van A';
    SELECT id INTO user_b_id FROM users WHERE user_name = 'Tran Thi B';
    SELECT id INTO user_c_id FROM users WHERE user_name = 'Le Van C';
    SELECT id INTO user_anh_id FROM users WHERE user_name = 'Nguyen Viet Anh';
    
    -- Create attendance data for 30 days
    WHILE current_date <= end_date LOOP
        -- Employee A: On time 20 days, late 5 days, absent 5 days
        IF current_date <= '2024-01-10' THEN
            IF current_date NOT IN ('2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05') THEN
                INSERT INTO logs (user_id, date, time_in, time_out, status) VALUES
                (user_a_id, current_date, 
                 current_date + INTERVAL '8 hours', 
                 current_date + INTERVAL '17 hours',
                 CASE 
                    WHEN current_date IN ('2023-12-18', '2023-12-25', '2024-01-08', '2024-01-09', '2024-01-10') 
                    THEN 'LATE' 
                    ELSE 'ON_TIME' 
                 END);
            END IF;
        END IF;
        
        -- Employee B: On time 15 days, late 8 days, absent 7 days
        IF current_date <= '2024-01-09' THEN
            IF current_date NOT IN ('2023-12-20', '2023-12-21', '2023-12-22', '2023-12-25', '2023-12-26', '2024-01-01', '2024-01-02') THEN
                INSERT INTO logs (user_id, date, time_in, time_out, status) VALUES
                (user_b_id, current_date, 
                 current_date + INTERVAL '8 hours', 
                 current_date + INTERVAL '17 hours',
                 CASE 
                    WHEN current_date IN ('2023-12-16', '2023-12-17', '2023-12-18', '2023-12-19', '2023-12-23', '2023-12-24', '2023-12-27', '2023-12-28') 
                    THEN 'LATE' 
                    ELSE 'ON_TIME' 
                 END);
            END IF;
        END IF;
        
        -- Employee C: On time 25 days, late 3 days, absent 2 days
        IF current_date <= '2024-01-13' THEN
            IF current_date NOT IN ('2023-12-25', '2024-01-01') THEN
                INSERT INTO logs (user_id, date, time_in, time_out, status) VALUES
                (user_c_id, current_date, 
                 current_date + INTERVAL '8 hours', 
                 current_date + INTERVAL '17 hours',
                 CASE 
                    WHEN current_date IN ('2023-12-26', '2024-01-02', '2024-01-03') 
                    THEN 'LATE' 
                    ELSE 'ON_TIME' 
                 END);
            END IF;
        END IF;
        
        -- Employee Anh: On time 22 days, late 6 days, absent 2 days
        IF current_date <= '2024-01-13' THEN
            IF current_date NOT IN ('2023-12-25', '2024-01-01') THEN
                INSERT INTO logs (user_id, date, time_in, time_out, status) VALUES
                (user_anh_id, current_date, 
                 current_date + INTERVAL '8 hours', 
                 current_date + INTERVAL '17 hours',
                 CASE 
                    WHEN current_date IN ('2023-12-16', '2023-12-17', '2023-12-18', '2023-12-19', '2023-12-20', '2023-12-21') 
                    THEN 'LATE' 
                    ELSE 'ON_TIME' 
                 END);
            END IF;
        END IF;
        
        current_date := current_date + INTERVAL '1 day';
    END LOOP;
END $$;

-- Add sample data for leave_requests table
INSERT INTO leave_requests (user_id, start_date, end_date, reason, status, created_at) VALUES
-- Employee A leave 5 days (1-5/1/2024)
((SELECT id FROM users WHERE user_name = 'Nguyen Van A'), '2024-01-01', '2024-01-05', 'New Year Holiday', 'CHECKIN', NOW()),

-- Employee B leave 7 days
((SELECT id FROM users WHERE user_name = 'Tran Thi B'), '2023-12-20', '2023-12-22', 'Sick Leave', 'CHECKIN', NOW()),
((SELECT id FROM users WHERE user_name = 'Tran Thi B'), '2023-12-25', '2023-12-26', 'Christmas Holiday', 'CHECKIN', NOW()),
((SELECT id FROM users WHERE user_name = 'Tran Thi B'), '2024-01-01', '2024-01-02', 'New Year Holiday', 'CHECKIN', NOW()),

-- Employee C leave 2 days
((SELECT id FROM users WHERE user_name = 'Le Van C'), '2023-12-25', '2023-12-25', 'Christmas Holiday', 'CHECKIN', NOW()),
((SELECT id FROM users WHERE user_name = 'Le Van C'), '2024-01-01', '2024-01-01', 'New Year Holiday', 'CHECKIN', NOW()),

-- Employee Anh leave 2 days
((SELECT id FROM users WHERE user_name = 'Nguyen Viet Anh'), '2023-12-25', '2023-12-25', 'Christmas Holiday', 'CHECKIN', NOW()),
((SELECT id FROM users WHERE user_name = 'Nguyen Viet Anh'), '2024-01-01', '2024-01-01', 'New Year Holiday', 'CHECKIN', NOW()));

-- Display results
SELECT 
    u.user_name,
    COUNT(l.id) as total_attendance,
    COUNT(CASE WHEN l.status = 'ON_TIME' THEN 1 END) as on_time,
    COUNT(CASE WHEN l.status = 'LATE' THEN 1 END) as late,
    COUNT(lr.id) as leave_requests
FROM users u
LEFT JOIN logs l ON u.id = l.user_id AND l.date >= '2023-12-16' AND l.date <= '2024-01-15'
LEFT JOIN leave_requests lr ON u.id = lr.user_id AND lr.start_date >= '2023-12-16' AND lr.end_date <= '2024-01-15'
WHERE u.role = 'EMPLOYEE'
GROUP BY u.id, u.user_name
ORDER BY u.user_name; 
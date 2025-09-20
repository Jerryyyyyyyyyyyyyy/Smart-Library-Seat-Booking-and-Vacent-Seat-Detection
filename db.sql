-- Create the library database
CREATE DATABASE IF NOT EXISTS library;
USE library;

-- Drop tables if they exist
DROP TABLE IF EXISTS Bookings;
DROP TABLE IF EXISTS Seats;
DROP TABLE IF EXISTS Students;

-- Students table: for user authentication
CREATE TABLE Students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE
);

-- Seats table: contains seat positions and live status
CREATE TABLE Seats (
    seat_id INT PRIMARY KEY,
    x1 INT NOT NULL,
    y1 INT NOT NULL,
    x2 INT NOT NULL,
    y2 INT NOT NULL,
    status VARCHAR(10) DEFAULT 'Vacant',
    INDEX idx_seat_id (seat_id)
);

-- Bookings table: tracks student reservations
CREATE TABLE Bookings (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    seat_id INT NOT NULL,
    student_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    INDEX idx_end_time (end_time)
);

-- Insert initial seat positions
INSERT INTO Seats (seat_id, x1, y1, x2, y2) VALUES
(1, 50, 50, 150, 150),
(2, 200, 50, 300, 150),
(3, 50, 200, 150, 300),
(4, 200, 200, 300, 300);

-- Insert sample students
INSERT INTO Students (student_id, name, email) VALUES
(1001, 'John Doe', 'john.doe@university.edu'),
(1002, 'Jane Smith', 'jane.smith@university.edu');
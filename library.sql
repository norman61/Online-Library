-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Aug 26, 2024 at 01:17 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `library`
--

-- --------------------------------------------------------

--
-- Table structure for table `books`
--

CREATE TABLE `books` (
  `Title` varchar(255) NOT NULL,
  `Author` varchar(255) NOT NULL,
  `Borrow_Date` varchar(255) NOT NULL,
  `Return_Date` varchar(255) NOT NULL,
  `Id` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `books`
--

INSERT INTO `books` (`Title`, `Author`, `Borrow_Date`, `Return_Date`, `Id`) VALUES
('The Phoenix Project', 'Gene Kiim', '2024-08-25', '2024-08-31', '04-2122-036255'),
('The Pragmatic Programmer', 'Andy Hunt', '2024-08-25', '2024-08-30', '04-2222- 0997'),
('The Mythical Man-Month', 'Frederick ', '2024-08-29', '2024-09-07', '09-2222'),
('Hello', 'norman', '2024-08-26', '2024-08-31', '04-2122-036255'),
('hello', 'norman', '2024-08-26', '2024-08-29', '04-2122-036255');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `Id` varchar(255) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Course` varchar(255) NOT NULL,
  `Year` varchar(255) NOT NULL,
  `Email` varchar(255) NOT NULL,
  `Password` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`Id`, `Name`, `Course`, `Year`, `Email`, `Password`) VALUES
('04-2122-036255', 'norman navarra ', 'BSIT', 'second', 'navarra@gmail.com', '123'),
('04-2222- 0997', 'norman', 'BSIT', 'second', 'norman@gmail.com', '123'),
('09-2222-983', 'Navarra', 'BSIT', 'second', 'norman@gmail.com', '123');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`Id`),
  ADD UNIQUE KEY `Id` (`Id`),
  ADD UNIQUE KEY `Id_2` (`Id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

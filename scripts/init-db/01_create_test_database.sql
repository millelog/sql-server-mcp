-- Create test database for integration testing
-- This script runs when the SQL Server Docker container starts

USE master;
GO

-- Create test database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'TestDB')
BEGIN
    CREATE DATABASE TestDB;
END
GO

USE TestDB;
GO

-- Create sample schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'sample')
BEGIN
    EXEC('CREATE SCHEMA sample');
END
GO

-- Create sample tables
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Users (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(50) NOT NULL UNIQUE,
        Email NVARCHAR(100) NOT NULL,
        FirstName NVARCHAR(50),
        LastName NVARCHAR(50),
        CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
        IsActive BIT DEFAULT 1
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Products' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Products (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Name NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        Price DECIMAL(10,2) NOT NULL,
        Category NVARCHAR(50),
        CreatedAt DATETIME2 DEFAULT GETUTCDATE()
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Orders' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.Orders (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        UserId INT NOT NULL FOREIGN KEY REFERENCES dbo.Users(Id),
        OrderDate DATETIME2 DEFAULT GETUTCDATE(),
        TotalAmount DECIMAL(10,2) NOT NULL,
        Status NVARCHAR(20) DEFAULT 'Pending'
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'OrderItems' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE dbo.OrderItems (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        OrderId INT NOT NULL FOREIGN KEY REFERENCES dbo.Orders(Id),
        ProductId INT NOT NULL FOREIGN KEY REFERENCES dbo.Products(Id),
        Quantity INT NOT NULL,
        UnitPrice DECIMAL(10,2) NOT NULL
    );
END
GO

-- Create sample view
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'UserOrders')
BEGIN
    EXEC('
    CREATE VIEW dbo.UserOrders AS
    SELECT
        u.Id AS UserId,
        u.Username,
        u.Email,
        o.Id AS OrderId,
        o.OrderDate,
        o.TotalAmount,
        o.Status
    FROM dbo.Users u
    INNER JOIN dbo.Orders o ON u.Id = o.UserId
    ');
END
GO

-- Create sample stored procedure
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'GetUserOrders')
BEGIN
    EXEC('
    CREATE PROCEDURE dbo.GetUserOrders
        @UserId INT,
        @Status NVARCHAR(20) = NULL
    AS
    BEGIN
        SET NOCOUNT ON;

        SELECT
            o.Id,
            o.OrderDate,
            o.TotalAmount,
            o.Status
        FROM dbo.Orders o
        WHERE o.UserId = @UserId
        AND (@Status IS NULL OR o.Status = @Status)
        ORDER BY o.OrderDate DESC;
    END
    ');
END
GO

-- Create sample function
IF NOT EXISTS (SELECT * FROM sys.objects WHERE name = 'GetOrderTotal' AND type = 'FN')
BEGIN
    EXEC('
    CREATE FUNCTION dbo.GetOrderTotal(@OrderId INT)
    RETURNS DECIMAL(10,2)
    AS
    BEGIN
        DECLARE @Total DECIMAL(10,2);

        SELECT @Total = SUM(Quantity * UnitPrice)
        FROM dbo.OrderItems
        WHERE OrderId = @OrderId;

        RETURN ISNULL(@Total, 0);
    END
    ');
END
GO

-- Insert sample data
IF NOT EXISTS (SELECT * FROM dbo.Users)
BEGIN
    INSERT INTO dbo.Users (Username, Email, FirstName, LastName)
    VALUES
        ('johndoe', 'john@example.com', 'John', 'Doe'),
        ('janedoe', 'jane@example.com', 'Jane', 'Doe'),
        ('bobsmith', 'bob@example.com', 'Bob', 'Smith');
END
GO

IF NOT EXISTS (SELECT * FROM dbo.Products)
BEGIN
    INSERT INTO dbo.Products (Name, Description, Price, Category)
    VALUES
        ('Widget A', 'A basic widget', 9.99, 'Widgets'),
        ('Widget B', 'An advanced widget', 19.99, 'Widgets'),
        ('Gadget X', 'A fancy gadget', 49.99, 'Gadgets'),
        ('Gadget Y', 'A premium gadget', 99.99, 'Gadgets');
END
GO

IF NOT EXISTS (SELECT * FROM dbo.Orders)
BEGIN
    INSERT INTO dbo.Orders (UserId, TotalAmount, Status)
    VALUES
        (1, 29.98, 'Completed'),
        (1, 49.99, 'Pending'),
        (2, 119.98, 'Completed');

    INSERT INTO dbo.OrderItems (OrderId, ProductId, Quantity, UnitPrice)
    VALUES
        (1, 1, 2, 9.99),
        (1, 2, 1, 9.99),
        (2, 3, 1, 49.99),
        (3, 4, 1, 99.99),
        (3, 2, 1, 19.99);
END
GO

PRINT 'Test database setup complete!';
GO

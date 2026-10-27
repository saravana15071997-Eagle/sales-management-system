-- Sales Management System
-- Database schema setup for MySQL 8.0+
-- Creates database, tables, foreign keys, generated column, and payment triggers.
-- Does not include real customer data or database passwords.

CREATE DATABASE IF NOT EXISTS sales_management_system
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE sales_management_system;

DROP TRIGGER IF EXISTS after_payment_insert;
DROP TRIGGER IF EXISTS after_payment_update;
DROP TRIGGER IF EXISTS after_payment_delete;

-- Tables are created if they do not already exist.
-- To rebuild from scratch, first back up your data and manually drop child tables first.

CREATE TABLE IF NOT EXISTS branches (
    branch_id INT NOT NULL AUTO_INCREMENT,
    branch_name VARCHAR(100) NOT NULL,
    branch_admin_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS users (
    user_id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    branch_id INT DEFAULT NULL,
    role ENUM('Super Admin', 'Admin') NOT NULL,
    email VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email (email),
    KEY idx_users_branch_id (branch_id),
    CONSTRAINT fk_users_branch FOREIGN KEY (branch_id) REFERENCES branches (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS customer_sales (
    sale_id INT NOT NULL AUTO_INCREMENT,
    branch_id INT NOT NULL,
    `date` DATE NOT NULL,
    name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL,
    product_name VARCHAR(30) NOT NULL,
    gross_sales DECIMAL(12,2) NOT NULL,
    received_amount DECIMAL(12,2) DEFAULT 0.00,
    pending_amount DECIMAL(12,2) GENERATED ALWAYS AS (gross_sales - received_amount) STORED,
    status ENUM('Open', 'Close') DEFAULT 'Open',
    PRIMARY KEY (sale_id),
    KEY idx_customer_sales_branch_id (branch_id),
    CONSTRAINT fk_customer_sales_branch FOREIGN KEY (branch_id) REFERENCES branches (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS payment_splits (
    payment_id INT NOT NULL AUTO_INCREMENT,
    sale_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount_paid DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    PRIMARY KEY (payment_id),
    KEY idx_payment_splits_sale_id (sale_id),
    CONSTRAINT fk_payment_splits_sale FOREIGN KEY (sale_id) REFERENCES customer_sales (sale_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DELIMITER $$

CREATE TRIGGER after_payment_insert
AFTER INSERT ON payment_splits
FOR EACH ROW
BEGIN
    UPDATE customer_sales
    SET received_amount = (
            SELECT COALESCE(SUM(ps.amount_paid), 0)
            FROM payment_splits AS ps
            WHERE ps.sale_id = NEW.sale_id
        ),
        status = CASE
            WHEN (SELECT COALESCE(SUM(ps.amount_paid), 0)
                  FROM payment_splits AS ps
                  WHERE ps.sale_id = NEW.sale_id) >= gross_sales THEN 'Close'
            ELSE 'Open'
        END
    WHERE sale_id = NEW.sale_id;
END$$

CREATE TRIGGER after_payment_update
AFTER UPDATE ON payment_splits
FOR EACH ROW
BEGIN
    IF OLD.sale_id <> NEW.sale_id THEN
        UPDATE customer_sales
        SET received_amount = (
                SELECT COALESCE(SUM(ps.amount_paid), 0)
                FROM payment_splits AS ps
                WHERE ps.sale_id = OLD.sale_id
            ),
            status = CASE
                WHEN (SELECT COALESCE(SUM(ps.amount_paid), 0)
                      FROM payment_splits AS ps
                      WHERE ps.sale_id = OLD.sale_id) >= gross_sales THEN 'Close'
                ELSE 'Open'
            END
        WHERE sale_id = OLD.sale_id;
    END IF;

    UPDATE customer_sales
    SET received_amount = (
            SELECT COALESCE(SUM(ps.amount_paid), 0)
            FROM payment_splits AS ps
            WHERE ps.sale_id = NEW.sale_id
        ),
        status = CASE
            WHEN (SELECT COALESCE(SUM(ps.amount_paid), 0)
                  FROM payment_splits AS ps
                  WHERE ps.sale_id = NEW.sale_id) >= gross_sales THEN 'Close'
            ELSE 'Open'
        END
    WHERE sale_id = NEW.sale_id;
END$$

CREATE TRIGGER after_payment_delete
AFTER DELETE ON payment_splits
FOR EACH ROW
BEGIN
    UPDATE customer_sales
    SET received_amount = (
            SELECT COALESCE(SUM(ps.amount_paid), 0)
            FROM payment_splits AS ps
            WHERE ps.sale_id = OLD.sale_id
        ),
        status = CASE
            WHEN (SELECT COALESCE(SUM(ps.amount_paid), 0)
                  FROM payment_splits AS ps
                  WHERE ps.sale_id = OLD.sale_id) >= gross_sales THEN 'Close'
            ELSE 'Open'
        END
    WHERE sale_id = OLD.sale_id;
END$$

DELIMITER ;

-- Optional example branch records. Uncomment if you want sample branches:
-- INSERT INTO branches (branch_name, branch_admin_name)
-- VALUES ('Arni', 'Arni Admin'), ('Chennai', 'Chennai Admin');

-- Add login users separately. Do not publish real passwords or customer data.

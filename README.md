# Warehouse Inventory Management System

A web-based inventory management system built using **Flask** and **MySQL** that allows users to manage products, warehouse locations, stock movements, and generate inventory reports.

## Features

- Add, edit, delete products and locations.
- Track stock movement between locations.
- Real-time stock quantity updates.
- Prevent deletion or modification of used entities.
- Generate detailed inventory reports showing stock at each location.
- User-friendly interface with basic error and validation handling.

## Technologies Used

- Python (Flask Framework)
- MySQL (Relational Database)
- HTML/CSS (Basic Frontend Templates)
- Jinja2 Templating Engine

## Screenshots

### 🏠 Home Page
![Home](images/home.png)

### 📦 Products Page
View, add, edit, and delete products.
![Products](images/product.png)

### ➕ Add Product
![Add Product](images/add.png)

### 🏭 Locations Page
View, add, edit, and delete warehouse locations.
![Locations](images/locations.png)

### ➕ Add Location
![Add Location](images/addL.png)

### 🔁 Product Movements
Track product transfers between warehouse locations.
![Movements](images/addM.png)

### ➕ Add Movement
![Add Movement](images/History.png)

### ✏️ Edit Movement
![Edit Movement](images/editM.png)

### 📊 Inventory Report
View live inventory at each warehouse.
![Report](images/inventoryreport.png)

## Database Schema

```sql
CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    quantity INT DEFAULT 0
);

CREATE TABLE Location (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL
);

CREATE TABLE ProductMovement (
    movement_id INT AUTO_INCREMENT PRIMARY KEY,
    from_location INT,
    to_location INT,
    product_id INT,
    qty INT,
    timestamp DATETIME,
    FOREIGN KEY (from_location) REFERENCES Location(location_id),
    FOREIGN KEY (to_location) REFERENCES Location(location_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);


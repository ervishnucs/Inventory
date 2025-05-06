from flask import Flask, render_template,request,redirect,url_for,flash
import mysql.connector

app = Flask(__name__)


DB = {
    'host': 'Vishnu',
    'user': 'Vishnu',
    'password': 'Vishnu@777',
    'database': 'productdispatch'
}

def get_db():
    return mysql.connector.connect(**DB)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/products')
def view_products():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    db.close()
    return render_template('products.html', products=products)
@app.route('/products/add/',methods=['GET','POST'])
def add_product():
    if request.method=='POST':       
        product_name=request.form['product_name']
        quantity=int(request.form['quantity'])
        db=get_db()
        cursor=db.cursor()
        cursor.execute("Insert Into product (product_name,quantity) values (%s,%s)",(product_name,quantity,))
        db.commit()
        db.close()
        return redirect(url_for('view_products'))
    return render_template('addProduct.html')
@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Prevent editing if the product is used in any movement
    cursor.execute("SELECT COUNT(*) as count FROM ProductMovement WHERE product_id = %s", (product_id,))
    used = cursor.fetchone()['count'] > 0

    if used:
        db.close()
        flash("Cannot edit: Product is used in product movements.", "error")
        return redirect(url_for('view_products'))

    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = int(request.form['quantity'])                       
        cursor.execute("UPDATE Product SET product_name = %s , quantity = %s WHERE product_id = %s", (product_name,quantity,product_id,))
        db.commit()
        db.close()
        return redirect(url_for('view_products'))

    cursor.execute("SELECT * FROM Product WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()
    db.close()
    return render_template('edit_product.html', product=product)

@app.route('/products/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    db = get_db()
    cursor = db.cursor() 

    # Prevent deletion if the product is used in any movement
    cursor.execute("SELECT COUNT(*) FROM ProductMovement WHERE product_id = %s", (product_id,))
    count = cursor.fetchone()[0]

    if count > 0:
        db.close()
        flash("Cannot delete: Product is used in product movements.", "error")
        return redirect(url_for('view_products'))

    cursor.execute("DELETE FROM Product WHERE product_id = %s", (product_id,))
    db.commit()
    db.close()
    return redirect(url_for('view_products'))


@app.route('/locations')
def view_locations():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Location")
    locations = cursor.fetchall()
    db.close()
    return render_template('locations.html', locations=locations)

@app.route('/locations/add/', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        location_name = request.form['location_name']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO Location (location_name) VALUES (%s)", (location_name,))
        db.commit()
        db.close()
        return redirect(url_for('view_locations'))
    return render_template('addLocation.html')

@app.route('/locations/edit/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'POST':
        location_name = request.form['location_name']
        cursor.execute("UPDATE Location SET location_name = %s WHERE location_id = %s", (location_name, location_id))
        db.commit()
        db.close()
        return redirect(url_for('view_locations'))
    cursor.execute("SELECT * FROM Location WHERE location_id = %s", (location_id,))
    location = cursor.fetchone()
    db.close()
    return render_template('edit_location.html', location=location)
@app.route('/locations/delete/<location_id>', methods=['POST'])
def delete_location(location_id):
    db = get_db()
    cursor = db.cursor()

   
    cursor.execute("""
        SELECT COUNT(*) FROM ProductMovement
        WHERE from_location = %s OR to_location = %s
    """, (location_id, location_id))
    count = cursor.fetchone()[0]

    if count > 0:
        db.close()
        return "Cannot delete: Location is used in product movements.", 400

    cursor.execute("DELETE FROM Location WHERE location_id = %s", (location_id,))
    db.commit()
    db.close()
    return redirect(url_for('view_locations'))


@app.route('/movements')
def view_movements():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('''
        SELECT 
            pm.movement_id,
            pm.timestamp,
            pm.qty,  -- Ensure qty is included here
            p.product_name,
            fl.location_name AS from_location_name,
            tl.location_name AS to_location_name
        FROM ProductMovement pm
        JOIN Product p ON pm.product_id = p.product_id
        LEFT JOIN Location fl ON pm.from_location = fl.location_id
        LEFT JOIN Location tl ON pm.to_location = tl.location_id
        ORDER BY pm.timestamp DESC
    ''')

    movements = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('movement.html', movements=movements)


@app.route('/movements/add', methods=['GET', 'POST'])
def add_movement():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Load data for dropdowns
    cursor.execute("SELECT product_id, product_name, quantity FROM Product")
    products = cursor.fetchall()
    cursor.execute("SELECT location_id, location_name FROM Location")
    locations = cursor.fetchall()

    if request.method == 'POST':
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        product_id = request.form['product_id']
        qty = int(request.form['qty'])

        # Validate product exists
        cursor.execute("SELECT quantity FROM Product WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            db.close()
            flash("Product does not exist.", "error")
            return render_template('addMovement.html', products=products, locations=locations)

        current_qty = product['quantity']

        # Validate stock if it's an outbound movement
        if from_location and qty > current_qty:
            flash(f"Not enough stock. Available: {current_qty}", "error")
            db.close()
            return render_template('addMovement.html', products=products, locations=locations)

        # Update product stock
        if from_location:
            cursor.execute("UPDATE Product SET quantity = quantity - %s WHERE product_id = %s", (qty, product_id))
        if to_location:
            cursor.execute("UPDATE Product SET quantity = quantity + %s WHERE product_id = %s", (qty, product_id))

        # Insert into ProductMovement
        cursor.execute("""
            INSERT INTO ProductMovement (from_location, to_location, product_id, qty)
            VALUES (%s, %s, %s, %s)
        """, (from_location, to_location, product_id, qty))

        db.commit()
        db.close()
        return redirect(url_for('view_movements'))

    db.close()
    return render_template('addMovement.html', products=products, locations=locations)


@app.route('/movements/edit/<int:movement_id>', methods=['GET', 'POST'])
def edit_movement(movement_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get all products and locations for the form
    cursor.execute("SELECT product_id, product_name FROM Product")
    products = cursor.fetchall()
    cursor.execute("SELECT location_id, location_name FROM Location")
    locations = cursor.fetchall()

    # Fetch original movement
    cursor.execute("SELECT * FROM ProductMovement WHERE movement_id = %s", (movement_id,))
    old_movement = cursor.fetchone()

    if not old_movement:
        db.close()
        flash("Movement not found.", "error")
        return redirect(url_for('view_movements'))

    if request.method == 'POST':
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        new_product_id = request.form['product_id']
        new_qty = int(request.form['qty'])

        # Validate that product exists
        cursor.execute("SELECT quantity FROM Product WHERE product_id = %s", (new_product_id,))
        product = cursor.fetchone()
        if not product:
            db.close()
            flash("Product does not exist.", "error")
            return render_template('edit_movement.html', movement=old_movement, products=products, locations=locations)

        # Reverse the stock effect of the original movement
        old_product_id = old_movement['product_id']
        old_qty = old_movement['qty']

        if old_movement['from_location']:
            cursor.execute("UPDATE Product SET quantity = quantity + %s WHERE product_id = %s", (old_qty, old_product_id))
        if old_movement['to_location']:
            cursor.execute("UPDATE Product SET quantity = quantity - %s WHERE product_id = %s", (old_qty, old_product_id))

        # Check if there's enough stock for the new movement
        if from_location:
            cursor.execute("SELECT quantity FROM Product WHERE product_id = %s", (new_product_id,))
            current_qty = cursor.fetchone()['quantity']
            if new_qty > current_qty:
                db.rollback()
                flash(f"Not enough stock for this product. Available: {current_qty}", "error")
                return render_template('edit_movement.html', movement=old_movement, products=products, locations=locations)

        # Apply the new stock changes
        if from_location:
            cursor.execute("UPDATE Product SET quantity = quantity - %s WHERE product_id = %s", (new_qty, new_product_id))
        if to_location:
            cursor.execute("UPDATE Product SET quantity = quantity + %s WHERE product_id = %s", (new_qty, new_product_id))

        # Update the movement record
        cursor.execute("""
            UPDATE ProductMovement 
            SET from_location = %s, to_location = %s, product_id = %s, qty = %s
            WHERE movement_id = %s
        """, (from_location, to_location, new_product_id, new_qty, movement_id))

        db.commit()
        db.close()
        return redirect(url_for('view_movements'))

    db.close()
    return render_template('edit_movement.html', movement=old_movement, products=products, locations=locations)


@app.route('/movements/delete/<int:movement_id>')
def delete_movement(movement_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM ProductMovement WHERE movement_id = %s", (movement_id,))
    db.commit()
    db.close()
    return redirect(url_for('view_movements'))


@app.route('/report')
def inventory_report():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute('''
        SELECT 
            p.product_name AS product,
            l.location_name AS warehouse,
            COALESCE(SUM(CASE WHEN pm.to_location = l.location_id THEN pm.qty ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN pm.from_location = l.location_id THEN pm.qty ELSE 0 END), 0) AS qty
        FROM Product p
        CROSS JOIN Location l
        LEFT JOIN ProductMovement pm ON pm.product_id = p.product_id
            AND (pm.to_location = l.location_id OR pm.from_location = l.location_id)
        GROUP BY p.product_name, l.location_name
        ORDER BY p.product_name, l.location_name
    ''')

    report = cursor.fetchall()
    db.close()
    return render_template('report.html', report=report)








if __name__ == '__main__':
    app.run(debug=True)
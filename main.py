from flask import Flask, render_template,request,redirect,url_for
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



@app.route('/products/add/', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['product_name'].strip()
        quantity = int(request.form['quantity'])

        db = get_db()
        cursor = db.cursor(dictionary=True)

        
        cursor.execute("SELECT * FROM Product WHERE LOWER(product_name) = LOWER(%s)", (product_name,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("Update Product Set quantity=quantity+%s where product_name=%s",(quantity,product_name,))
        else:         
          cursor.execute("INSERT INTO Product (product_name, quantity) VALUES (%s, %s)", (product_name, quantity))
        db.commit()
        db.close()
        return redirect(url_for('view_products'))

    return render_template('addProduct.html')

@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM ProductMovement WHERE product_id = %s", (product_id,))
    used = cursor.fetchone()['count'] > 0

    if used:
        db.close()
        return"Cannot edit: Product is used in product movements.", 400
        

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

   
    cursor.execute("SELECT COUNT(*) FROM ProductMovement WHERE product_id = %s", (product_id,))
    count = cursor.fetchone()[0]

    if count > 0:
        db.close()       
        return "Cannot delete: Product is used in product movements.",400

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
        location_name = request.form['location_name'].strip()
        db = get_db()
        cursor = db.cursor(dictionary=True)

        
        cursor.execute("SELECT * FROM Location WHERE LOWER(location_name) = LOWER(%s)", (location_name,))
        existing = cursor.fetchone()

        if existing:
            db.close()
            return "Location Exsist!!!",400

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
            pm.qty,  
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

    cursor.execute("SELECT product_id, product_name FROM Product")
    products = cursor.fetchall()
    cursor.execute("SELECT location_id, location_name FROM Location")
    locations = cursor.fetchall()

    if request.method == 'POST':
        from_location = request.form.get('from_location') or None
        to_location = request.form.get('to_location') or None
        product_id = int(request.form['product_id'])
        qty = int(request.form['qty'])

      
        if from_location:
            cursor.execute("SELECT quantity, product_id FROM Location WHERE location_id = %s", (from_location,))
            source = cursor.fetchone()

            if not source or source['product_id'] != product_id:
                db.close()
                return "Product not found in source location.", 400

            if qty > source['quantity']:
                db.close()
                return f"Not enough stock in source location. Available: {source['quantity']}", 400

            cursor.execute("UPDATE Location SET quantity = quantity - %s WHERE location_id = %s", (qty, from_location))

        if to_location:
           
            cursor.execute("SELECT quantity, product_id FROM Location WHERE location_id = %s", (to_location,))
            dest = cursor.fetchone()

            if dest:
                if dest['product_id'] is None:
                         cursor.execute("""
                        UPDATE Location SET quantity = %s, product_id = %s WHERE location_id = %s
                    """, (qty, product_id, to_location))
                elif dest['product_id'] == product_id:
                    
                    cursor.execute("""
                        UPDATE Location SET quantity = quantity + %s WHERE location_id = %s
                    """, (qty, to_location))
                else:
                    db.close()
                    return "Destination already contains a different product.", 400

    
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

    cursor.execute("SELECT product_id, product_name FROM Product")
    products = cursor.fetchall()
    cursor.execute("SELECT location_id, location_name FROM Location")
    locations = cursor.fetchall()

    cursor.execute("SELECT * FROM ProductMovement WHERE movement_id = %s", (movement_id,))
    old = cursor.fetchone()

    if not old:
        db.close()
        return "Movement not found.", "400"
        

    if request.method == 'POST':
        new_from = request.form.get('from_location') or None
        new_to = request.form.get('to_location') or None
        new_product_id = int(request.form['product_id'])
        new_qty = int(request.form['qty'])

        #  old movement
        if old['from_location']:
            cursor.execute("UPDATE Location SET quantity = quantity + %s WHERE location_id = %s",
                           (old['qty'], old['from_location']))
        if old['to_location']:
            cursor.execute("UPDATE Location SET quantity = quantity - %s WHERE location_id = %s",
                           (old['qty'], old['to_location']))

        #  new movement
        if new_from:
            cursor.execute("SELECT quantity, product_id FROM Location WHERE location_id = %s", (new_from,))
            src = cursor.fetchone()
            if not src or src['product_id'] != new_product_id:
                db.rollback()
                return "Invalid source location or mismatched product.", 400
                

            if new_qty > src['quantity']:
                db.rollback()
                return f"Not enough stock in source. Available: {src['quantity']}", 400
               

            cursor.execute("UPDATE Location SET quantity = quantity - %s WHERE location_id = %s",
                           (new_qty, new_from))

        if new_to:
            cursor.execute("SELECT quantity, product_id FROM Location WHERE location_id = %s", (new_to,))
            dest = cursor.fetchone()
            if dest:
                if dest['product_id'] is None:
                    cursor.execute("UPDATE Location SET quantity = %s, product_id = %s WHERE location_id = %s",
                                   (new_qty, new_product_id, new_to))
                elif dest['product_id'] == new_product_id:
                    cursor.execute("UPDATE Location SET quantity = quantity + %s WHERE location_id = %s",
                                   (new_qty, new_to))
                else:
                    db.rollback()
                    return"Destination has a different product.", 400
                    return render_template('edit_movement.html', movement=old, products=products, locations=locations)

        # movement
        cursor.execute("""
            UPDATE ProductMovement
            SET from_location = %s, to_location = %s, product_id = %s, qty = %s
            WHERE movement_id = %s
        """, (new_from, new_to, new_product_id, new_qty, movement_id))

        db.commit()
        db.close()
        return redirect(url_for('view_movements'))

    db.close()
    return render_template('edit_movement.html', movement=old, products=products, locations=locations)


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
            l.location_name AS warehouse,
            p.product_name AS product,
            l.quantity
        FROM Location l
        JOIN Product p ON l.product_id = p.product_id
        WHERE l.product_id IS NOT NULL
        ORDER BY p.product_name, l.location_name
    ''')

    report = cursor.fetchall()
    db.close()
    return render_template('report.html', report=report)

if __name__ == '__main__':
    app.run(debug=True)
  
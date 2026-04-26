from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from database import init_db, get_db
from datetime import datetime, date
from bson import ObjectId
from notifier import send_alert_email, get_alerts
from scheduler import start_scheduler
import functools
import os

app = Flask(__name__)
app.secret_key = 'medshop_secret_2024'
LOW_STOCK_THRESHOLD = 10


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Try admin / admin123', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    db        = get_db()
    col       = db.medicines
    today     = date.today().isoformat()
    total     = col.count_documents({})
    low_stock = col.count_documents({'quantity': {'$lte': LOW_STOCK_THRESHOLD}})
    expired   = col.count_documents({'expiry_date': {'$lt': today}})
    in_stock  = col.count_documents({'quantity': {'$gt': LOW_STOCK_THRESHOLD}})
    recent    = list(col.find().sort('created_at', -1).limit(5))
    low_items = list(col.find({'quantity': {'$lte': LOW_STOCK_THRESHOLD}}).sort('quantity', 1).limit(5))
    alerts    = get_alerts(db)
    return render_template('dashboard.html',
        total=total, low_stock=low_stock, expired=expired, in_stock=in_stock,
        recent=recent, low_items=low_items, today=today, alerts=alerts)


@app.route('/send-alert', methods=['POST'])
@login_required
def send_alert():
    db     = get_db()
    result = send_alert_email(db)
    flash(result['message'], 'success' if result['sent'] else 'error')
    return redirect(url_for('dashboard'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    import notifier
    import scheduler as sched
    if request.method == 'POST':
        gmail        = request.form.get('gmail', '').strip()
        password     = request.form.get('password', '').strip()
        notify       = request.form.get('notify_email', '').strip()
        alert_hour   = request.form.get('alert_hour', '9').strip()
        alert_minute = request.form.get('alert_minute', '0').strip()
        if gmail and password and notify:
            os.environ['GMAIL_ADDRESS']  = gmail
            os.environ['GMAIL_PASSWORD'] = password
            os.environ['NOTIFY_EMAIL']   = notify
            notifier.GMAIL_ADDRESS  = gmail
            notifier.GMAIL_PASSWORD = password
            notifier.NOTIFY_EMAIL   = notify
            try:
                sched.ALERT_HOUR   = int(alert_hour)
                sched.ALERT_MINUTE = int(alert_minute)
                os.environ['ALERT_HOUR']   = alert_hour
                os.environ['ALERT_MINUTE'] = alert_minute
            except ValueError:
                pass
            flash(f'Settings saved! Daily alerts at {alert_hour}:{alert_minute.zfill(2)} ✅', 'success')
        else:
            flash('Please fill in all three fields.', 'error')
        return redirect(url_for('settings'))
    return render_template('settings.html',
        gmail=notifier.GMAIL_ADDRESS,
        notify=notifier.NOTIFY_EMAIL,
        alert_hour=sched.ALERT_HOUR,
        alert_minute=sched.ALERT_MINUTE)


@app.route('/medicines')
@login_required
def medicines():
    db          = get_db()
    col         = db.medicines
    today       = date.today().isoformat()
    search      = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', 'all')
    query       = {}
    if search:
        query['$or'] = [
            {'name':         {'$regex': search, '$options': 'i'}},
            {'manufacturer': {'$regex': search, '$options': 'i'}}
        ]
    if filter_type == 'low':
        query['quantity'] = {'$lte': LOW_STOCK_THRESHOLD}
    elif filter_type == 'expired':
        query['expiry_date'] = {'$lt': today}
    elif filter_type == 'expiring':
        from datetime import timedelta
        soon = (date.today() + timedelta(days=30)).isoformat()
        query['expiry_date'] = {'$gte': today, '$lte': soon}
    meds = list(col.find(query).sort('name', 1))
    return render_template('medicines.html', medicines=meds, today=today,
                           search=search, filter=filter_type, threshold=LOW_STOCK_THRESHOLD)


@app.route('/medicines/add', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        category     = request.form.get('category', '').strip()
        price        = request.form.get('price', 0)
        quantity     = request.form.get('quantity', 0)
        expiry_date  = request.form.get('expiry_date', '')
        description  = request.form.get('description', '').strip()
        errors = []
        if not name:        errors.append('Medicine name is required.')
        if not expiry_date: errors.append('Expiry date is required.')
        try:    price    = float(price)
        except: errors.append('Invalid price.')
        try:    quantity = int(quantity)
        except: errors.append('Invalid quantity.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('add_medicine.html', form=request.form)
        get_db().medicines.insert_one({
            'name': name, 'manufacturer': manufacturer, 'category': category,
            'price': price, 'quantity': quantity, 'expiry_date': expiry_date,
            'description': description, 'created_at': datetime.now().isoformat()
        })
        flash(f'Medicine "{name}" added successfully!', 'success')
        return redirect(url_for('medicines'))
    return render_template('add_medicine.html', form={})


@app.route('/medicines/edit/<med_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(med_id):
    db  = get_db()
    col = db.medicines
    med = col.find_one({'_id': ObjectId(med_id)})
    if not med:
        flash('Medicine not found.', 'error')
        return redirect(url_for('medicines'))
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        category     = request.form.get('category', '').strip()
        price        = request.form.get('price', 0)
        quantity     = request.form.get('quantity', 0)
        expiry_date  = request.form.get('expiry_date', '')
        description  = request.form.get('description', '').strip()
        errors = []
        if not name:        errors.append('Name is required.')
        if not expiry_date: errors.append('Expiry date is required.')
        try:    price    = float(price)
        except: errors.append('Invalid price.')
        try:    quantity = int(quantity)
        except: errors.append('Invalid quantity.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('add_medicine.html', form=request.form,
                                   edit=True, med_id=med_id)
        col.update_one({'_id': ObjectId(med_id)}, {'$set': {
            'name': name, 'manufacturer': manufacturer, 'category': category,
            'price': price, 'quantity': quantity, 'expiry_date': expiry_date,
            'description': description, 'updated_at': datetime.now().isoformat()
        }})
        flash(f'Medicine "{name}" updated!', 'success')
        return redirect(url_for('medicines'))
    return render_template('add_medicine.html', form=med, edit=True, med_id=med_id)


@app.route('/medicines/delete/<med_id>', methods=['POST'])
@login_required
def delete_medicine(med_id):
    db  = get_db()
    med = db.medicines.find_one({'_id': ObjectId(med_id)})
    if med:
        db.medicines.delete_one({'_id': ObjectId(med_id)})
        flash(f'Medicine "{med["name"]}" deleted.', 'success')
    return redirect(url_for('medicines'))


@app.route('/api/search')
@login_required
def api_search():
    q     = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    db    = get_db()
    today = date.today().isoformat()
    meds  = list(db.medicines.find(
        {'name': {'$regex': q, '$options': 'i'}}
    ).limit(10))
    return jsonify([{
        'id':           str(m['_id']),
        'name':         m['name'],
        'price':        m['price'],
        'quantity':     m['quantity'],
        'expiry_date':  m['expiry_date'],
        'manufacturer': m.get('manufacturer', ''),
        'category':     m.get('category', ''),
        'is_expired':   m['expiry_date'] < today,
        'is_low':       m['quantity'] <= LOW_STOCK_THRESHOLD
    } for m in meds])


if __name__ == '__main__':
    init_db()
    start_scheduler(app)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
